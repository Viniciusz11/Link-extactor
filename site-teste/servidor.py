#!/usr/bin/env python3
"""
Servidor HTTP que hospeda as 10 paginas de teste.

Cada pagina responde com uma latencia propria (+-20% de variacao aleatoria),
simulando o tempo de rede ate um site real na Internet. O servidor conta
quantas vezes cada pagina foi buscada, o que permite verificar se o servico
de extracao realmente foi ate a origem (sem cache) ou respondeu pelo Redis
(com cache).

  GET /<pagina>.html  -> pagina de teste
  GET /__stats        -> JSON com o numero de buscas por pagina
  GET /__reset        -> zera os contadores
"""
import json
import random
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

AQUI = Path(__file__).parent
ESPERADO = json.loads((AQUI / "esperado.json").read_text())
PAGINAS = {f"/{n}.html": (AQUI / "paginas" / f"{n}.html").read_bytes() for n in ESPERADO}
LATENCIA = {f"/{n}.html": v["latencia_ms"] / 1000 for n, v in ESPERADO.items()}

contador = {k: 0 for k in PAGINAS}
trava = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        caminho = self.path.split("?")[0]
        if caminho == "/__stats":
            with trava:
                corpo = json.dumps({"buscas": dict(contador), "total": sum(contador.values())}).encode()
            return self._responder(200, corpo, "application/json")
        if caminho == "/__reset":
            with trava:
                for k in contador:
                    contador[k] = 0
            return self._responder(200, b'{"ok": true}', "application/json")
        if caminho not in PAGINAS:
            return self._responder(404, b"not found", "text/plain")
        with trava:
            contador[caminho] += 1
        time.sleep(LATENCIA[caminho] * random.uniform(0.8, 1.2))
        self._responder(200, PAGINAS[caminho], "text/html; charset=utf-8")

    def _responder(self, status, corpo, tipo):
        self.send_response(status)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def log_message(self, *args):
        pass


class Servidor(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 512


if __name__ == "__main__":
    porta = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    print(f"Site de teste em http://127.0.0.1:{porta}/ ({len(PAGINAS)} paginas)", flush=True)
    Servidor(("0.0.0.0", porta), Handler).serve_forever()
