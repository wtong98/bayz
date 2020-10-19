"""
Manages and launches Bayz server instance. To launch a server instance manually,
run

$ python -m bayz.server

which launches a server on the default port 42700. To stop the server, hit
<enter>.

The protocol used to communicate with the WebAudio client is a simple JSON
messaging system. One message has the structure:

{
    deploy: [bool]       // determine whether to apply the current data
    cycleLength: [int]   // the duration (in seconds) of a cycle of music
    sound: [
        {
            name: [str],             // name of the instrument to be played
            notes: [list of ints],   // notes to be played (midi values)
            rhythm: [list of ints]   // rhythm of notes (relative durations)
        }

        // one or more sound messages like the above
    ]
}

For more information about the rhythm system, see bayz.music.py.

author: William Tong (wlt2115@columbia.edu)
"""

import http.server
import json
import threading

""" Tracks the global music information to be committed to the bayz beat """
globalData = {}

class BayzServer:
    def __init__(self, port):
        """
        param port: port to listen for bayz beats
        """

        self.port = port
        self.httpd = None
        self.data = {}

    def start(self):
        """
        Starts the server in separate thread
        """

        def _startServer():
            server_address = ('', self.port)
            self.httpd = http.server.HTTPServer(server_address, BayzRequestHandler)
            self.httpd.serve_forever()

        if self.httpd is None:
            process = threading.Thread(target=_startServer)
            process.daemon = True
            process.start()
    
    def commit(self, data):
        """
        Commits music data to the bayz beat client
        
        param data: data to commit
        """

        global globalData
        globalData = data

    def stop(self):
        """
        Stops the server
        """

        if self.httpd is not None:
            self.httpd.shutdown()
            self.httpd = None


class BayzRequestHandler(http.server.BaseHTTPRequestHandler):
    """
    Handles incoming requests from the bayz beat WebAudio client
    """

    def do_HEAD(self):
        self._send_headers()

    def do_GET(self):
        """
        Provides the music data. Once comitted, the data is reset in preparation
        for the next live code run.
        """

        global globalData

        self._send_headers()
        json_data = json.dumps(globalData)
        self.wfile.write(json_data.encode('utf-8'))
        globalData = {}

    def _send_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
    
    def log_message(self, format, *args):
        return # silence logging


if __name__ == '__main__':
    srv = BayzServer(42700)
    srv.start()
    input()