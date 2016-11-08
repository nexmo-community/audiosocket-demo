#!/usr/bin/env python

import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
import json
import time

def is_binary(data):
	try:
		decoded = data.decode("utf-8")
		return False
	except UnicodeDecodeError:
	    return True
		
class WSHandler(tornado.websocket.WebSocketHandler):
        connections = []
        def open(self):
                print("client connected")
                self.connections.append(self)
        def on_message(self, message):
				if type(message) == str:
					print("Binary Message recieved")
					self.write_message(message, binary=True)
				else:
					print(message)
					self.write_message('ok')
        def on_close(self):
                print("client disconnected")
		def select_subprotocol(self, subprotocols):
			print(subprotocols)


def send(conn):
        conn.write_message(json.dumps(message))


application = tornado.web.Application([
    (r'/socket', WSHandler)
])


if __name__ == "__main__":
        http_server = tornado.httpserver.HTTPServer(application)
        http_server.listen(8000)
        tornado.ioloop.IOLoop.instance().start()
