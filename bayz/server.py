"""
Manages and launches Bayz server instance

author: William Tong (wlt2115@columbia.edu)
"""

import http.server
import json
import threading

globalData = {}

class BayzServer:
    def __init__(self, port):
        self.port = port
        self.httpd = None
        self.data = {}

    def start(self):
        def _startServer():
            server_address = ('', self.port)
            self.httpd = http.server.HTTPServer(server_address, BayzRequestHandler)
            self.httpd.serve_forever()

        if self.httpd is None:
            process = threading.Thread(target=_startServer)
            process.daemon = True
            process.start()
    
    def commit(self, data):
        global globalData
        globalData = data

    def stop(self):
        if self.httpd is not None:
            self.httpd.shutdown()
            self.httpd = None


class BayzRequestHandler(http.server.BaseHTTPRequestHandler):
    def do_HEAD(self):
        self._send_headers()

    def do_GET(self):
        global globalData

        self._send_headers()
        json_data = json.dumps(globalData)
        # json_data = json.dumps({
        #     'sound': [
        #         {
        #             'name': 'sine',
        #             'notes': [60, 63, 67, 70],
        #             'rhythm': [1, 2, 3],
        #         },
        #         {
        #             'name': 'sine',
        #             'notes': [63, 67, 70, 74],
        #             'rhythm': [3, 2, 1],
        #         }
        #     ],
        #     'cycleLength': 2,
        #     'deploy': True
        # })
        self.wfile.write(json_data.encode('utf-8'))
        globalData = {}

    def _send_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()


if __name__ == '__main__':
    srv = BayzServer(42700)
    srv.start()
    input()