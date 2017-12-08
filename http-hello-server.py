#!/usr/bin/env python3
import argparse
import http.server
import logging
from http import HTTPStatus
import socketserver
import socket

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

class HttpServer(socketserver.TCPServer):
    # prevent "Address already in use" error when restarting the server program
    # after a socket has been opened
    allow_reuse_address = True

def say_hello(self):
    self.send_response(HTTPStatus.OK)
    self.send_header("Content-type", "text/plain")
    body = "hello from {}:{}!\n".format(self.hostname, self.port)

    body_bytes = body.encode('UTF-8')
    self.send_header("Content-Length", len(body_bytes))
    self.wfile.write(body_bytes)



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, help="HTTP port to serve on.")
    args = parser.parse_args()

    if not args.port:
        raise ValueError("no port given")

    Handler = http.server.SimpleHTTPRequestHandler
    Handler.port = args.port
    Handler.hostname = socket.gethostname()
    Handler.do_GET = say_hello

    httpd = socketserver.TCPServer(("", args.port), Handler)

    print("serving at port", args.port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt as e:
        log.debug("Interrupted by user. Shutting down ...")
    finally:
        log.debug("shutting down server ...")
        httpd.shutdown()
        log.debug("server shut down.")
