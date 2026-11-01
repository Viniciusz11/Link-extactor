"""
Trabalho 4 - Teste de desempenho do servico de extracao de links (Link Extractor)

Comportamento de cada usuario virtual:
  - executa uma SEQUENCIA DE 10 INVOCACOES ao servico de extracao de links
    (GET /api/<url>), passando uma URL DIFERENTE em cada invocacao;
  - a ordem das 10 URLs e sorteada a cada sequencia (evita que todos os
    usuarios peçam a mesma pagina ao mesmo tempo);
  - entre uma invocacao e outra o usuario "pensa" de 0,5 a 1,5 s;
  - cada resposta e validada: HTTP 200, JSON valido e quantidade de links
    igual a esperada para aquela pagina (senao conta como falha).

Exemplo de execucao (servico Python na porta 5000):
  locust -f locustfile.py --host http://127.0.0.1:5000 --headless -u 50 -r 10 -t 95s \
         --reset-stats --csv resultados/python-cache-50u/locust

Variaveis de ambiente opcionais:
  SITE_URL   - endereco do site de teste (padrao http://127.0.0.1:8080)
  URLS_FILE  - arquivo com uma URL por linha (para testar com sites reais)
  RAW_CSV    - se definido, grava o tempo de CADA requisicao neste CSV
"""
import csv
import json
import os
import random
import time
from pathlib import Path

from locust import FastHttpUser, between, events, task

AQUI = Path(__file__).resolve().parent
SITE = os.getenv("SITE_URL", "http://127.0.0.1:8080")
ESPERADO_ARQ = AQUI.parent / "site-teste" / "esperado.json"

if os.getenv("URLS_FILE"):
    URLS = [l.strip() for l in open(os.environ["URLS_FILE"]) if l.strip()]
    ESPERADO = {}
else:
    esperado = json.loads(ESPERADO_ARQ.read_text())
    URLS = [f"{SITE}/{nome}.html" for nome in esperado]
    ESPERADO = {f"{SITE}/{nome}.html": v["links"] for nome, v in esperado.items()}

assert len(URLS) == 10, "o usuario virtual deve invocar o servico com 10 URLs diferentes"


def rotulo(url):
    """Nome curto usado nas estatisticas do Locust, ex.: /api/[wiki]"""
    return "/api/[" + url.rstrip("/").rsplit("/", 1)[-1].replace(".html", "") + "]"


class UsuarioLinkExtractor(FastHttpUser):
    wait_time = between(0.5, 1.5)  # tempo de "reflexao" entre invocacoes

    @task
    def sequencia_de_10_invocacoes(self):
        urls = random.sample(URLS, k=len(URLS))  # 10 URLs diferentes, ordem aleatoria
        for i, url in enumerate(urls):
            with self.client.get(f"/api/{url}", name=rotulo(url), catch_response=True) as resp:
                if resp.status_code != 200:
                    resp.failure(f"HTTP {resp.status_code}")
                else:
                    try:
                        links = resp.json()
                    except Exception:
                        resp.failure("resposta nao e JSON valido")
                    else:
                        esperado = ESPERADO.get(url)
                        if esperado is not None and len(links) != esperado:
                            resp.failure(f"{len(links)} links (esperado {esperado})")
                        else:
                            resp.success()
            if i < len(urls) - 1:
                self.wait()  # pausa entre uma invocacao e a proxima


# ---------------------------------------------------------------------------
# Registro bruto de cada requisicao (opcional), so durante o regime
# estacionario (depois que todos os usuarios foram criados).
# ---------------------------------------------------------------------------
_raw = {"f": None, "w": None}


@events.test_start.add_listener
def _abrir(environment, **kw):
    if os.getenv("RAW_CSV"):
        _raw["f"] = open(os.environ["RAW_CSV"], "w", newline="")
        _raw["w"] = csv.writer(_raw["f"])
        _raw["w"].writerow(["timestamp", "nome", "tempo_ms", "bytes", "usuarios", "falha"])


@events.request.add_listener
def _registrar(request_type, name, response_time, response_length, exception, context, **kw):
    w = _raw["w"]
    runner = getattr(_registrar, "runner", None)
    if w is None or runner is None or runner.state in ("ready", "spawning"):
        return
    w.writerow([f"{time.time():.3f}", name, f"{response_time:.2f}", response_length,
                runner.user_count, "" if exception is None else str(exception)[:80]])


@events.init.add_listener
def _guardar_runner(environment, **kw):
    _registrar.runner = environment.runner


@events.test_stop.add_listener
def _fechar(environment, **kw):
    if _raw["f"]:
        _raw["f"].close()
        _raw["f"] = _raw["w"] = None


# ---------------------------------------------------------------------------
# Resumo final (opcional): grava as metricas FINAIS do Locust em JSON.
# (O CSV periodico do Locust pode ficar ate 1 s defasado no encerramento.)
# ---------------------------------------------------------------------------
PERCENTIS = [0.50, 0.66, 0.75, 0.80, 0.90, 0.95, 0.98, 0.99, 0.999, 1.0]


def _metricas(e):
    return {
        "requisicoes": e.num_requests,
        "falhas": e.num_failures,
        "media_ms": round(e.avg_response_time, 2),
        "mediana_ms": e.median_response_time,
        "min_ms": round(e.min_response_time or 0, 2),
        "max_ms": round(e.max_response_time, 2),
        "req_por_s": round(e.total_rps, 3),
        "falhas_por_s": round(e.total_fail_per_sec, 3),
        "tamanho_medio_bytes": round(e.avg_content_length, 1),
        **{f"p{str(round(p * 100, 1)).replace('.0', '')}_ms": e.get_response_time_percentile(p) for p in PERCENTIS},
    }


@events.quit.add_listener
def _resumo(exit_code, **kw):
    destino = os.getenv("SUMMARY_JSON")
    runner = getattr(_registrar, "runner", None)
    if not destino or runner is None:
        return
    st = runner.stats
    dados = {"agregado": _metricas(st.total),
             "por_url": {nome: _metricas(e) for (nome, _m), e in sorted(st.entries.items())},
             "erros": [{"nome": e.name, "erro": str(e.error), "ocorrencias": e.occurrences}
                       for e in st.errors.values()]}
    Path(destino).write_text(json.dumps(dados, indent=2, ensure_ascii=False))
