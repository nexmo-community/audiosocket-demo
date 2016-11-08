#!/usr/bin/env python

import tornado.httpserver
import tornado.ioloop
import tornado.process
import tornado.web
import tornado.websocket
import os
import sys


clients = []


class ServerWSHandler(tornado.websocket.WebSocketHandler):
    sp = None
    connections = []
    def open(self):
        print("VAPI Client Connected")
        # Start transcoder:
        self.sp = tornado.process.Subprocess(
            "ffmpeg  -f s16le -ar 16000 -ac 1 -channel_layout mono -re  -i pipe: -f s32le -ar 44100 pipe:",
            stdin=tornado.process.Subprocess.STREAM,
            stdout=tornado.process.Subprocess.STREAM,
            shell=True,
        )
        # Transcoded bytes are sent for broadcast:
        self.sp.stdout.read_bytes(1024, streaming_callback=broadcast)

        self.connections.append(self)
        self.write_message('00000000', binary=True)

    def on_message(self, message):
        if type(message) == str:
            sys.stderr.write('.')
            sys.stderr.flush()
            self.write_message(message, binary=True)
            # Feed bytes to transcoder:
            self.sp.stdin.write(message)
        else:
            print(message)
            self.write_message('ok')

    def on_close(self):
        print("VAPI Client Disconnected")
        self.connections.remove(self)
        # We won't be needing this transcoder any more:
        self.sp.proc.terminate()


def broadcast(message):
    print("Sending")
    for conn in clients:
        conn.write_message(message, binary=True)


class ClientWSHandler(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True
    def open(self):
        print("Browser Client Connected")
        clients.append(self)

    def on_message(self, message):
        print("Browser Client Message Recieved")

    def on_close(self):
        print("Browser Client Disconnected")
        clients.remove(self)


static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
application = tornado.web.Application([
    (r'/socket', ServerWSHandler),
    (r'/browser', ClientWSHandler),
    (r'/s/(.*)', tornado.web.StaticFileHandler, {'path': static_path}),
])

if __name__ == "__main__":
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8000)
    tornado.ioloop.IOLoop.instance().start()