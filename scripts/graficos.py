#!/usr/bin/env python3
"""
Gera os graficos de barras (PNG) a partir de resultados/resultados_consolidados.csv.

  graficos.py [pasta_resultados]            -> resultados/graficos/*.png (com titulo)
  graficos.py [pasta_resultados] --slides   -> resultados/graficos/slides/*.png
                                               (sem titulo interno; o titulo fica no slide)

Graficos:
  01 tempo medio         barras agrupadas, um painel sem cache e outro com cache
  02 percentis           p50/p90/p95/p99 por cenario (2 x 2 paineis)
  03 vazao               req/s atendidas x demanda gerada
  04 CPU do servico      % de um nucleo
  05 ganho do cache      mediana sem cache / mediana com cache
  06 falhas              % de requisicoes com falha
"""
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
H1, H2 = (5.6, 6.2) if SLIDES else (6.8, 7.4)
TOP1, TOP2 = (0.88, 0.86) if SLIDES else (0.75, 0.78)

# ---------------------------------------------------------------- estilo
TINTA, TINTA2, MUDO = "#0b0b0b", "#52514e", "#898781"
GRADE, EIXO, FUNDO = "#e1e0d9", "#c3c2b7", "#ffffff"
VERSOES = ("Python", "Ruby")
CACHES = ("Sem cache", "Com cache")
# cor = versao (azul Python, laranja Ruby); tom = cache (forte sem cache, claro com cache)
COR = {("Python", "Sem cache"): "#2a78d6", ("Python", "Com cache"): "#9ec5f4",
       ("Ruby", "Sem cache"): "#eb6834", ("Ruby", "Com cache"): "#f7b899"}
BORDA = {"Python": "#1c5cab", "Ruby": "#b8471c"}
RAMPA = {"Python": ["#b7d3f6", "#5598e7", "#256abf", "#0d366b"],
         "Ruby": ["#f9cdb5", "#ef8a5c", "#c4521f", "#7a2c0b"]}
PCTS = [("mediana_ms", "Mediana (p50)"), ("p90_ms", "p90"), ("p95_ms", "p95"), ("p99_ms", "p99")]

plt.rcParams.update({
    "font.family": "Inter", "font.size": 13, "axes.labelsize": 13, "axes.labelcolor": TINTA2,
    "xtick.color": TINTA2, "ytick.color": TINTA2, "xtick.labelsize": 13, "ytick.labelsize": 12,
    "axes.edgecolor": EIXO, "axes.linewidth": 1, "axes.grid": True, "axes.grid.axis": "y",
    "grid.color": GRADE, "grid.linewidth": 0.8, "axes.axisbelow": True,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.facecolor": FUNDO, "axes.facecolor": FUNDO, "savefig.facecolor": FUNDO,
    "legend.frameon": False, "legend.fontsize": 12.5,
})


def br(v, casas=None):
    """numero no formato brasileiro (virgula decimal, ponto de milhar)."""
    s = f"{v:,.{casas}f}" if casas is not None else f"{v:,g}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def ms_fmt(v):
    if v >= 1000:
        return f"{br(v / 1000, 1)} s"
    if v >= 10:
        return f"{br(v, 0)} ms"
    return f"{br(v, 1)} ms"


def tick_ms(v, _=None):
    return f"{br(v / 1000)} s" if v >= 1000 else f"{br(v)} ms"


def titulo(fig, t, sub=None):
    if SLIDES:
        return
    fig.text(0.012, 0.975, t, ha="left", va="top", fontsize=19, fontweight="semibold", color=TINTA)
    if sub:
        fig.text(0.012, 0.912, sub, ha="left", va="top", fontsize=12.5, color=TINTA2)


def salvar(fig, nome):
    fig.savefig(OUT / nome, dpi=150)
    plt.close(fig)
    print("ok", OUT / nome)


def rotular(ax, barras, textos, tamanho=11):
    for b, t in zip(barras, textos):
        ax.annotate(t, (b.get_x() + b.get_width() / 2, b.get_height()), xytext=(0, 4),
                    textcoords="offset points", ha="center", va="bottom", fontsize=tamanho, color=TINTA)


# ---------------------------------------------------------------- dados
df = pd.read_csv(RES / "resultados_consolidados.csv")
USU = sorted(df["usuarios"].unique())
X = np.arange(len(USU))


def valores(v, c, col):
    d = df[(df.versao == v) & (df.cache == c)].set_index("usuarios").reindex(USU)
    return d[col].to_numpy(dtype=float)


def eixo_x(ax, rotulo="Usuários virtuais simultâneos"):
    ax.set_xticks(X)
    ax.set_xticklabels([br(u) for u in USU])
    ax.set_xlabel(rotulo)
    ax.tick_params(axis="x", length=0)


def legenda_4(fig_ou_ax, **kw):
    h = [Patch(facecolor=COR[(v, c)], edgecolor=BORDA[v], label=f"{v} · {c.lower()}")
         for v in VERSOES for c in CACHES]
    fig_ou_ax.legend(handles=h, ncol=4, handlelength=1.4, columnspacing=1.6, **kw)


