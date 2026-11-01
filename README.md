# Trabalho 4 – Testes de desempenho do Link Extractor

Testes de carga com **Locust** sobre as duas versões do serviço de extração de links
do [Link Extractor](https://github.com/ibnesayeed/linkextractor):

| Versão | Origem no repositório | Stack | Porta |
|---|---|---|---|
| Python | `step5/api` | Flask + requests + BeautifulSoup + Redis | 5000 |
| Ruby   | `step6/api` | Sinatra (WEBrick) + open-uri + Nokogiri + Redis | 4567 |

## Estrutura

```
servicos/python-api/      código do step5 + chave CACHE_ENABLED
servicos/ruby-api/        código do step6 + chave CACHE_ENABLED + URI.open (Ruby 3)
site-teste/               gerador e servidor das 10 páginas usadas como URL de entrada
locust/locustfile.py      comportamento do usuário virtual (10 invocações, 10 URLs diferentes)
scripts/servico.sh        sobe/derruba uma versão do serviço (com ou sem cache)
scripts/validar_servicos.py  teste funcional: Python e Ruby devolvem exatamente os links esperados
scripts/executar_cenarios.py roda os 24 cenários e salva as métricas
scripts/consolidar.py     junta tudo em CSV e na planilha planilha_resultados.xlsx
scripts/graficos.py       gera os gráficos (PNG); com --slides, a versão sem título usada nos slides
scripts/verificar_resultados.py  checagem cruzada: Locust x tempos brutos x Redis x site de origem
scripts/diagnostico_webrick.sh   teste extra: Ruby com 200 usuários e limite do WEBrick em 300
apresentacao/             gerador da apresentação (.pptx) e textos dos slides
resultados/<cenario>/     saída bruta de cada cenário (CSV/HTML do Locust, resumo, tempos brutos, meta)
```

## Alterações mínimas no código original

1. **`CACHE_ENABLED`** (variável de ambiente, padrão `true`) nas duas versões: com `false`
   o serviço ignora o Redis (não lê nem grava) – é o modo "sem cache" dos testes.
2. **Ruby:** `open(url)` → `URI.open(url)`. A partir do Ruby 3.0, `Kernel#open` não abre mais URLs
   (o Dockerfile original usa `ruby:2.6`, onde as duas formas funcionam).

3. **Ruby (só para o diagnóstico):** se a variável `WEBRICK_MAX_CLIENTS` existir, ela muda o limite de
   conexões simultâneas do WEBrick (padrão 100). Nos 24 cenários ela não foi usada; o teste extra
   `scripts/diagnostico_webrick.sh` repete o Ruby com 200 usuários usando 300.

Nada mais foi alterado: o Flask continua no servidor de desenvolvimento (`app.run`) e o Sinatra no WEBrick, como no tutorial.

## Como reproduzir

```bash
# dependências
python3 -m venv venv && ./venv/bin/pip install flask beautifulsoup4 redis requests locust pandas matplotlib openpyxl psutil
sudo apt-get install redis-server ruby ruby-sinatra ruby-nokogiri ruby-redis ruby-webrick   # ou: gem install sinatra nokogiri redis webrick

python3 site-teste/gerar_paginas.py                          # gera as 10 páginas e esperado.json
./venv/bin/python scripts/executar_cenarios.py               # 24 cenários (~45 min); sobe Redis e o site sozinho
./venv/bin/python scripts/consolidar.py                      # CSV + planilha
./venv/bin/python scripts/graficos.py                        # gráficos em resultados/graficos/
```

Para rodar um cenário isolado:

```bash
scripts/servico.sh start ruby nocache
locust -f locust/locustfile.py --host http://127.0.0.1:4567 --headless -u 50 -r 10 -t 95s --reset-stats --csv saida/locust
```

Observação: o Locust 2.47 às vezes registra um erro de "I/O operation on closed file" ao encerrar
(o gravador periódico de CSV tenta escrever depois que os arquivos foram fechados). Por isso os CSVs
`locust_stats.csv` podem ficar até 1 s defasados; as métricas oficiais de cada cenário vêm de
`resumo.json`, gravado pelo próprio locustfile no encerramento com as estatísticas finais.

Para testar com sites reais em vez do site de teste, crie um arquivo com 10 URLs (uma por linha)
e rode o Locust com `URLS_FILE=urls.txt` (a checagem de quantidade de links é desligada nesse caso).
Com Docker (por exemplo no Play-with-Docker), use os `docker-compose.yml` do `step5`/`step6` com as
pastas `servicos/*-api` e acrescente `CACHE_ENABLED=false` ao `environment` do serviço `api` para o modo sem cache.
