// Gera a apresentacao do Trabalho 4 (.pptx pronto para importar no Google Slides).
// Uso: node gerar_apresentacao.js dados_apresentacao.json saida.pptx
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const { applyTheme } = require("/mnt/skills/public/pptx/scripts/apply_theme.js");

const D = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const SAIDA = process.argv[3] || "apresentacao.pptx";
const GRAF = D.pasta_graficos;

const THEME = {
  name: "Link Extractor Perf",
  headFontFace: "Arial",
  bodyFontFace: "Arial",
  colors: {
    dk1: "1F2328", lt1: "FFFFFF", dk2: "15202B", lt2: "F2F4F7",
    accent1: "2A78D6", accent2: "EB6834", accent3: "0E9F6E", accent4: "57606A",
    accent5: "D0D7DE", accent6: "0B6B47", hlink: "2A78D6", folHlink: "6250D6",
  },
};
// hex usados onde o pptxgenjs so aceita hex
const HX = { tinta: "1F2328", tinta2: "57606A", mudo: "8C959F", escuro: "15202B", painel: "F2F4F7",
  borda: "D0D7DE", py: "2A78D6", rb: "EB6834", verde: "0E9F6E", verdeEsc: "0B6B47", chip: "E3F4EC",
  branco: "FFFFFF", escuro2: "22303D", verdeClaro: "7EE2B8" };
const MONO = "Courier New";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5 in
pres.title = "Testes de desempenho – Link Extractor";
pres.author = "Equipe do Trabalho 4";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;

// ------------------------------------------------------------------ layouts
pres.defineSlideMaster({
  title: "CAPA",
  background: { color: HX.escuro },
  objects: [],
});
pres.defineSlideMaster({
  title: "CONTEUDO",
  background: { color: HX.branco },
  margin: [0.5, 0.6, 0.5, 0.6],
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.62, w: 12.13, h: 0.7,
        fontSize: 32, bold: true, color: C.text1, valign: "middle", align: "left", margin: 0 }, text: "" } },
    { text: { text: "Trabalho 4 · Testes de desempenho do Link Extractor",
        options: { x: 0.6, y: 7.05, w: 8, h: 0.3, fontSize: 10, color: C.accent4, margin: 0 } } },
  ],
  slideNumber: { x: 12.13, y: 7.05, w: 0.6, h: 0.3, fontSize: 10, color: HX.tinta2, align: "right" },
});
pres.defineSlideMaster({
  title: "ESCURO",
  background: { color: HX.escuro },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.62, w: 12.13, h: 0.8,
        fontSize: 34, bold: true, color: C.background1, valign: "middle", align: "left", margin: 0 }, text: "" } },
  ],
  slideNumber: { x: 12.13, y: 7.05, w: 0.6, h: 0.3, fontSize: 10, color: HX.mudo, align: "right" },
});

