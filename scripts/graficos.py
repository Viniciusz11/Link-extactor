#!/usr/bin/env python3
"""
Gera os graficos (PNG) a partir de resultados/resultados_consolidados.csv,
resultados/resultados_por_url.csv e dos tempos brutos de cada cenario.

  graficos.py [pasta_resultados]            -> resultados/graficos/*.png (com titulo)
  graficos.py [pasta_resultados] --slides   -> resultados/graficos/slides/*.png
                                               (sem titulo interno; o titulo fica no slide)
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter

RAIZ = Path(__file__).resolve().parent.parent
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
SLIDES = "--slides" in sys.argv
RES = Path(ARGS[0]) if ARGS else RAIZ / "resultados"
OUT = RES / "graficos" / ("slides" if SLIDES else "")
OUT.mkdir(parents=True, exist_ok=True)
H1, H2, H3 = (5.6, 6.2, 6.0) if SLIDES else (6.8, 7.4, 7.0)
TOP1, TOP2 = (0.90, 0.90) if SLIDES else (0.77, 0.80)

# ---------------------------------------------------------------- estilo
TINTA, TINTA2, MUDO = "#0b0b0b", "#52514e", "#898781"
GRADE, EIXO, FUNDO = "#e1e0d9", "#c3c2b7", "#ffffff"
COR = {"Python": "#2a78d6", "Ruby": "#eb6834"}          # identidade da versao (slots 1 e 2 da paleta)
ESTILO = {"Sem cache": dict(ls="-", marker="o", mfc=None),
          "Com cache": dict(ls="--", marker="s", mfc=FUNDO)}

plt.rcParams.update({
    "font.family": "Inter", "font.size": 13, "axes.labelsize": 13, "axes.labelcolor": TINTA2,
    "xtick.color": TINTA2, "ytick.color": TINTA2, "xtick.labelsize": 12.5, "ytick.labelsize": 12.5,
    "axes.edgecolor": EIXO, "axes.linewidth": 1, "axes.grid": True, "grid.color": GRADE,
    "grid.linewidth": 0.8, "axes.axisbelow": True, "axes.spines.top": False, "axes.spines.right": False,
    "figure.facecolor": FUNDO, "axes.facecolor": FUNDO, "savefig.facecolor": FUNDO,
    "legend.frameon": False, "legend.fontsize": 12.5, "lines.linewidth": 2, "lines.markersize": 7,
})


def br(v, casas=None):
    """numero no formato brasileiro (virgula decimal, ponto de milhar)."""
    s = f"{v:,.{casas}f}" if casas is not None else f"{v:,g}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def ms_fmt(v, _=None):
    if v >= 1000:
        return f"{br(v / 1000, 2 if v < 10000 else 1).rstrip('0').rstrip(',')} s"
    if v >= 10:
        return f"{br(v, 0)} ms"
    return f"{br(v, 1)} ms"


def tick_ms(v, _=None):
    return f"{br(v / 1000)} s" if v >= 1000 else f"{br(v)} ms"


def log_y(ax, fmt=tick_ms):
    ax.set_yscale("log")
    ax.yaxis.set_major_locator(LogLocator(base=10, subs=(1.0, 3.0)))
    ax.yaxis.set_major_formatter(FuncFormatter(fmt))
    ax.yaxis.set_minor_formatter(NullFormatter())


def eixo_usuarios(ax, usuarios, rotulo="Usuários virtuais simultâneos (escala log)"):
    ax.set_xscale("log")
    ax.set_xticks(usuarios)
    ax.set_xticklabels([str(u) for u in usuarios])
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xlabel(rotulo)


def titulo(fig, t, sub=None):
    if SLIDES:
        return
    fig.text(0.012, 0.975, t, ha="left", va="top", fontsize=19, fontweight="semibold", color=TINTA)
    if sub:
        fig.text(0.012, 0.912, sub, ha="left", va="top", fontsize=12.5, color=TINTA2)


def legenda_series(ax):
    h = [Line2D([], [], color=COR["Python"], lw=2.5, label="Python (Flask + BeautifulSoup)"),
         Line2D([], [], color=COR["Ruby"], lw=2.5, label="Ruby (Sinatra + Nokogiri)"),
         Line2D([], [], color=TINTA2, ls="-", marker="o", label="Sem cache"),
         Line2D([], [], color=TINTA2, ls="--", marker="s", mfc=FUNDO, label="Com cache (Redis)")]
    ax.legend(handles=h, loc="lower left", bbox_to_anchor=(0, 1.02), ncol=4, borderaxespad=0,
              handlelength=2.6, columnspacing=1.6)


def linha(ax, x, y, versao, cache):
    e = ESTILO[cache]
    ax.plot(x, y, color=COR[versao], ls=e["ls"], marker=e["marker"],
            mfc=e["mfc"] or COR[versao], mec=COR[versao], mew=2, zorder=3)


def rotulos_finais(ax, itens, gap_px=34):
    """Rotulos no fim de cada linha, afastados verticalmente para nao se sobreporem.
    itens = [(x, y, texto)]; gap em pixels da figura (dpi de saida 150)."""
    fig = ax.figure
    fig.set_dpi(150)
    fig.canvas.draw()
    pts = sorted((ax.transData.transform((x, y))[1], x, y, t) for x, y, t in itens)
    pos = []
    for py, *_ in pts:
        pos.append(max(py, pos[-1] + gap_px) if pos else py)
    for i, (py, x, y, t) in enumerate(pts):
        ax.annotate(t, (x, y), xytext=(10, (pos[i] - py) * 72 / fig.dpi), textcoords="offset points",
                    va="center", fontsize=12, color=TINTA, annotation_clip=False)


def salvar(fig, nome):
    fig.savefig(OUT / nome, dpi=150)
    plt.close(fig)
    print("ok", OUT / nome)


# ---------------------------------------------------------------- dados
df = pd.read_csv(RES / "resultados_consolidados.csv")
pu = pd.read_csv(RES / "resultados_por_url.csv")
USU = sorted(df["usuarios"].unique())
SERIES = [(v, c) for v in ("Python", "Ruby") for c in ("Sem cache", "Com cache")]


def serie(v, c, col):
    d = df[(df.versao == v) & (df.cache == c)].sort_values("usuarios")
    return d["usuarios"], d[col]


def fig_padrao():
    fig, ax = plt.subplots(figsize=(13.33, H1))
    fig.subplots_adjust(left=0.08, right=0.84, top=TOP1, bottom=0.12)
    return fig, ax


# ---------------------------------------------------------------- 1. tempo medio
fig, ax = fig_padrao()
fins = []
for v, c in SERIES:
    x, y = serie(v, c, "media_ms")
    linha(ax, x, y, v, c)
    _, f = serie(v, c, "falhas")
    extra = f" ({int(f.iloc[-1])} timeouts)" if f.iloc[-1] > 0 else ""
    fins.append((x.iloc[-1], y.iloc[-1], f"{v} {ms_fmt(y.iloc[-1])}{extra}"))
log_y(ax)
eixo_usuarios(ax, USU)
ax.set_ylabel("Tempo médio de resposta (escala log)")
legenda_series(ax)
rotulos_finais(ax, fins)
titulo(fig, "Tempo médio de resposta × número de usuários",
       "Sem cache, cada requisição baixa e analisa a página; com cache, a resposta vem pronta do Redis.")
salvar(fig, "01_tempo_medio.png")


# ---------------------------------------------------------------- 2. percentis por cenario
def oklch_rampa(hex_cor, Ls):
    """Rampa de um so matiz: mesmo matiz/croma em OKLCH, luminosidade variavel."""
    def s2l(c):
        return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)

    def l2s(c):
        c = np.clip(c, 0, 1)
        return np.where(c <= 0.0031308, 12.92 * c, 1.055 * c ** (1 / 2.4) - 0.055)

    rgb = s2l(np.array([int(hex_cor[i:i + 2], 16) / 255 for i in (1, 3, 5)]))
    M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929], [0.2119034982, 0.6806995451, 0.1073969566],
                   [0.0883024619, 0.2817188376, 0.6299787005]])
    M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468], [1.9779984951, -2.4285922050, 0.4505937099],
                   [0.0259040371, 0.7827717662, -0.8086757660]])
    lab = M2 @ np.cbrt(M1 @ rgb)
    C, h = np.hypot(lab[1], lab[2]), np.arctan2(lab[2], lab[1])
    out = []
    for L in Ls:
        lms = (np.linalg.inv(M2) @ np.array([L, C * np.cos(h), C * np.sin(h)])) ** 3
        r = l2s(np.linalg.inv(M1) @ lms)
        out.append("#" + "".join(f"{int(round(v * 255)):02x}" for v in r))
    return out


RAMPA = {"Python": ["#86b6ef", "#3987e5", "#1c5cab", "#0d366b"],
         "Ruby": oklch_rampa("#eb6834", [0.80, 0.68, 0.55, 0.42])}
PCTS = [("mediana_ms", "Mediana (p50)"), ("p90_ms", "p90"), ("p95_ms", "p95"), ("p99_ms", "p99")]

fig, axs = plt.subplots(2, 2, figsize=(13.33, H2), sharex=True, sharey=True)
fig.subplots_adjust(left=0.08, right=0.98, top=TOP2 - 0.035, bottom=0.10, hspace=0.32, wspace=0.08)
for i, v in enumerate(("Python", "Ruby")):
    for j, c in enumerate(("Sem cache", "Com cache")):
        ax = axs[i, j]
        for k, (col, nome) in enumerate(PCTS):
            x, y = serie(v, c, col)
            ax.plot(x, y, color=RAMPA[v][k], marker="o", ms=5, lw=2, ls=ESTILO[c]["ls"])
        ax.set_title(f"{v} · {c.lower()}", loc="left", fontsize=14, fontweight="semibold", color=TINTA)
        log_y(ax)
        ax.yaxis.set_major_locator(LogLocator(base=10, subs=(1.0,)))
        eixo_usuarios(ax, USU, "Usuários virtuais (escala log)" if i == 1 else "")
CINZAS = ["#c3c2b7", "#898781", "#52514e", "#0b0b0b"]
fig.legend(handles=[Line2D([], [], color=g, marker="o", ms=5, lw=2, label=n) for g, (_, n) in zip(CINZAS, PCTS)],
           loc="upper right", bbox_to_anchor=(0.985, 0.995 if SLIDES else 0.985), ncol=4, fontsize=12,
           handlelength=1.6)
titulo(fig, "Percentis do tempo de resposta em cada cenário",
       "Mesma escala nos quatro painéis; cor = versão (azul Python, laranja Ruby), mais escuro = percentil mais alto.")
salvar(fig, "02_percentis_por_cenario.png")

# ---------------------------------------------------------------- 3. vazao
fig, ax = fig_padrao()
xs = np.array(USU, dtype=float)
ax.plot(xs, xs, color=MUDO, lw=1.5, ls=":", zorder=2)
ax.annotate("demanda gerada (≈ 1 req/s por usuário)", (xs[-2], xs[-2]), xytext=(-12, 10),
            textcoords="offset points", ha="right", fontsize=11.5, color=TINTA2)
fins = []
for v, c in SERIES:
    x, y = serie(v, c, "req_por_s")
    linha(ax, x, y, v, c)
    fins.append((x.iloc[-1], y.iloc[-1], f"{v} {br(y.iloc[-1], 0)} req/s"))
ax.set_xscale("log")
ax.set_yscale("log")
eixo_usuarios(ax, USU)
ax.set_yticks([1, 3, 10, 30, 100, 300])
ax.yaxis.set_major_formatter(FuncFormatter(lambda val, _: br(val)))
ax.yaxis.set_minor_formatter(NullFormatter())
ax.set_ylabel("Vazão atendida (req/s, escala log)")
legenda_series(ax)
rotulos_finais(ax, fins)
titulo(fig, "Vazão (requisições atendidas por segundo)",
       "Quando a linha se afasta da demanda, o serviço saturou e as requisições passam a esperar em fila.")
salvar(fig, "03_vazao.png")

# ---------------------------------------------------------------- 4. CPU
fig, ax = fig_padrao()
ax.axhline(100, color=MUDO, lw=1.5, ls=":")
ax.annotate("100% = um núcleo inteiro (o serviço roda preso a 1 núcleo)", (USU[0], 100), xytext=(0, -16),
            textcoords="offset points", fontsize=11.5, color=TINTA2)
fins = []
for v, c in SERIES:
    x, y = serie(v, c, "cpu_servico_pct")
    linha(ax, x, y, v, c)
    fins.append((x.iloc[-1], y.iloc[-1], f"{v} {br(y.iloc[-1], 0)}%"))
eixo_usuarios(ax, USU)
ax.set_ylim(0, 110)
ax.set_yticks([0, 20, 40, 60, 80, 100])
ax.yaxis.set_major_formatter(FuncFormatter(lambda val, _: f"{val:.0f}%"))
ax.set_ylabel("CPU do processo do serviço")
legenda_series(ax)
rotulos_finais(ax, fins)
titulo(fig, "Uso de CPU do serviço de extração",
       "Python e Ruby executam um thread por vez por processo (GIL/GVL): o teto prático é ~100% de um núcleo.")
salvar(fig, "04_cpu_servico.png")

# ---------------------------------------------------------------- 5. ganho do cache
fig, ax = fig_padrao()
for v, off in (("Python", 12), ("Ruby", -20)):
    _, sem = serie(v, "Sem cache", "mediana_ms")  # mediana: a media do Ruby/200 usuarios e distorcida por timeouts
    x, com = serie(v, "Com cache", "mediana_ms")
    ganho = sem.values / com.values
    ax.plot(x, ganho, color=COR[v], marker="o", mfc=COR[v], mec=COR[v], mew=2, lw=2.5)
    for xi, gi in zip(x, ganho):
        ax.annotate(f"{br(gi, 0)}×", (xi, gi), xytext=(0, off), textcoords="offset points",
                    ha="center", fontsize=11.5, color=TINTA)
log_y(ax, fmt=lambda val, _=None: f"{br(val)}×")
eixo_usuarios(ax, USU)
ax.set_ylabel("Mediana sem cache ÷ mediana com cache")
ax.set_ylim(bottom=40)
ax.legend(handles=[Line2D([], [], color=COR["Python"], lw=2.5, marker="o", label="Python"),
                   Line2D([], [], color=COR["Ruby"], lw=2.5, marker="o", label="Ruby")],
          loc="lower left", bbox_to_anchor=(0, 1.02), ncol=2, borderaxespad=0)
titulo(fig, "Quantas vezes o cache acelera o tempo de resposta (mediana)",
       "Razão entre a mediana sem cache e com cache, para a mesma versão e a mesma carga.")
salvar(fig, "05_ganho_do_cache.png")


# ---------------------------------------------------------------- 6. distribuicao (CDF)
def cdf(nome_cen):
    t = np.sort(pd.read_csv(RES / nome_cen / "tempos_brutos.csv")["tempo_ms"].values)
    return t, np.arange(1, len(t) + 1) / len(t)


CARGA_CDF = 50 if 50 in USU else USU[len(USU) // 2]
fig, ax = plt.subplots(figsize=(13.33, H1))
fig.subplots_adjust(left=0.08, right=0.97, top=TOP1, bottom=0.12)
for v, c in SERIES:
    nome = f"{v.lower()}-{'com' if c == 'Com cache' else 'sem'}-cache-{CARGA_CDF:03d}u"
    t, p = cdf(nome)
    ax.plot(t, p * 100, color=COR[v], ls=ESTILO[c]["ls"], lw=2.2)
ax.set_xscale("log")
ax.xaxis.set_major_locator(LogLocator(base=10, subs=(1.0, 3.0)))
ax.xaxis.set_major_formatter(FuncFormatter(tick_ms))
ax.xaxis.set_minor_formatter(NullFormatter())
ax.set_yticks([0, 25, 50, 75, 90, 100])
ax.yaxis.set_major_formatter(FuncFormatter(lambda val, _: f"{val:.0f}%"))
ax.set_xlabel("Tempo de resposta (escala log)")
ax.set_ylabel("% das requisições respondidas em até X")
h = [Line2D([], [], color=COR["Python"], lw=2.5, label="Python"),
     Line2D([], [], color=COR["Ruby"], lw=2.5, label="Ruby"),
     Line2D([], [], color=TINTA2, ls="-", label="Sem cache"),
     Line2D([], [], color=TINTA2, ls="--", label="Com cache (Redis)")]
ax.legend(handles=h, loc="lower left", bbox_to_anchor=(0, 1.02), ncol=4, borderaxespad=0, handlelength=2.6)
titulo(fig, f"Distribuição dos tempos de resposta com {CARGA_CDF} usuários (todas as requisições)",
       "Curva acumulada: quanto mais à esquerda, mais rápido. Dados brutos registrados pelo script do Locust.")
salvar(fig, f"06_distribuicao_{CARGA_CDF}u.png")

# ---------------------------------------------------------------- 7. por URL
esp = json.loads((RAIZ / "site-teste/esperado.json").read_text())
CARGA_URL = 10 if 10 in USU else USU[0]
d = pu[(pu.cache == "Sem cache") & (pu.usuarios == CARGA_URL)].copy()
d["pagina"] = d["url"].str.extract(r"\[(.*)\]", expand=False)
ordem = sorted(esp, key=lambda k: esp[k]["bytes"])
fig, ax = plt.subplots(figsize=(13.33, H3))
fig.subplots_adjust(left=0.25, right=0.95, top=TOP2, bottom=0.11)
y = np.arange(len(ordem))
h = 0.36
for v in ("Python", "Ruby"):
    desloc = (h / 2 + 0.015) * (1 if v == "Python" else -1)
    vals = [d[(d.versao == v) & (d.pagina == pg)]["media_ms"].iloc[0] for pg in ordem]
    ax.barh(y + desloc, vals, height=h, color=COR[v], zorder=3)
    for yi, val in zip(y, vals):
        ax.annotate(f"{br(val, 0)} ms", (val, yi + desloc), xytext=(5, 0), textcoords="offset points",
                    va="center", fontsize=10.5, color=TINTA2)
lat = [esp[pg]["latencia_ms"] for pg in ordem]
ax.scatter(lat, y, marker="|", s=520, color=TINTA, zorder=4, linewidths=2.2)
ax.set_yticks(y)
ax.set_yticklabels([f"{pg}  ({esp[pg]['bytes']/1024:.0f} KB · {esp[pg]['links']} links)" for pg in ordem])
ax.grid(axis="y", visible=False)
ax.set_xlabel("Tempo médio de resposta (ms)")
ax.legend(handles=[Patch(color=COR["Python"], label="Python"), Patch(color=COR["Ruby"], label="Ruby"),
                   Line2D([], [], color=TINTA, marker="|", ls="", ms=16, mew=2.2,
                          label="latência simulada da página de origem")],
          loc="lower left", bbox_to_anchor=(0, 1.02), ncol=3, borderaxespad=0)
titulo(fig, f"Custo de cada URL sem cache ({CARGA_URL} usuários)",
       "Páginas ordenadas por tamanho. O traço preto marca a latência simulada da origem; o resto é processamento.")
salvar(fig, f"07_por_url_{CARGA_URL}u.png")