def barras_4(ax, col, largura=0.2, rotulo=None, tamanho=10.5):
    """4 barras por grupo de usuarios: Python sem/com, Ruby sem/com."""
    series = [(v, c) for v in VERSOES for c in CACHES]
    for k, (v, c) in enumerate(series):
        y = valores(v, c, col)
        b = ax.bar(X + (k - 1.5) * (largura + 0.01), y, width=largura, color=COR[(v, c)],
                   edgecolor=BORDA[v], linewidth=0.8, zorder=3)
        if rotulo:
            rotular(ax, b, [rotulo(val) for val in y], tamanho)


# ---------------------------------------------------------------- 1. tempo medio
fig, axs = plt.subplots(1, 2, figsize=(13.33, H1))
fig.subplots_adjust(left=0.07, right=0.98, top=TOP1, bottom=0.16, wspace=0.18)
for ax, c in zip(axs, CACHES):
    for k, v in enumerate(VERSOES):
        y = valores(v, c, "media_ms")
        f = valores(v, c, "falhas")
        b = ax.bar(X + (k - 0.5) * 0.37, y, width=0.35, color=COR[(v, "Sem cache")],
                   edgecolor=BORDA[v], linewidth=0.8, zorder=3)
        rotular(ax, b, [ms_fmt(val) + ("*" if fi > 0 else "") for val, fi in zip(y, f)], 10.5)
    ax.set_title(c + (" (escala log)" if c == "Com cache" else ""), loc="left", fontsize=15,
                 fontweight="semibold", color=TINTA)
    if c == "Com cache":  # Python fica em ms e Ruby vai a segundos (timeouts): so a escala log mostra os dois
        ax.set_yscale("log")
        ax.set_ylim(1, 40000)
        ax.yaxis.set_major_locator(LogLocator(base=10))
        ax.yaxis.set_minor_formatter(NullFormatter())
    ax.yaxis.set_major_formatter(FuncFormatter(tick_ms))
    ax.margins(y=0.18)
    eixo_x(ax)
axs[0].set_ylabel("Tempo médio de resposta")
fig.text(0.07, 0.015, "* cenário com falhas por timeout (60 s), que entram na média; ver o gráfico de falhas",
         fontsize=10.5, color=TINTA2)
fig.legend(handles=[Patch(color=COR[(v, "Sem cache")], label=v) for v in VERSOES],
           loc="upper right", bbox_to_anchor=(0.98, 0.995 if SLIDES else 0.86), ncol=2)
titulo(fig, "Tempo médio de resposta por número de usuários",
       "Escalas diferentes em cada painel: sem cache o tempo vai a dezenas de segundos; com cache, o Python fica em milissegundos.")
salvar(fig, "01_tempo_medio.png")

# ---------------------------------------------------------------- 2. percentis
fig, axs = plt.subplots(2, 2, figsize=(13.33, H2), sharex=True, sharey=True)
fig.subplots_adjust(left=0.08, right=0.98, top=TOP2, bottom=0.10, hspace=0.32, wspace=0.06)
for i, v in enumerate(VERSOES):
    for j, c in enumerate(CACHES):
        ax = axs[i, j]
        for k, (col, nome) in enumerate(PCTS):
            ax.bar(X + (k - 1.5) * 0.2, valores(v, c, col), width=0.19, color=RAMPA[v][k], zorder=3)
        ax.set_title(f"{v} · {c.lower()}", loc="left", fontsize=14, fontweight="semibold", color=TINTA)
        ax.set_yscale("log")
        ax.set_ylim(bottom=1)
        ax.yaxis.set_major_locator(LogLocator(base=10))
        ax.yaxis.set_major_formatter(FuncFormatter(tick_ms))
        ax.yaxis.set_minor_formatter(NullFormatter())
        eixo_x(ax, "Usuários virtuais" if i == 1 else "")
CINZAS = ["#d9d8d2", "#a3a29c", "#62615d", "#0b0b0b"]
fig.legend(handles=[Patch(color=g, label=n) for g, (_, n) in zip(CINZAS, PCTS)],
           loc="upper right", bbox_to_anchor=(0.985, 0.995 if SLIDES else 0.89), ncol=4, fontsize=12)
titulo(fig, "Percentis do tempo de resposta em cada cenário",
       "Escala logarítmica (cada linha da grade = 10 vezes a anterior), igual nos quatro painéis. Mais escuro = percentil mais alto.")
salvar(fig, "02_percentis_por_cenario.png")

# ---------------------------------------------------------------- 3. vazao
fig, ax = plt.subplots(figsize=(13.33, H1))
fig.subplots_adjust(left=0.08, right=0.98, top=TOP1, bottom=0.13)
barras_4(ax, "req_por_s", rotulo=lambda val: br(val, 0))
for xi, u in zip(X, USU):  # demanda gerada: ~1 req/s por usuario
    ax.hlines(u, xi - 0.43, xi + 0.43, colors=TINTA, linestyles=(0, (4, 2)), linewidth=1.6, zorder=4)
