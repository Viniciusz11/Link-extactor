#!/usr/bin/env python3
"""
Teste funcional (antes do teste de carga): pede ao servico Python e ao Ruby
os links de cada uma das 10 paginas e confere que
  1) a quantidade de links e exatamente a esperada;
  2) as duas versoes devolvem exatamente a mesma lista (texto e href);
  3) os links "[IMG]" e os hrefs relativos foram resolvidos corretamente.
Uso: validar_servicos.py <arquivo_python.json> <arquivo_ruby.json>
     (arquivos gerados por coletar_respostas)
"""
import json
import sys
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

RAIZ = Path(__file__).resolve().parent.parent
ESPERADO = json.loads((RAIZ / "site-teste" / "esperado.json").read_text())
SITE = "http://127.0.0.1:8080"
SESS = requests.Session()
SESS.trust_env = False


def coletar(porta):
    out = {}
    for nome in ESPERADO:
        r = SESS.get(f"http://127.0.0.1:{porta}/api/{SITE}/{nome}.html", timeout=30)
        r.raise_for_status()
        out[nome] = r.json()
    return out


def referencia(nome):
    """Extracao independente, feita direto do arquivo HTML, para comparar."""
    html = (RAIZ / "site-teste" / "paginas" / f"{nome}.html").read_text(encoding="utf-8")
    base = f"{SITE}/{nome}.html"
    return [{"text": " ".join(a.text.split()) or "[IMG]", "href": urljoin(base, a.get("href"))}
            for a in BeautifulSoup(html, "html.parser").find_all("a")]


def main():
    py, rb = coletar(5000), coletar(4567)
    ok = True
    for nome, esp in ESPERADO.items():
        ref = referencia(nome)
        c_ok = len(py[nome]) == len(rb[nome]) == esp["links"] == len(ref)
        igual = py[nome] == rb[nome] == ref
        img = sum(1 for x in py[nome] if x["text"] == "[IMG]")
        print(f"{nome:13s} esperado={esp['links']:5d} python={len(py[nome]):5d} ruby={len(rb[nome]):5d} "
              f"[IMG]={img:3d}  contagem={'OK' if c_ok else 'FALHA'}  conteudo_identico={'OK' if igual else 'FALHA'}")
        ok &= c_ok and igual
    print("\nRESULTADO:", "TODAS AS VERIFICACOES PASSARAM" if ok else "HA DIVERGENCIAS")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