// ------------------------------------------------------------------ helpers
function chip(slide, texto, opts = {}) {
  const escuro = opts.escuro;
  const w = 0.16 + texto.length * 0.105;
  slide.addText(texto, { x: 0.6, y: 0.22, w, h: 0.32, fontFace: MONO, fontSize: 12, bold: true,
    color: escuro ? HX.verdeClaro : HX.verdeEsc, fill: { color: escuro ? HX.escuro2 : HX.chip },
    shape: pres.shapes.ROUNDED_RECTANGLE, rectRadius: 0.06, align: "center", valign: "middle",
    margin: 0, isTextBox: true, objectName: "chip" });
}
function lead(slide, texto, y = 1.36, cor = HX.tinta2) {
  slide.addText(texto, { x: 0.6, y, w: 12.13, h: 0.6, fontSize: 16, color: cor, margin: 0,
    valign: "top", isTextBox: true, objectName: "lead" });
}
let NUM = 0;
const proximo = (rot) => `${String(++NUM).padStart(2, "0")} · ${rot}`;
function conteudo(secao, rotChip, titulo) {
  const s = pres.addSlide({ masterName: "CONTEUDO", sectionTitle: secao });
  chip(s, proximo(rotChip));
  s.addText(titulo, { placeholder: "title" });
  return s;
}
function grafico(secao, numChip, titulo, sub, arquivo, w, h, nota) {
  const s = conteudo(secao, numChip, titulo);
  lead(s, sub);
  const x = (13.33 - w) / 2;
  s.addImage({ path: path.join(GRAF, arquivo), x, y: 2.05, w, h, altText: titulo, objectName: "grafico" });
  if (nota) s.addNotes(nota);
  return s;
}
const fmt = (v, d = 0) => Number(v).toLocaleString("pt-BR", { minimumFractionDigits: d, maximumFractionDigits: d });
const limpa = (txt) => txt.replace(/,0+$/, "").replace(/(,\d*?)0+$/, "$1");
const fmtMs = (v) => (v >= 1000 ? limpa(fmt(v / 1000, 2)) + " s" : limpa(fmt(v, v < 10 ? 1 : 0)) + " ms");
const fmtPct = (v) => (v < 1 ? "<1%" : fmt(v, 0) + "%");

// ================================================================== 1. capa
pres.addSection({ title: "Abertura" });
{
  const s = pres.addSlide({ masterName: "CAPA", sectionTitle: "Abertura" });
  chip(s, "trabalho 4 · testes de desempenho", { escuro: true });
  s.addText("Link Extractor sob carga", { x: 0.6, y: 2.0, w: 12.1, h: 1.1, fontSize: 48, bold: true,
    color: HX.branco, margin: 0, isTextBox: true, objectName: "titulo-capa" });
  s.addText("Testes de desempenho do serviço de extração de links: Python × Ruby, com e sem cache Redis, usando Locust",
    { x: 0.6, y: 3.15, w: 10.5, h: 0.9, fontSize: 20, color: "C9D1D9", margin: 0, isTextBox: true, objectName: "subtitulo-capa" });
  // faixa de numeros-chave do estudo
  const itens = [[String(D.n_cenarios), "cenários de teste"], [fmt(D.total_req), "requisições medidas"],
    [String(D.n_urls), "URLs por usuário virtual"], [`${D.usuarios[0]} a ${D.usuarios[D.usuarios.length - 1]}`, "usuários virtuais simultâneos"]];
  itens.forEach(([n, t], i) => {
    const x = 0.6 + i * 3.05;
    s.addText([{ text: n, options: { fontSize: 30, bold: true, color: HX.branco, breakLine: true } },
      { text: t, options: { fontSize: 13, color: "AEB8C2" } }],
      { x, y: 4.75, w: 2.8, h: 1.0, margin: 0, valign: "top", isTextBox: true, objectName: `kpi-${i}` });
  });
  s.addText(`Execução dos testes: ${D.data_execucao}`, { x: 0.6, y: 6.75, w: 8, h: 0.35, fontSize: 12,
    color: "AEB8C2", margin: 0, isTextBox: true });
}

// ================================================================== 2. equipe
{
  const s = conteudo("Abertura", "equipe", "Equipe");
  lead(s, "Integrantes que realizaram o trabalho");
  const linhas = [[{ text: "Nome", options: { bold: true, color: HX.branco, fill: { color: HX.escuro } } },
    { text: "Matrícula", options: { bold: true, color: HX.branco, fill: { color: HX.escuro } } }]];
  D.equipe.forEach((m) => linhas.push([{ text: m.nome, options: { color: m.placeholder ? HX.mudo : HX.tinta, italic: !!m.placeholder } },
    { text: m.matricula, options: { color: m.placeholder ? HX.mudo : HX.tinta, italic: !!m.placeholder, fontFace: MONO } }]));
  s.addTable(linhas, { x: 0.6, y: 2.1, w: 8.4, colW: [5.9, 2.5], fontSize: 18, rowH: 0.62, valign: "middle",
    border: { type: "solid", pt: 0.75, color: HX.borda }, margin: [0, 0.15, 0, 0.15], objectName: "tabela-equipe" });
}

