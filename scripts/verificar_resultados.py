#!/usr/bin/env python3
"""
Confere a consistencia dos resultados de cada cenario usando fontes independentes:
  - Locust (resumo.json) x tempos brutos registrados pelo script (tempos_brutos.csv):
      quantidade de requisicoes e tempo medio devem bater;
  - com cache: todas as requisicoes devem ter acertado o Redis e nenhuma ido a origem;
  - sem cache: o Redis nao deve ter sido consultado e cada requisicao deve ter
      buscado a pagina na origem;
  - nenhuma falha (HTTP != 200 ou quantidade de links diferente da esperada).
"""
import json
import sys
from pathlib import Path

import pandas as pd

RES = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "resultados"
problemas = 0
print(f"{'cenario':24s} {'req':>6s} {'brutos':>6s} {'media':>8s} {'media_b':>8s} {'falhas':>6s} "
      f"{'hits':>6s} {'miss':>5s} {'origem':>6s}  ok?")
for pasta in sorted(p for p in RES.iterdir() if (p / "meta.json").exists()):
    meta = json.loads((pasta / "meta.json").read_text())
    a = json.loads((pasta / "resumo.json").read_text())["agregado"]
    bruto = pd.read_csv(pasta / "tempos_brutos.csv")
    n, nb = a["requisicoes"], len(bruto)
    media_b = bruto["tempo_ms"].mean()
    erros = []
    if abs(n - nb) > max(3, 0.01 * n):
        erros.append("contagem Locust x brutos")
    if abs(a["media_ms"] - media_b) > max(0.5, 0.03 * a["media_ms"]):
        erros.append("media Locust x brutos")
    if a["falhas"] or bruto["falha"].notna().sum():
        erros.append("falhas")
    if meta["cache"] == "com":
        if meta["redis_faltas"] != 0 or meta["buscas_na_origem"] != 0 or meta["redis_acertos"] < n:
            erros.append("cache nao atendeu tudo")
    else:
        if meta["redis_acertos"] or meta["redis_faltas"]:
            erros.append("redis usado sem cache")
        if meta["buscas_na_origem"] < n:
            erros.append("menos buscas na origem que requisicoes")
    problemas += bool(erros)
    print(f"{meta['cenario']:24s} {n:6d} {nb:6d} {a['media_ms']:8.1f} {media_b:8.1f} {a['falhas']:6d} "
          f"{meta['redis_acertos']:6d} {meta['redis_faltas']:5d} {meta['buscas_na_origem']:6d}  "
          f"{'OK' if not erros else 'ATENCAO: ' + ', '.join(erros)}")
print("\nRESULTADO:", "todos os cenarios consistentes" if not problemas else f"{problemas} cenario(s) com alerta")