ax.set_ylabel("Requisições atendidas por segundo")
ax.yaxis.set_major_formatter(FuncFormatter(lambda val, _: br(val)))
ax.margins(y=0.12)
eixo_x(ax)
h = [Patch(facecolor=COR[(v, c)], edgecolor=BORDA[v], label=f"{v} · {c.lower()}") for v in VERSOES for c in CACHES]
h.append(Line2D([], [], color=TINTA, ls=(0, (4, 2)), lw=1.6, label="demanda (≈ 1 req/s por usuário)"))
ax.legend(handles=h, loc="upper left", ncol=3, handlelength=1.6)
titulo(fig, "Vazão: requisições atendidas por segundo",
       "A linha tracejada é a demanda gerada. Barra abaixo dela = o serviço não dá conta e as requisições esperam em fila.")
salvar(fig, "03_vazao.png")

# ---------------------------------------------------------------- 4. CPU
fig, ax = plt.subplots(figsize=(13.33, H1))
fig.subplots_adjust(left=0.08, right=0.98, top=TOP1, bottom=0.13)
barras_4(ax, "cpu_servico_pct", rotulo=lambda val: f"{val:.0f}%")
ax.axhline(100, color=MUDO, lw=1.5, ls=":", zorder=2)
ax.set_ylim(0, 125)
ax.set_yticks([0, 20, 40, 60, 80, 100])
ax.yaxis.set_major_formatter(FuncFormatter(lambda val, _: f"{val:.0f}%"))
ax.set_ylabel("CPU do processo do serviço (% de 1 núcleo)")
eixo_x(ax)
legenda_4(ax, loc="upper left")
titulo(fig, "Uso de CPU do serviço de extração",
       "O serviço roda preso a um núcleo: 100% é o teto (Python e Ruby executam uma thread por vez por processo).")
salvar(fig, "04_cpu_servico.png")

# ---------------------------------------------------------------- 5. ganho do cache (mediana)
fig, ax = plt.subplots(figsize=(13.33, H1))
fig.subplots_adjust(left=0.08, right=0.98, top=TOP1, bottom=0.13)
def mediana_exata(v, c):
    """mediana calculada do tempo de cada requisicao (o Locust arredonda a sua: 2 ms, 12000 ms...)"""
    out = []
    for u in USU:
        f = RES / f"{v.lower()}-{'com' if c == 'Com cache' else 'sem'}-cache-{u:03d}u" / "tempos_brutos.csv"
        out.append(pd.read_csv(f, usecols=["tempo_ms"])["tempo_ms"].median())
    return np.array(out)


for k, v in enumerate(VERSOES):
    g = mediana_exata(v, "Sem cache") / mediana_exata(v, "Com cache")
    b = ax.bar(X + (k - 0.5) * 0.37, g, width=0.35, color=COR[(v, "Sem cache")], edgecolor=BORDA[v],
               linewidth=0.8, zorder=3)
    rotular(ax, b, [f"{br(val, 0)}×" for val in g], 12)
ax.set_ylabel("Mediana sem cache ÷ mediana com cache")
ax.yaxis.set_major_formatter(FuncFormatter(lambda val, _: f"{br(val)}×"))
ax.margins(y=0.12)
eixo_x(ax)
ax.legend(handles=[Patch(color=COR[(v, "Sem cache")], label=v) for v in VERSOES], loc="upper left", ncol=2)
titulo(fig, "Quantas vezes o cache acelera a resposta (mediana)",
       "Razão entre a mediana sem cache e com cache (calculada do tempo de cada requisição), para a mesma versão e carga.")
salvar(fig, "05_ganho_do_cache.png")

# ---------------------------------------------------------------- 6. falhas
df["falhas_pct"] = 100 * df["falhas"] / df["requisicoes"].clip(lower=1)
fig, ax = plt.subplots(figsize=(13.33, H1))
fig.subplots_adjust(left=0.08, right=0.98, top=TOP1, bottom=0.13)
series = [(v, c) for v in VERSOES for c in CACHES]
for k, (v, c) in enumerate(series):
    p = valores(v, c, "falhas_pct")
    n = valores(v, c, "falhas")
    b = ax.bar(X + (k - 1.5) * 0.21, p, width=0.2, color=COR[(v, c)], edgecolor=BORDA[v], linewidth=0.8, zorder=3)
    rotular(ax, b, [f"{br(pi, 1)}%" if ni > 0 else "0" for pi, ni in zip(p, n)], 10.5)
ax.set_ylabel("Requisições com falha (%)")
ax.yaxis.set_major_formatter(FuncFormatter(lambda val, _: f"{br(val)}%"))
ax.set_ylim(bottom=0)
ax.margins(y=0.15)
eixo_x(ax)
legenda_4(ax, loc="upper left")
titulo(fig, "Requisições com falha",
       "Falha = sem resposta em 60 s (timeout), status diferente de 200 ou quantidade de links errada.")
salvar(fig, "06_falhas.png")
