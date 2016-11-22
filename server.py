
import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
import json
import time
import os
import nexmo
from creds import *


# Varibles
clients = [] #list of browser websocket connections for receieving the binary audio data
eventclients = [] #list of browser websocket connections for receieving the event data
header = 'RIFF$\xe2\x04\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\x00\xe2\x04\x00'
payload = None #The buffered PCM frames into 200ms WAV file
count = 0 #How many PCM frames I have in the buffer
vapi_call_uuid = None
vapi_connected = False
#Create Nexmo Client
client = nexmo.Client(key=API_KEY, secret=API_SECRET, application_id=APP_ID, private_key=PRIVATE_KEY)

	
#Helper Functions
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
	#print "Sending {} bytes".format(str(len(payload)))
	for conn in clients:
		conn.write_message(payload, binary=True)
		
def broadcast_event(event):
	print "Sending Event {}".format(event)
	for conn in eventclients:
		conn.write_message(event)

def process_event(event):
	if event['direction'] == "outbound" and event['status'] ==  "answered":
		global vapi_call_uuid
		vapi_call_uuid = event['uuid']
		print "VAPI CALL ID SET AS {}".format(vapi_call_uuid)
	return True

def check_clients():
	if (len(clients) == 1 and vapi_connected == False):
		connect_vapi()
	elif (len(clients) == 0 and vapi_connected == True):
		disconnect_vapi()
	else:
		return True

def connect_vapi():
	client.create_call({'to': [{
	                  "type": "websocket",
	                  "uri": "ws://audiosocket.sammachin.com:8000/socket",
	                  "content-type": "audio/l16;rate=16000", 
	                  "headers": {
	                       "app": "audiosocket"
	                       }
	                  }],
	                 'from': {'type': 'phone', 'number': '442037831800'},
	                 'answer_url': ['http://audiosocket.sammachin.com:8000/ncco']})
	global vapi_connected
	vapi_connected = True		 
	return True


def disconnect_vapi():
	client.update_call(vapi_call_uuid, action='hangup')
	global vapi_connected
	vapi_connected = True
	return True

#The Handlers
class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("static/index.html")


class EventHandler(tornado.web.RequestHandler):
	def post(self):
		event = json.loads(self.request.body)
		print "EVENT RECEIVED {}".format(json.dumps(event))
		process_event(event)
		broadcast_event(event)        
		self.set_status(204)


class NCCOHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_header('Content-Type', 'application/json')
        self.render("static/conf.json")
		
		
class ServerWSHandler(tornado.websocket.WebSocketHandler):
	connections = []
	def open(self):
		print("VAPI Client Connected")
		self.connections.append(self)
		self.write_message('00000000', binary=True)	
	def on_message(self, message):
		if type(message) == str:
			#print("Binary Message recieved {}".format(str(len(message))))
			self.write_message(message, binary=True)
			buffer(message)
		else:
			print(message)
			self.write_message('ok')
	def on_close(self):
		print("VAPI Client Disconnected")
		self.connections.remove(self)


class ClientWSHandler(tornado.websocket.WebSocketHandler):
	def open(self):
		print("Browser Client Connected")
		clients.append(self)
		check_clients()
	def on_message(self, message):
		print("Browser Client Message Recieved")
	def on_close(self):
		print("Browser Client Disconnected")
		clients.remove(self)
		check_clients()

class ClientEventWSHandler(tornado.websocket.WebSocketHandler):
	def open(self):
		print("Browser Client Connected")
		eventclients.append(self)
	def on_message(self, message):
		print("Browser Client Message Recieved")
	def on_close(self):
		print("Browser Client Disconnected")
		eventclients.remove(self)


#The Server Config
static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/')
print static_path
application = tornado.web.Application([
	(r"/", MainHandler),
	(r"/event", EventHandler),
	(r"/ncco", NCCOHandler),
    (r'/socket', ServerWSHandler),
	(r'/browser', ClientWSHandler),
	(r'/browserevent', ClientEventWSHandler),
	(r'/s/(.*)', tornado.web.StaticFileHandler, {'path': static_path})
])


#Running It
if __name__ == "__main__":
        http_server = tornado.httpserver.HTTPServer(application)
        http_server.listen(8000)
        tornado.ioloop.IOLoop.instance().start()
