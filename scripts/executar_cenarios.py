#!/usr/bin/env python3
"""
Executa todos os cenarios do teste de desempenho, um apos o outro:

  versao do servico : python (Flask, porta 5000) | ruby (Sinatra, porta 4567)
  modo de cache     : com | sem
  usuarios virtuais : 1, 10, 25, 50, 100

Para cada cenario:
  1. sobe o servico (preso ao nucleo 1 da CPU) com CACHE_ENABLED=true/false;
  2. limpa o Redis e zera os contadores do Redis e do site de teste;
  3. com cache: aquece o cache pedindo as 10 URLs uma vez (regime permanente);
  4. roda o Locust (nucleo 0): rampa de 5 s + 90 s de medicao (--reset-stats);
  5. guarda CSVs/HTML do Locust, resumo JSON, tempos brutos, uso de CPU e
     memoria do servico, acertos/faltas no Redis e buscas feitas na origem.

Uso: executar_cenarios.py [--duracao 90] [--usuarios 1,10,25,50,100]
                          [--versoes python,ruby] [--caches com,sem] [--saida resultados]
"""
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import psutil
import redis
import requests

RAIZ = Path(__file__).resolve().parent.parent
VENV = Path(os.environ.get("VENV_BIN", Path(sys.executable).parent))  # pasta com o executavel locust
PORTAS = {"python": 5000, "ruby": 4567}
SITE = "http://127.0.0.1:8080"
RAMPA_S = 5

sess = requests.Session()
sess.trust_env = False  # tudo e local; nao usar proxy
r = redis.Redis(host="127.0.0.1", port=6379)


def log(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def infra():
    """Sobe Redis e o site de teste se ainda nao estiverem no ar."""
    procs = []
    try:
        r.ping()
    except Exception:
        procs.append(subprocess.Popen(["taskset", "-c", "0", "redis-server", "--port", "6379", "--save", "",
                                       "--appendonly", "no"], stdout=open(RAIZ / "logs/redis.log", "w"),
                                      stderr=subprocess.STDOUT))
    try:
        sess.get(f"{SITE}/__stats", timeout=2)
    except Exception:
        procs.append(subprocess.Popen(["taskset", "-c", "0", sys.executable, str(RAIZ / "site-teste/servidor.py"),
                                       "8080"], stdout=open(RAIZ / "logs/site.log", "w"), stderr=subprocess.STDOUT))
    for _ in range(40):
        try:
            r.ping(); sess.get(f"{SITE}/__stats", timeout=2); break
        except Exception:
            time.sleep(0.25)
    return procs


def servico(acao, versao=None, cache=None):
    args = ["bash", str(RAIZ / "scripts/servico.sh"), acao]
    if acao == "start":
        args += [versao, "cache" if cache == "com" else "nocache"]
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL)


def pid_servico(versao):
    alvo = "python-api/main.py" if versao == "python" else "linkextractor.rb"
    for p in psutil.process_iter(["cmdline"]):
        cmd = " ".join(p.info["cmdline"] or [])
        if alvo in cmd and "taskset" not in cmd and "bash" not in cmd:
            return p
    raise RuntimeError("processo do servico nao encontrado")


