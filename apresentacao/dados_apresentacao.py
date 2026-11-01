#!/usr/bin/env python3
"""Monta dados_apresentacao.json (numeros + textos) a partir dos resultados consolidados."""
import json
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
import os
RES = Path(os.environ.get("RES_DIR", RAIZ / "resultados"))
df = pd.read_csv(RES / "resultados_consolidados.csv")
esp = json.loads((RAIZ / "site-teste/esperado.json").read_text())
metas = [json.loads(p.read_text()) for p in sorted(RES.glob("*/meta.json"))]
USU = sorted(df.usuarios.unique().tolist())
UMAX = max(USU)


def g(v, c, u, col):
    return float(df[(df.versao == v) & (df.cache == c) & (df.usuarios == u)][col].iloc[0])


def ms(v):
    return f"{v/1000:.1f} s".replace(".", ",") if v >= 1000 else f"{v:.0f} ms" if v >= 10 else f"{v:.1f} ms".replace(".", ",")


def br(v, d=0):
    return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


equipe_arq = RAIZ / "apresentacao/equipe.json"
if equipe_arq.exists():
    equipe = json.loads(equipe_arq.read_text())
else:
    equipe = [{"nome": f"Nome do integrante {i}", "matricula": "matrícula", "placeholder": True} for i in range(1, 5)]

# ---- numeros-chave
sp = {v: g(v, "Sem cache", UMAX, "media_ms") / g(v, "Com cache", UMAX, "media_ms") for v in ("Python", "Ruby")}
vaz_sem = {v: df[(df.versao == v) & (df.cache == "Sem cache")]["req_por_s"].max() for v in ("Python", "Ruby")}
vaz_com = {v: g(v, "Com cache", UMAX, "req_por_s") for v in ("Python", "Ruby")}
total_req = int(df.requisicoes.sum())
total_falhas = int(df.falhas.sum())

dados = {
    "pasta_graficos": str(RES / "graficos" / "slides"),
    "data_execucao": pd.Timestamp(metas[0]["inicio"]).strftime("%d/%m/%Y"),
    "n_cenarios": int(len(df)), "n_urls": len(esp), "usuarios": USU,
    "total_req": total_req, "total_falhas": total_falhas,
    "equipe": equipe,
    "linhas": df.to_dict(orient="records"),
    "paginas": [{"nome": k, "links": v["links"], "kb": v["bytes"] / 1024, "latencia_ms": v["latencia_ms"]} for k, v in esp.items()],
    "numeros": {"speedup": sp, "vazao_max_sem_cache": vaz_sem, "vazao_com_cache_umax": vaz_com},
}
AP = RAIZ / "apresentacao"
dados["textos"] = json.loads((AP / "textos_fixos.json").read_text())
tr = json.loads((AP / os.environ.get("TEXTOS_RESULTADOS", "textos_resultados.json")).read_text())
dados["textos"].update(tr["textos"])
dados["cards"] = tr["cards"]
dados["graficos"] = tr["graficos"]
dados["webrick"] = tr.get("webrick")
json.dump(dados, sys.stdout, indent=2, ensure_ascii=False, default=float)