// ================================================================== 3. resumo
{
  const s = conteudo("Abertura", "resumo", "O que os testes mostraram");
  lead(s, D.textos.resumo_lead);
  D.cards.forEach((c, i) => {
    const x = 0.6 + i * 4.13, y = 2.0, w = 3.83, h = 3.75;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: HX.painel },
      line: { color: HX.painel }, objectName: `card-${i}` });
    s.addText(c.numero, { x: x + 0.3, y: y + 0.3, w: w - 0.6, h: 1.1, fontSize: 40, bold: true,
      color: c.cor ? c.cor : HX.tinta, margin: 0, valign: "middle", isTextBox: true, fit: "shrink" });
    s.addText(c.rotulo, { x: x + 0.3, y: y + 1.35, w: w - 0.6, h: 0.65, fontSize: 15, bold: true,
      color: HX.tinta, margin: 0, valign: "top", isTextBox: true });
    s.addText(c.texto, { x: x + 0.3, y: y + 2.05, w: w - 0.6, h: 1.55, fontSize: 13.5, color: HX.tinta2,
      margin: 0, valign: "top", isTextBox: true });
  });
  if (D.textos.resumo_rodape) s.addText(D.textos.resumo_rodape, { x: 0.6, y: 6.05, w: 12.13, h: 0.7, fontSize: 14,
    color: HX.tinta, margin: 0, valign: "top", isTextBox: true });
}

// ================================================================== 4. arquitetura
pres.addSection({ title: "Ferramenta e método" });
{
  const s = conteudo("Ferramenta e método", "sistema testado", "O que foi testado");
  lead(s, "Somente o serviço de extração de links (a API), chamado diretamente pelo Locust, sem o front-end PHP");
  const caixa = (x, y, w, h, titulo, sub, cor, fill) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: fill || HX.painel },
      line: { color: cor || HX.borda, width: 1.5 } });
    s.addText([{ text: titulo, options: { bold: true, fontSize: 16, color: HX.tinta, breakLine: true } },
      { text: sub, options: { fontSize: 12, color: HX.tinta2 } }],
      { x: x + 0.15, y, w: w - 0.3, h, align: "center", valign: "middle", margin: 0, isTextBox: true });
  };
  // seta horizontal com rotulo (1 ou 2 linhas) acima dela
  const seta = (x1, x2, y, rot, mono) => {
    s.addShape(pres.shapes.LINE, { x: x1, y, w: x2 - x1, h: 0, line: { color: HX.tinta2, width: 1.75, endArrowType: "triangle" } });
    if (rot) s.addText(rot, { x: x1, y: y - 0.58, w: x2 - x1, h: 0.52, fontSize: 11, color: HX.tinta2, align: "center",
      valign: "bottom", margin: 0, isTextBox: true, fontFace: mono ? MONO : undefined });
  };
  // grupo "servico de extracao" (so uma versao no ar por vez)
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 4.1, y: 2.0, w: 4.1, h: 3.45, rectRadius: 0.08, fill: { color: HX.branco },
    line: { color: HX.mudo, width: 1, dashType: "dash" } });
  s.addText("Serviço de extração (uma versão por vez)", { x: 4.1, y: 2.08, w: 4.1, h: 0.3, fontSize: 12, bold: true,
    color: HX.tinta2, align: "center", margin: 0, isTextBox: true });
  caixa(0.6, 2.97, 2.3, 1.5, "Locust", "usuários virtuais\n(gerador de carga)");
  caixa(4.35, 2.5, 3.6, 1.25, "Python", "Flask + BeautifulSoup · porta 5000", HX.py, "EAF2FC");
  caixa(4.35, 3.95, 3.6, 1.25, "Ruby", "Sinatra + Nokogiri · porta 4567", HX.rb, "FDEFE8");
  caixa(9.6, 2.05, 3.13, 1.2, "Redis", "cache: URL → JSON de links");
  caixa(9.6, 4.15, 3.13, 1.2, "Site de teste", "10 páginas HTML\n(origem das URLs)");
  seta(2.9, 4.1, 3.72, "GET\n/api/<url>", true);
  seta(8.2, 9.6, 2.65, "1. consulta\no cache");
  seta(8.2, 9.6, 4.75, "2. se faltar,\nbaixa a página");
  s.addText("Uma versão por vez fica no ar. Com cache, a 1ª requisição de cada URL baixa a página, extrai os links e grava o JSON no Redis; as seguintes são respondidas direto do Redis. Sem cache (CACHE_ENABLED=false), toda requisição baixa e analisa a página.",
    { x: 0.6, y: 5.75, w: 12.1, h: 0.9, fontSize: 14, color: HX.tinta2, margin: 0, valign: "top", isTextBox: true });
}