def rodar(versao, cache, usuarios, duracao, saida):
    nome = f"{versao}-{cache}-cache-{usuarios:03d}u"
    pasta = saida / nome
    pasta.mkdir(parents=True, exist_ok=True)
    porta = PORTAS[versao]
    servico("start", versao, cache)
    r.flushall()
    if cache == "com":  # aquece o cache: as 10 URLs ficam no Redis antes da medicao
        esperado = json.loads((RAIZ / "site-teste/esperado.json").read_text())
        for pag in esperado:
            sess.get(f"http://127.0.0.1:{porta}/api/{SITE}/{pag}.html", timeout=30).raise_for_status()
        assert r.dbsize() == 10, "cache nao foi aquecido"
    r.config_resetstat()
    sess.get(f"{SITE}/__reset", timeout=5)

    proc = pid_servico(versao)
    cpu0, t0 = proc.cpu_times(), time.time()
    rss_max = 0
    # rampa de 5 s, mas nunca mais de 100 usuarios criados por segundo (com 1000 usuarios: 10 s)
    rampa = max(RAMPA_S, -(-usuarios // 100))
    taxa = max(1, -(-usuarios // rampa))
    cmd = ["taskset", "-c", "0", str(VENV / "locust"), "-f", str(RAIZ / "locust/locustfile.py"),
           "--host", f"http://127.0.0.1:{porta}", "--headless", "-u", str(usuarios), "-r", str(taxa),
           "-t", f"{rampa + duracao}s", "--reset-stats", "--only-summary", "--loglevel", "WARNING",
           "--csv", str(pasta / "locust"), "--html", str(pasta / "relatorio_locust.html")]
    env = dict(os.environ, SUMMARY_JSON=str(pasta / "resumo.json"), RAW_CSV=str(pasta / "tempos_brutos.csv"))
    log(f"{nome}: {usuarios} usuarios, rampa {rampa}s, medicao {duracao}s")
    with open(pasta / "locust_saida.txt", "w") as out:
        lp = subprocess.Popen(cmd, stdout=out, stderr=subprocess.STDOUT, env=env)
        while lp.poll() is None:
            rss_max = max(rss_max, proc.memory_info().rss)
            time.sleep(1)
    cpu1, t1 = proc.cpu_times(), time.time()

    info = r.info("stats")
    origem = sess.get(f"{SITE}/__stats", timeout=5).json()
    resumo = json.loads((pasta / "resumo.json").read_text())
    meta = {
        "cenario": nome, "versao": versao, "cache": cache, "usuarios": usuarios,
        "duracao_medicao_s": duracao, "rampa_s": rampa, "taxa_spawn": taxa,
        "inicio": datetime.fromtimestamp(t0).isoformat(timespec="seconds"),
        "cpu_servico_pct": round(100 * ((cpu1.user + cpu1.system) - (cpu0.user + cpu0.system)) / (t1 - t0), 1),
        "memoria_max_servico_mb": round(rss_max / 2**20, 1),
        "redis_acertos": info["keyspace_hits"], "redis_faltas": info["keyspace_misses"],
        "buscas_na_origem": origem["total"],
        "locust_cpu_alerta": "CPU usage above" in (pasta / "locust_saida.txt").read_text(),
    }
    (pasta / "meta.json").write_text(json.dumps(meta, indent=2))
    a = resumo["agregado"]
    log(f"   -> {a['requisicoes']} req, {a['falhas']} falhas, media {a['media_ms']} ms, "
        f"mediana {a['mediana_ms']} ms, p95 {a['p95_ms']} ms, {a['req_por_s']} req/s, "
        f"CPU servico {meta['cpu_servico_pct']}%, redis hit/miss {meta['redis_acertos']}/{meta['redis_faltas']}, "
        f"origem {meta['buscas_na_origem']}")
    servico("stop")
    time.sleep(3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--duracao", type=int, default=90)
    ap.add_argument("--usuarios", default="50,200,400,1000")
    ap.add_argument("--versoes", default="python,ruby")
    ap.add_argument("--caches", default="com,sem")
    ap.add_argument("--saida", default=str(RAIZ / "resultados"))
    a = ap.parse_args()
    (RAIZ / "logs").mkdir(exist_ok=True)
    procs = infra()
    try:
        for versao in a.versoes.split(","):
            for cache in a.caches.split(","):
                for u in map(int, a.usuarios.split(",")):
                    rodar(versao, cache, u, a.duracao, Path(a.saida))
    finally:
        servico("stop")
        for p in procs:
            p.terminate()
    log("FIM")


if __name__ == "__main__":
    main()
