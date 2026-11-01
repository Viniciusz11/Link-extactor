#!/usr/bin/env bash
# Teste de diagnostico (fora da matriz dos 24 cenarios):
# repete o cenario Ruby com 200 usuarios aumentando o limite de conexoes simultaneas
# do WEBrick (MaxClients, padrao 100) para 300, para confirmar a causa das falhas.
set -euo pipefail
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
export WEBRICK_MAX_CLIENTS=300
python3 "$RAIZ/scripts/executar_cenarios.py" --versoes ruby --caches com,sem --usuarios 200 \
  --duracao 90 --saida "$RAIZ/resultados_diagnostico/webrick-maxclients-300"
