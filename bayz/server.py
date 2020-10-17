"""
Manages and launches Bayz server instance

author: William Tong (wlt2115@columbia.edu)
"""

import http.server
import json
import threading

class BayzServer:
    def __init__(self, port):
        self.port = port
        self.httpd = None

    def start(self):
        def _startServer():
            server_address = ('', self.port)
            self.httpd = http.server.HTTPServer(server_address, BayzServer.BayzRequestHandler)
            self.httpd.serve_forever()

        if self.httpd is None:
            process = threading.Thread(target=_startServer)
            process.daemon = True
            process.start()


    class BayzRequestHandler(http.server.BaseHTTPRequestHandler):
        def do_HEAD(self):
            self._send_headers()

        def do_GET(self):
            self._send_headers()
            json_data = json.dumps({'hello': 'world', 'received': 'ok'})
            self.wfile.write(json_data.encode('utf-8'))

        def _send_headers(self):
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()


    def stop(self):
        if self.httpd is not None:
            self.httpd.shutdown()
            self.httpd = None


if __name__ == '__main__':
    srv = BayzServer(42700)
    srv.start()
    input()