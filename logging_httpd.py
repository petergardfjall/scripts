#! /usr/bin/env python

#
# A very simple HTTP server that logs all incoming GET and POST requests.
#

import cgi
import json
import logging
import optparse
from http.server import SimpleHTTPRequestHandler
import socketserver
import sys

DEFAULT_LOGFILE="httpd.log"
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s", stream=sys.stdout)
log = logging.getLogger()

request_count = 0

class HttpServer(socketserver.TCPServer):
    # prevent "Address already in use" error when restarting the server program
    # after a socket has been opened
    allow_reuse_address = True

class ServerHandler(SimpleHTTPRequestHandler):

    def do_GET(self):
        global request_count
        request_count += 1
        log.info("received request %d", request_count)
        log.info(self.headers)
        SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        global request_count
        request_count += 1
        log.info("received request %d", request_count)
        log.info(self.headers)
        self.log_request()
        content_len = int(self.headers.get('content-length'))
        post_body = self.rfile.read(content_len)
        # prettify output if we know it is of type json type
        if self.headers.get('content-type') == "application/json":
            post_body = json.dumps(json.loads(post_body), indent=2)
        log.info("\n%s", post_body)
        SimpleHTTPRequestHandler.do_GET(self)


if __name__ == "__main__":
    usage = """usage: %prog [options]

    HTTP server that logs all received GET and POST requests."""
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("--port", dest="port",
                      help="The HTTP listen port."
                      "directory. Default: 8000",
                      metavar="PORT", default=8000,
                      type=int)
    parser.add_option("--logfile", dest="logfile",
                      help="The file where log output is written."
                      " Default: %s" % DEFAULT_LOGFILE,
                      metavar="FILE", default=DEFAULT_LOGFILE,
                      type=str)
    (options, args) = parser.parse_args()
    # set up logging to file
    logfile_handler = logging.FileHandler(options.logfile, mode="w")
    logfile_handler.setLevel(logging.INFO)
    logfile_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    log.addHandler(logfile_handler)

    # start http server
    Handler = ServerHandler
    httpd = HttpServer(("", options.port), Handler)
    log.debug("Listening on port %d" % options.port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt as e:
        log.debug("Interrupted by user. Shutting down ...")
    finally:
        log.debug("shutting down server ...")
        httpd.shutdown()
        log.debug("server shut down.")