// ================================================================== 5. ferramenta
{
  const s = conteudo("Ferramenta e método", "ferramenta", "Ferramenta de carga: Locust");
  lead(s, "Ferramenta open-source em Python em que o comportamento de cada usuário virtual é escrito como código");
  const bul = [
    ["Usuários virtuais como classes Python", "cada usuário executa as tarefas (@task) e espera entre elas (wait_time)"],
    ["Modo headless, sem interface", "parâmetros por linha de comando: nº de usuários (-u), taxa de criação (-r), duração (-t)"],
    ["Métricas por requisição e agregadas", "média, mediana, mín/máx, percentis (p50…p99,9), req/s e falhas, gravadas em CSV e HTML"],
    ["Validação da resposta no próprio script", "catch_response permite marcar como falha uma resposta HTTP 200 com conteúdo errado"],
  ];
  const textos = [];
  bul.forEach(([t, d], i) => {
    textos.push({ text: t, options: { bold: true, fontSize: 16, color: HX.tinta, breakLine: true } });
    textos.push({ text: d, options: { fontSize: 14, color: HX.tinta2, breakLine: i < bul.length - 1, paraSpaceAfter: 12 } });
  });
  s.addText(textos, { x: 0.6, y: 2.0, w: 6.0, h: 4.6, margin: 0, valign: "top", isTextBox: true });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 7.0, y: 2.0, w: 5.73, h: 4.6, rectRadius: 0.06, fill: { color: HX.escuro }, line: { color: HX.escuro } });
  s.addText("Comando de cada cenário", { x: 7.3, y: 2.2, w: 5.2, h: 0.35, fontSize: 13, bold: true, color: HX.verdeClaro, margin: 0, isTextBox: true });
  s.addText(D.textos.comando_locust, { x: 7.3, y: 2.65, w: 5.2, h: 2.4, fontFace: MONO, fontSize: 12, color: "E6EDF3", margin: 0, valign: "top", isTextBox: true });
  s.addText(D.textos.versoes_ferramentas, { x: 7.3, y: 4.75, w: 5.2, h: 1.5, fontSize: 12, color: "AEB8C2", margin: 0, valign: "top", isTextBox: true });
}

