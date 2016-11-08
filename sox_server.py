#!/usr/bin/env python

import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
import json
import time
import os
import tempfile
from pydub import AudioSegment

clients = []

def is_binary(data):
	try:
		decoded = data.decode("utf-8")
		return False
	except UnicodeDecodeError:
	    return True

def convert(data):
	tf = tempfile.NamedTemporaryFile(mode='w+b', suffix=".wav")
	tf.write(data)
	_input = AudioSegment.from_wav(tf.name)
	tf.close()
	tf = tempfile.NamedTemporaryFile(mode='w+b', suffix=".wav")
	output = _input.set_channels(1).set_frame_rate(44100).set_sample_width(4)
	f = output.export(tf.name, format="wav")
	return f.read()

class ServerWSHandler(tornado.websocket.WebSocketHandler):
	connections = []
	def open(self):
		print("VAPI Client Connected")
		self.connections.append(self)
		self.write_message('00000000', binary=True)	
	def on_message(self, message):
		if type(message) == str:
			print("Binary Message recieved {}".format(str(len(message))))
			newmessage = convert(message)
			self.write_message(newmessage, binary=True)
			for conn in clients:
				conn.write_message(message, binary=True)			
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
    (r'/socket', ServerWSHandler),
	(r'/browser', ClientWSHandler),
	(r'/s/(.*)', tornado.web.StaticFileHandler, {'path': static_path}),
])


if __name__ == "__main__":
        http_server = tornado.httpserver.HTTPServer(application)
        http_server.listen(8000)
        tornado.ioloop.IOLoop.instance().start()
