#! /usr/bin/env python

#
# A very simple HTTP server that logs all incoming GET and POST requests.
#

import cgi
import json
import logging
import optparse
import SimpleHTTPServer
import SocketServer
import sys

DEFAULT_LOGFILE="httpd.log"
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s", stream=sys.stdout)
log = logging.getLogger()


class ServerHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    def do_GET(self):
        log.info(self.headers)
        SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        log.info(self.headers)
        self.log_request()
        content_len = int(self.headers.getheader('content-length'))
        post_body = self.rfile.read(content_len)
        # prettify output if we know it is of type json type
        if self.headers.getheader('content-type') == "application/json":
            post_body = json.dumps(json.loads(post_body), indent=2)
        log.info("\n" + post_body)
        SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)


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
    httpd = SocketServer.TCPServer(("", options.port), Handler)
    log.debug("Listening on port %d" % options.port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt, e:
        log.debug("Interrupted by user. Shutting down ...")
            