// ================================================================== 6. script
{
  const s = conteudo("Ferramenta e método", "usuário virtual", "Script do usuário virtual (locustfile.py)");
  lead(s, "Cada usuário faz uma sequência de 10 invocações ao serviço, com uma URL diferente em cada uma");
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 1.95, w: 7.75, h: 4.85, rectRadius: 0.05, fill: { color: HX.escuro }, line: { color: HX.escuro } });
  s.addText(D.textos.codigo, { x: 0.8, y: 2.08, w: 7.4, h: 4.6, fontFace: MONO, fontSize: 11, color: "E6EDF3", margin: 0, valign: "top", isTextBox: true, objectName: "codigo" });
  const notas = [
    ["10 URLs diferentes", "random.sample sorteia a ordem das 10 páginas a cada sequência, para os usuários não pedirem a mesma página ao mesmo tempo"],
    ["Pausa entre invocações", "0,5 a 1,5 s (média 1 s): cada usuário gera ≈ 1 requisição/s enquanto o serviço responde rápido"],
    ["Validação do resultado", "conta como falha se o status não for 200 ou se a lista não tiver exatamente os links da página"],
    ["Registro bruto", "o script completo também grava o tempo de cada requisição (CSV) para a curva de distribuição"],
  ];
  const t = [];
  notas.forEach(([a, b], i) => {
    t.push({ text: `${i + 1}  ${a}`, options: { bold: true, fontSize: 14, color: HX.tinta, breakLine: true } });
    t.push({ text: b, options: { fontSize: 12, color: HX.tinta2, breakLine: i < notas.length - 1, paraSpaceAfter: 10 } });
  });
  s.addText(t, { x: 8.65, y: 1.95, w: 4.08, h: 4.85, margin: 0, valign: "top", isTextBox: true });
}

// ================================================================== 7. ambiente
{
  const s = conteudo("Ferramenta e método", "ambiente", "Ambiente e cuidados de medição");
  lead(s, "Tudo na mesma máquina (2 núcleos, 8 GB), com o serviço medido isolado em um núcleo");
  const cards = D.textos.ambiente;
  cards.forEach((c, i) => {
    const col = i % 2, lin = Math.floor(i / 2);
    const x = 0.6 + col * 6.17, y = 2.0 + lin * 2.45, w = 5.96, h = 2.25;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.06, fill: { color: HX.painel }, line: { color: HX.painel } });
    s.addText([{ text: c.titulo, options: { bold: true, fontSize: 16, color: HX.tinta, breakLine: true, paraSpaceAfter: 6 } },
      { text: c.texto, options: { fontSize: 14, color: HX.tinta2 } }],
      { x: x + 0.25, y: y + 0.18, w: w - 0.5, h: h - 0.3, margin: 0, valign: "top", isTextBox: true });
  });
}

// ================================================================== 8. URLs
{
  const s = conteudo("Ferramenta e método", "URLs de entrada", "As 10 URLs passadas ao serviço");
  lead(s, "Páginas que imitam tipos reais de sites, com tamanhos e quantidades de links diferentes");
  const cab = ["Página (URL http://127.0.0.1:8080/…)", "Links", "Tamanho", "Latência simulada"];
  const linhas = [cab.map((t, j) => ({ text: t, options: { bold: true, color: HX.branco, fill: { color: HX.escuro }, align: j ? "right" : "left" } }))];
  D.paginas.forEach((p, i) => linhas.push([
    { text: `${p.nome}.html`, options: { fontFace: MONO } },
    { text: fmt(p.links), options: { align: "right" } },
    { text: `${fmt(p.kb, 0)} KB`, options: { align: "right" } },
    { text: `${p.latencia_ms} ms`, options: { align: "right" } }]));
  s.addTable(linhas, { x: 0.6, y: 1.95, w: 8.2, colW: [4.0, 1.2, 1.4, 1.6], fontSize: 12.5, rowH: 0.405,
    color: HX.tinta, valign: "middle", border: { type: "solid", pt: 0.5, color: HX.borda }, margin: [0, 0.12, 0, 0.12] });
  s.addText(D.textos.urls_nota, { x: 9.15, y: 1.95, w: 3.58, h: 4.7, fontSize: 13, color: HX.tinta2, margin: 0, valign: "top", isTextBox: true, paraSpaceAfter: 8 });
}

