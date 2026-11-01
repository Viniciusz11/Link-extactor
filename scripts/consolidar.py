#!/usr/bin/env python3
"""
Junta as metricas de todos os cenarios (resultados/<cenario>/resumo.json e
meta.json) em:
  resultados/resultados_consolidados.csv   - uma linha por cenario
  resultados/resultados_por_url.csv        - uma linha por cenario x URL
  resultados/planilha_resultados.xlsx      - planilha formatada (Resumo,
                                             Ganho do cache, Por URL, Paginas)
"""
import json
import sys
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

RAIZ = Path(__file__).resolve().parent.parent
RES = Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / "resultados"

COLS = [  # (chave, cabecalho)
    ("cenario", "Cenário"), ("versao", "Versão"), ("cache", "Cache"), ("usuarios", "Usuários virtuais"),
    ("requisicoes", "Requisições"), ("falhas", "Falhas"), ("media_ms", "Média (ms)"),
    ("mediana_ms", "Mediana (ms)"), ("min_ms", "Mín (ms)"), ("p75_ms", "p75 (ms)"), ("p90_ms", "p90 (ms)"),
    ("p95_ms", "p95 (ms)"), ("p99_ms", "p99 (ms)"), ("max_ms", "Máx (ms)"), ("req_por_s", "Vazão (req/s)"),
    ("cpu_servico_pct", "CPU do serviço (% de 1 núcleo)"), ("memoria_max_servico_mb", "Memória máx. (MB)"),
    ("redis_acertos", "Acertos no Redis"), ("redis_faltas", "Faltas no Redis"),
    ("buscas_na_origem", "Buscas na página de origem"),
]


def carregar():
    linhas, por_url = [], []
    for pasta in sorted(RES.iterdir()):
        if not (pasta / "meta.json").exists():
            continue
        meta = json.loads((pasta / "meta.json").read_text())
        resumo = json.loads((pasta / "resumo.json").read_text())
        linhas.append({**meta, **resumo["agregado"]})
        for nome, m in resumo["por_url"].items():
            por_url.append({"cenario": meta["cenario"], "versao": meta["versao"], "cache": meta["cache"],
                            "usuarios": meta["usuarios"], "url": nome, **m})
    df = pd.DataFrame(linhas)
    df["versao"] = df["versao"].map({"python": "Python", "ruby": "Ruby"})
    df["cache"] = df["cache"].map({"com": "Com cache", "sem": "Sem cache"})
    df = df.sort_values(["versao", "cache", "usuarios"], ascending=[True, False, True]).reset_index(drop=True)
    pu = pd.DataFrame(por_url)
    pu["versao"] = pu["versao"].map({"python": "Python", "ruby": "Ruby"})
    pu["cache"] = pu["cache"].map({"com": "Com cache", "sem": "Sem cache"})
    return df, pu


# ----------------------------------------------------------------------------- planilha
AZUL = PatternFill("solid", fgColor="1F3A5F")
CINZA = PatternFill("solid", fgColor="F2F2F2")
BORDA = Border(bottom=Side(style="thin", color="BFBFBF"))
F = "Arial"


def cabecalho(ws, linha, titulos, larguras):
    for j, (t, w) in enumerate(zip(titulos, larguras), 1):
        c = ws.cell(row=linha, column=j, value=t)
        c.font = Font(name=F, bold=True, color="FFFFFF", size=10)
        c.fill = AZUL
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(j)].width = w
    ws.row_dimensions[linha].height = 42


def titulo(ws, texto, sub):
    ws["A1"] = texto
    ws["A1"].font = Font(name=F, bold=True, size=14, color="1F3A5F")
    ws["A2"] = sub
    ws["A2"].font = Font(name=F, italic=True, size=9, color="595959")


