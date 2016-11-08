#!/usr/bin/env python

import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
import json
import time
import os
clients = []

header = 'RIFF$\xe2\x04\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\x00\xe2\x04\x00'
payload = None
count = 0

def is_binary(data):
	try:
		decoded = data.decode("utf-8")
		return False
	except UnicodeDecodeError:
	    return True

def buffer(data):
	global count
	global payload
	if count == 0:
		payload = header + data
		count += 1
	elif count == 9:
		payload += data
		broadcast(payload)
		count = 0
		payload = None
	else:
		payload += data
		count += 1

def broadcast(payload):
	print "Sending {} bytes".format(str(len(payload)))
	for conn in clients:
		conn.write_message(payload, binary=True)
		
class ServerWSHandler(tornado.websocket.WebSocketHandler):
	connections = []
	def open(self):
		print("VAPI Client Connected")
		self.connections.append(self)
		self.write_message('00000000', binary=True)	
	def on_message(self, message):
		if type(message) == str:
			print("Binary Message recieved {}".format(str(len(message))))
			self.write_message(message, binary=True)
			buffer(message)
		else:
			print(message)
			self.write_message('ok')
	def on_close(self):
		print("VAPI Client Disconnected")
		self.connections.remove(self)

class ClientWSHandler(tornado.websocket.WebSocketHandler):
	connections = []
	def check_origin(self, origin):
	    return True
	def open(self):
		print("Browser Client Connected")
		self.connections.append(self)
		clients.append(self)
	def on_message(self, message):
		print("Browser Client Message Recieved")
	def on_close(self):
		print("Browser Client Disconnected")
		self.connections.remove(self)
		clients.remove(self)
     
static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
application = tornado.web.Application([
	(r'/', tornado.web.StaticFileHandler, {'path': static_path + 'clean.html'}),
    (r'/socket', ServerWSHandler),
	(r'/browser', ClientWSHandler),
	(r'/s/(.*)', tornado.web.StaticFileHandler, {'path': static_path}),
])


if __name__ == "__main__":
        http_server = tornado.httpserver.HTTPServer(application)
        http_server.listen(8000)
        tornado.ioloop.IOLoop.instance().start()