// ================================================================== 9. cenarios
{
  const s = conteudo("Ferramenta e método", "cenários", `${D.n_cenarios} cenários de teste`);
  lead(s, "2 versões × 2 modos de cache × 6 quantidades de usuários virtuais; cada cenário foi executado separadamente");
  const usu = D.usuarios.join(" · ");
  const x0 = 2.6, y0 = 2.35, cw = 4.0, rh = 1.15;
  ["Sem cache", "Com cache (Redis)"].forEach((t, j) => s.addText(t, { x: x0 + j * (cw + 0.15), y: y0 - 0.45, w: cw, h: 0.35, fontSize: 14, bold: true, color: HX.tinta, align: "center", margin: 0, isTextBox: true }));
  [["Python", HX.py, "EAF2FC"], ["Ruby", HX.rb, "FDEFE8"]].forEach(([v, cor, fill], i) => {
    s.addText(v, { x: 0.6, y: y0 + i * (rh + 0.15), w: 1.85, h: rh, fontSize: 18, bold: true, color: HX.tinta, valign: "middle", margin: 0, isTextBox: true });
    s.addShape(pres.shapes.OVAL, { x: 0.6 + 1.0, y: y0 + i * (rh + 0.15) + rh / 2 - 0.09, w: 0.18, h: 0.18, fill: { color: cor }, line: { color: cor } });
    for (let j = 0; j < 2; j++) {
      s.addText([{ text: `${usu}`, options: { fontSize: 16, bold: true, color: HX.tinta, breakLine: true } },
        { text: "usuários virtuais", options: { fontSize: 11, color: HX.tinta2 } }],
        { x: x0 + j * (cw + 0.15), y: y0 + i * (rh + 0.15), w: cw, h: rh, align: "center", valign: "middle", margin: 0,
          fill: { color: fill }, line: { color: cor, width: 1 }, shape: pres.shapes.ROUNDED_RECTANGLE, rectRadius: 0.06, isTextBox: true });
    }
  });
  const params = D.textos.parametros;
  const t = [];
  params.forEach(([a, b], i) => {
    t.push({ text: a + "  ", options: { bold: true, fontSize: 13, color: HX.tinta } });
    t.push({ text: b, options: { fontSize: 13, color: HX.tinta2, breakLine: i < params.length - 1, paraSpaceAfter: 7 } });
  });
  s.addText(t, { x: 0.6, y: 5.05, w: 12.13, h: 1.8, margin: 0, valign: "top", isTextBox: true, objectName: "parametros" });
}

// ================================================================== graficos
pres.addSection({ title: "Resultados" });
D.graficos.forEach((g, i) => grafico("Resultados", g.chip, g.titulo, g.sub, g.arquivo, g.w, g.h, g.nota));

// ================================================================== achado: limite do WEBrick
if (D.webrick) {
  const W = D.webrick;
  const s = conteudo("Resultados", "achado", W.titulo);
  lead(s, W.lead);
  W.evidencias.forEach((e, i) => {
    const y = 2.0 + i * 1.6;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y, w: 5.5, h: 1.4, rectRadius: 0.06, fill: { color: HX.painel }, line: { color: HX.painel } });
    s.addText(e.numero, { x: 0.85, y, w: 2.45, h: 1.4, fontSize: 28, bold: true, color: HX.tinta, valign: "middle", margin: 0, isTextBox: true });
    s.addText(e.texto, { x: 3.4, y, w: 2.55, h: 1.4, fontSize: 13, color: HX.tinta2, valign: "middle", margin: 0, isTextBox: true });
  });
  const t = [];
  W.explicacao.forEach(([a, b], i) => {
    t.push({ text: a, options: { bold: true, fontSize: 16, color: HX.tinta, breakLine: true } });
    t.push({ text: b, options: { fontSize: 13.5, color: HX.tinta2, breakLine: i < W.explicacao.length - 1, paraSpaceAfter: 14 } });
  });
  s.addText(t, { x: 6.55, y: 2.0, w: 6.18, h: 4.6, margin: 0, valign: "top", isTextBox: true });
  if (W.nota) s.addNotes(W.nota);
}

