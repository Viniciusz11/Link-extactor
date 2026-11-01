#!/usr/bin/env python3
"""
Gera as 10 paginas HTML usadas como alvo do teste de carga.

Cada pagina imita um tipo de site real (portal de noticias, wiki, loja...),
com quantidades de links e tamanhos diferentes. A quantidade exata de links
de cada pagina e gravada em esperado.json, para que o script do Locust possa
conferir se o servico de extracao devolveu o resultado correto.
"""
import json
import random
from pathlib import Path

AQUI = Path(__file__).parent
PASTA = AQUI / "paginas"
PASTA.mkdir(exist_ok=True)

# nome, titulo, n_links, n_paragrafos, latencia_ms (simula a rede ate o site de origem)
PAGINAS = [
    ("noticias",     "Portal de Noticias",        650,  60, 180),
    ("blog",         "Blog de Tecnologia",        120,  40, 120),
    ("wiki",         "Artigo de Enciclopedia",   1100, 150, 250),
    ("loja",         "Loja Online - Eletronicos", 420,  30, 200),
    ("documentacao", "Documentacao de API",       300,  80,  90),
    ("universidade", "Portal da Universidade",    220,  25, 300),
    ("forum",        "Forum de Discussao",        500, 100, 160),
    ("pessoal",      "Pagina Pessoal",             35,   8,  60),
    ("agregador",    "Agregador de Links",       1500,  10, 140),
    ("receitas",     "Site de Receitas",          160,  35, 110),
]

PALAVRAS = ("dados sistema desempenho rede servidor cliente requisicao cache memoria "
            "processamento usuario aplicacao servico container imagem docker redis "
            "python ruby latencia vazao carga teste resultado analise grafico media "
            "mediana percentil tempo resposta arquitetura microsservico orquestracao "
            "pagina link extracao conteudo noticia artigo produto preco receita forum "
            "comentario universidade curso disciplina pesquisa projeto equipe").split()

DOMINIOS = ["exemplo.com.br", "noticias.exemplo.org", "wiki.exemplo.org", "loja.exemplo.com",
            "docs.exemplo.dev", "ufc.exemplo.br", "forum.exemplo.net", "cdn.exemplo.com",
            "github.com", "youtube.com", "twitter.com", "linkedin.com"]


def frase(rng, a=6, b=18):
    return " ".join(rng.choice(PALAVRAS) for _ in range(rng.randint(a, b))).capitalize()


def href(rng, i):
    """Mistura de links absolutos, relativos, ancoras, query strings e mailto (todos ASCII)."""
    tipo = rng.random()
    slug = "-".join(rng.choice(PALAVRAS) for _ in range(rng.randint(1, 4)))
    if tipo < 0.40:
        return f"/{slug}/{i}"
    if tipo < 0.55:
        return f"{slug}-{i}.html"
    if tipo < 0.80:
        return f"https://{rng.choice(DOMINIOS)}/{slug}/{i}"
    if tipo < 0.88:
        return f"/busca?q={slug.replace('-', '+')}&pagina={i}"
    if tipo < 0.95:
        return f"#secao-{i}"
    return f"mailto:contato{i}@exemplo.com.br"


def ancora(rng, i):
    # ~8% dos links sao imagens clicaveis (o servico devolve o texto "[IMG]")
    if rng.random() < 0.08:
        return f'<a href="{href(rng, i)}"><img src="/img/{i}.png" alt=""></a>'
    return f'<a href="{href(rng, i)}">{frase(rng, 1, 5)}</a>'


def gerar(nome, titulo, n_links, n_par, rng):
    links = [ancora(rng, i) for i in range(n_links)]
    # distribui os links entre menu, corpo, barra lateral e rodape
    n_menu = min(12, n_links // 5)
    n_rodape = min(20, n_links // 6)
    n_lateral = n_links // 5
    menu = links[:n_menu]
    rodape = links[n_menu:n_menu + n_rodape]
    lateral = links[n_menu + n_rodape:n_menu + n_rodape + n_lateral]
    corpo = links[n_menu + n_rodape + n_lateral:]

    paragrafos = []
    por_par = max(1, len(corpo) // max(1, n_par))
    for p in range(n_par):
        trecho = corpo[p * por_par:(p + 1) * por_par]
        texto = " ".join(f"{frase(rng)} {a}" for a in trecho)
        paragrafos.append(f"<p>{frase(rng, 20, 60)}. {texto} {frase(rng, 10, 30)}.</p>")
    sobra = corpo[n_par * por_par:]
    if sobra:
        paragrafos.append("<ul>" + "".join(f"<li>{a}</li>" for a in sobra) + "</ul>")

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>{titulo}</title>
<style>body{{font-family:sans-serif;max-width:960px;margin:auto}} nav a{{margin-right:8px}}</style>
</head>
<body>
<header><h1>{titulo}</h1><nav>{' '.join(menu)}</nav></header>
<div class="conteudo">
<main>
{chr(10).join(paragrafos)}
</main>
<aside><h3>Veja tambem</h3><ul>{''.join(f'<li>{a}</li>' for a in lateral)}</ul></aside>
</div>
<footer><p>Mapa do site</p>{' | '.join(rodape)}</footer>
</body>
</html>
"""
    (PASTA / f"{nome}.html").write_text(html, encoding="utf-8")
    return len(html.encode("utf-8"))


def main():
    rng = random.Random(2026)
    esperado = {}
    for nome, titulo, n_links, n_par, lat in PAGINAS:
        tamanho = gerar(nome, titulo, n_links, n_par, rng)
        esperado[nome] = {"links": n_links, "bytes": tamanho, "latencia_ms": lat}
        print(f"{nome:13s} {n_links:5d} links {tamanho/1024:8.1f} KB  latencia {lat} ms")
    (AQUI / "esperado.json").write_text(json.dumps(esperado, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
