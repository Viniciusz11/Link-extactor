#!/usr/bin/env bash
# Sobe (ou derruba) uma versao do servico de extracao de links.
#   ./servico.sh start python|ruby cache|nocache
#   ./servico.sh stop
# O servico fica preso ao nucleo 1 da CPU (taskset); Locust, Redis e o site de
# teste ficam no nucleo 0, para que a ferramenta de carga nao dispute CPU com
# o servico medido.
set -euo pipefail
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
PY="${PY:-$(command -v python3)}"   # defina PY=caminho/do/venv/bin/python se usar venv
export REDIS_URL="redis://127.0.0.1:6379"

parar() {
  pkill -f "[p]ython-api/main.py" 2>/dev/null || true
  pkill -f "ruby.*[l]inkextractor.rb" 2>/dev/null || true
  sleep 1
}

esperar() {  # espera a porta responder
  for _ in $(seq 1 60); do
    curl -s -o /dev/null "http://127.0.0.1:$1/" && return 0
    sleep 0.5
  done
  echo "servico nao respondeu na porta $1" >&2; exit 1
}

case "${1:-}" in
  start)
    versao="$2"; modo="$3"
    parar
    [[ "$modo" == "cache" ]] && export CACHE_ENABLED=true || export CACHE_ENABLED=false
    mkdir -p "$RAIZ/logs"
    if [[ "$versao" == "python" ]]; then
      cd "$RAIZ/servicos/python-api"
      nohup taskset -c 1 "$PY" "$RAIZ/servicos/python-api/main.py" > "$RAIZ/logs/api-python.log" 2>&1 &
      esperar 5000
    else
      cd "$RAIZ/servicos/ruby-api"
      nohup taskset -c 1 /usr/bin/ruby "$RAIZ/servicos/ruby-api/linkextractor.rb" -o 0.0.0.0 -p 4567 > "$RAIZ/logs/api-ruby.log" 2>&1 &
      esperar 4567
    fi
    echo "servico $versao no ar (CACHE_ENABLED=$CACHE_ENABLED)"
    ;;
  stop) parar ;;
  *) echo "uso: $0 start python|ruby cache|nocache | stop"; exit 1 ;;
esac