// ================================================================== tabelas
["Python", "Ruby"].forEach((v, k) => {
  const s = conteudo("Resultados", "números", `Resumo numérico – ${v}`);
  lead(s, "Estatísticas finais do Locust em cada cenário (90 s de medição). Planilha completa: planilha_resultados.xlsx");
  const cab = ["Cache", "Usuários", "Requisições", "Falhas", "Média", "Mediana", "p90", "p95", "p99", "Vazão (req/s)", "CPU serviço"];
  const linhas = [cab.map((t, j) => ({ text: t, options: { bold: true, color: HX.branco, fill: { color: HX.escuro }, align: j > 1 ? "right" : "left" } }))];
  D.linhas.filter((r) => r.versao === v).forEach((r) => {
    const sem = r.cache === "Sem cache";
    const o = (txt, al = "right") => ({ text: txt, options: { align: al, fill: { color: sem ? "F6F8FA" : HX.branco } } });
    linhas.push([o(r.cache, "left"), o(String(r.usuarios), "left"), o(fmt(r.requisicoes)), o(fmt(r.falhas)), o(fmtMs(r.media_ms)),
      o(fmtMs(r.mediana_ms)), o(fmtMs(r.p90_ms)), o(fmtMs(r.p95_ms)), o(fmtMs(r.p99_ms)), o(fmt(r.req_por_s, 1)), o(fmtPct(r.cpu_servico_pct))]);
  });
  s.addTable(linhas, { x: 0.6, y: 1.95, w: 12.13, colW: [1.45, 1.0, 1.25, 0.85, 1.05, 1.05, 1.0, 1.0, 1.0, 1.28, 1.2],
    fontSize: 12, rowH: 0.36, color: HX.tinta, valign: "middle", border: { type: "solid", pt: 0.5, color: HX.borda }, margin: [0, 0.1, 0, 0.1] });
});

// ================================================================== conclusoes
pres.addSection({ title: "Conclusões" });
{
  const s = pres.addSlide({ masterName: "ESCURO", sectionTitle: "Conclusões" });
  chip(s, proximo("conclusões"), { escuro: true });
  s.addText("Conclusões", { placeholder: "title" });
  const t = [];
  D.textos.conclusoes.forEach(([a, b], i) => {
    t.push({ text: a, options: { bold: true, fontSize: 17, color: HX.branco, breakLine: true } });
    t.push({ text: b, options: { fontSize: 14, color: "C9D1D9", breakLine: i < D.textos.conclusoes.length - 1, paraSpaceAfter: 14 } });
  });
  s.addText(t, { x: 0.6, y: 1.75, w: 12.1, h: 5.1, margin: 0, valign: "top", isTextBox: true });
}
{
  const s = conteudo("Conclusões", "arquivos", "Arquivos entregues e reprodução");
  lead(s, "Tudo o que foi usado e gerado nos testes está na pasta do trabalho");
  const metade = Math.ceil(D.textos.arquivos.length / 2);
  [D.textos.arquivos.slice(0, metade), D.textos.arquivos.slice(metade)].forEach((itens, col) => {
    const t = [];
    itens.forEach(([a, b], i) => {
      t.push({ text: a, options: { fontFace: MONO, bold: true, fontSize: 14, color: HX.tinta, breakLine: true } });
      t.push({ text: b, options: { fontSize: 13, color: HX.tinta2, breakLine: i < itens.length - 1, paraSpaceAfter: 12 } });
    });
    s.addText(t, { x: 0.6 + col * 6.2, y: 2.05, w: 5.9, h: 4.8, margin: 0, valign: "top", isTextBox: true });
  });
}

(async () => {
  await pres.writeFile({ fileName: SAIDA });
  await applyTheme(SAIDA, THEME);
  console.log("ok", SAIDA);
})();