def planilha(df, pu):
    wb = Workbook()

    # --- Resumo -------------------------------------------------------------
    ws = wb.active
    ws.title = "Resumo"
    titulo(ws, "Teste de desempenho – Link Extractor: métricas por cenário",
           "Fonte: Locust 2.47 (estatísticas finais de cada execução, 90 s de medição após rampa de 5 s). "
           "CPU/memória medidas no processo do serviço; acertos/faltas via INFO do Redis; "
           "buscas na origem contadas pelo site de teste.")
    cabecalho(ws, 4, [h for _, h in COLS], [24, 9, 12, 10, 11, 8, 10, 10, 9, 9, 9, 9, 9, 10, 10, 13, 11, 10, 10, 12])
    for i, row in df.iterrows():
        r = 5 + i
        for j, (k, _) in enumerate(COLS, 1):
            c = ws.cell(row=r, column=j, value=row[k])
            c.font = Font(name=F, size=10, color="0000FF" if j > 4 else "000000")
            c.border = BORDA
            if isinstance(row[k], float):
                c.number_format = "#,##0.0"
            elif j > 4:
                c.number_format = "#,##0"
        if (row["cache"] == "Sem cache"):
            for j in range(1, len(COLS) + 1):
                ws.cell(row=r, column=j).fill = CINZA
    ultima = 4 + len(df)
    nota = ultima + 2
    ws.cell(row=nota, column=1, value="Valores em azul = medições (dados de entrada). "
            "Percentis do Locust são aproximados (agrupamento em faixas de 10 ms acima de 100 ms e de 100 ms acima de 1 s).").font = Font(name=F, size=9, italic=True)
    ws.freeze_panes = "E5"
    ws.auto_filter.ref = f"A4:{get_column_letter(len(COLS))}{ultima}"

    # --- Ganho do cache (formulas) -------------------------------------------
    g = wb.create_sheet("Ganho do cache")
    titulo(g, "Ganho do cache Redis (calculado por fórmulas a partir da aba Resumo)",
           "Speedup = métrica sem cache ÷ métrica com cache, para a mesma versão e o mesmo nº de usuários.")
    cab = ["Versão", "Usuários", "Média sem cache (ms)", "Média com cache (ms)", "Speedup da média (×)",
           "p95 sem cache (ms)", "p95 com cache (ms)", "Speedup do p95 (×)",
           "Vazão sem cache (req/s)", "Vazão com cache (req/s)", "Redução do tempo médio",
           "Mediana sem cache (ms)", "Mediana com cache (ms)", "Speedup da mediana (×)"]
    cabecalho(g, 4, cab, [10, 10, 14, 14, 13, 13, 13, 13, 14, 14, 14, 14, 14, 13])
    # chave auxiliar: Versao|Cache|Usuarios na coluna V da aba Resumo
    for i in range(len(df)):
        r = 5 + i
        ws.cell(row=r, column=22, value=f'=B{r}&"|"&C{r}&"|"&D{r}').font = Font(name=F, size=8, color="808080")
    ws.cell(row=4, column=22, value="chave (auxiliar)").font = Font(name=F, size=8, color="808080")
    rng = f"Resumo!$V$5:$V${ultima}"

    def busca(col_letra, versao_cell, cache_txt, usu_cell):
        return (f'INDEX(Resumo!${col_letra}$5:${col_letra}${ultima},'
                f'MATCH({versao_cell}&"|{cache_txt}|"&{usu_cell},{rng},0))')

    combos = df[["versao", "usuarios"]].drop_duplicates().values.tolist()
    for i, (v, u) in enumerate(combos):
        r = 5 + i
        g.cell(row=r, column=1, value=v)
        g.cell(row=r, column=2, value=int(u))
        g.cell(row=r, column=3, value="=" + busca("G", f"A{r}", "Sem cache", f"B{r}"))
        g.cell(row=r, column=4, value="=" + busca("G", f"A{r}", "Com cache", f"B{r}"))
        g.cell(row=r, column=5, value=f"=IFERROR(C{r}/D{r},0)")
        g.cell(row=r, column=6, value="=" + busca("L", f"A{r}", "Sem cache", f"B{r}"))
        g.cell(row=r, column=7, value="=" + busca("L", f"A{r}", "Com cache", f"B{r}"))
        g.cell(row=r, column=8, value=f"=IFERROR(F{r}/G{r},0)")
        g.cell(row=r, column=9, value="=" + busca("O", f"A{r}", "Sem cache", f"B{r}"))
        g.cell(row=r, column=10, value="=" + busca("O", f"A{r}", "Com cache", f"B{r}"))
        g.cell(row=r, column=11, value=f"=IFERROR(1-D{r}/C{r},0)")
        g.cell(row=r, column=12, value="=" + busca("H", f"A{r}", "Sem cache", f"B{r}"))
        g.cell(row=r, column=13, value="=" + busca("H", f"A{r}", "Com cache", f"B{r}"))
        g.cell(row=r, column=14, value=f"=IFERROR(L{r}/M{r},0)")
        for j in range(1, 15):
            c = g.cell(row=r, column=j)
            c.font = Font(name=F, size=10)
            c.border = BORDA
            c.number_format = {5: '0.0"×"', 8: '0.0"×"', 14: '0.0"×"', 11: "0.0%", 2: "0"}.get(j, "#,##0.0")
    nota_g = 6 + len(combos)
    g.cell(row=nota_g, column=1, value="Ruby com 200 usuários: média e p99 distorcidos por 100 requisições que esperaram o timeout de 60 s "
           "(limite de 100 conexões do WEBrick) – ver aba Diagnóstico WEBrick. Os gráficos de ganho usam a mediana.").font = Font(name=F, size=9, italic=True)

    # --- Por URL ------------------------------------------------------------
    p = wb.create_sheet("Por URL")
    titulo(p, "Métricas por URL (página) em cada cenário", "Mesma fonte da aba Resumo, separada por página consultada.")
    cp = [("cenario", "Cenário"), ("versao", "Versão"), ("cache", "Cache"), ("usuarios", "Usuários"),
          ("url", "URL (rótulo)"), ("requisicoes", "Requisições"), ("falhas", "Falhas"), ("media_ms", "Média (ms)"),
          ("mediana_ms", "Mediana (ms)"), ("p95_ms", "p95 (ms)"), ("p99_ms", "p99 (ms)"), ("max_ms", "Máx (ms)"),
          ("req_por_s", "Vazão (req/s)"), ("tamanho_medio_bytes", "Tamanho médio da resposta (bytes)")]
    cabecalho(p, 4, [h for _, h in cp], [24, 9, 12, 9, 20, 11, 8, 10, 10, 9, 9, 10, 10, 14])
    for i, row in pu.reset_index(drop=True).iterrows():
        for j, (k, _) in enumerate(cp, 1):
            c = p.cell(row=5 + i, column=j, value=row[k])
            c.font = Font(name=F, size=10)
            if isinstance(row[k], float):
                c.number_format = "#,##0.0"
    p.freeze_panes = "F5"
    p.auto_filter.ref = f"A4:{get_column_letter(len(cp))}{4 + len(pu)}"

    # --- Paginas ------------------------------------------------------------
    esp = json.loads((RAIZ / "site-teste/esperado.json").read_text())
    q = wb.create_sheet("Páginas de teste")
    titulo(q, "As 10 URLs usadas pelo usuário virtual", "Páginas geradas por site-teste/gerar_paginas.py e servidas por site-teste/servidor.py.")
    cabecalho(q, 4, ["Página", "URL", "Links esperados", "Tamanho (KB)", "Latência simulada (ms)"], [16, 42, 12, 12, 14])
    for i, (nome, v) in enumerate(esp.items()):
        r = 5 + i
        for j, val in enumerate([nome, f"http://127.0.0.1:8080/{nome}.html", v["links"], round(v["bytes"] / 1024, 1), v["latencia_ms"]], 1):
            c = q.cell(row=r, column=j, value=val)
            c.font = Font(name=F, size=10)
    r = 5 + len(esp)
    q.cell(row=r, column=1, value="Total / média").font = Font(name=F, bold=True, size=10)
    q.cell(row=r, column=3, value=f"=SUM(C5:C{r-1})").font = Font(name=F, bold=True, size=10)
    q.cell(row=r, column=4, value=f"=AVERAGE(D5:D{r-1})").font = Font(name=F, bold=True, size=10)
    q.cell(row=r, column=4).number_format = "0.0"
    q.cell(row=r, column=5, value=f"=AVERAGE(E5:E{r-1})").font = Font(name=F, bold=True, size=10)
    q.cell(row=r, column=5).number_format = "0"

    diag = RAIZ / "resultados_diagnostico" / "webrick-maxclients-300"
    if diag.exists():
        dg = wb.create_sheet("Diagnóstico WEBrick")
        titulo(dg, "Diagnóstico: limite de conexões do WEBrick (servidor do Ruby)",
               "Mesmo cenário Ruby com 200 usuários, com o limite padrão (MaxClients = 100) e com MaxClients = 300. "
               "Teste extra, fora da matriz dos 24 cenários.")
        cd = [("cache", "Cache"), ("limite", "Limite de conexões (MaxClients)"), ("usuarios", "Usuários"),
              ("requisicoes", "Requisições"), ("falhas", "Falhas"), ("media_ms", "Média (ms)"), ("mediana_ms", "Mediana (ms)"),
              ("p95_ms", "p95 (ms)"), ("p99_ms", "p99 (ms)"), ("req_por_s", "Vazão (req/s)"), ("cpu_servico_pct", "CPU do serviço (%)")]
        cabecalho(dg, 4, [h for _, h in cd], [12, 16, 10, 12, 9, 11, 11, 10, 10, 11, 12])
        linhas = []
        for cache in ("Com cache", "Sem cache"):
            base = df[(df.versao == "Ruby") & (df.cache == cache) & (df.usuarios == 200)].iloc[0].to_dict()
            linhas.append({**base, "limite": "100 (padrão)"})
            pasta = diag / f"ruby-{'com' if cache == 'Com cache' else 'sem'}-cache-200u"
            m = json.loads((pasta / "meta.json").read_text())
            a = json.loads((pasta / "resumo.json").read_text())["agregado"]
            linhas.append({**m, **a, "cache": cache, "limite": "300"})
        for i, row in enumerate(linhas):
            for j, (k, _) in enumerate(cd, 1):
                c = dg.cell(row=5 + i, column=j, value=row[k])
                c.font = Font(name=F, size=10, bold=(row["limite"] == "300"))
                c.border = BORDA
                if isinstance(row[k], float):
                    c.number_format = "#,##0.0"

    destino = RES / "planilha_resultados.xlsx"
    wb.save(destino)
    return destino


def main():
    df, pu = carregar()
    df[[k for k, _ in COLS]].to_csv(RES / "resultados_consolidados.csv", index=False)
    pu.to_csv(RES / "resultados_por_url.csv", index=False)
    print(df[["cenario", "requisicoes", "falhas", "media_ms", "mediana_ms", "p95_ms", "p99_ms", "req_por_s",
              "cpu_servico_pct", "redis_acertos", "redis_faltas", "buscas_na_origem"]].to_string(index=False))
    print("planilha:", planilha(df, pu))


if __name__ == "__main__":
    main()
