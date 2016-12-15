#!/usr/bin/env python

import json
import logging
import os.path

import nexmo
import phonenumbers
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket

from creds import Config

WAV_HEADER = 'RIFF$\xe2\x04\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>' \
             '\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\x00\xe2\x04\x00'


CONFIG = Config()


class State(object):
    def __init__(self):
        # Browser websocket connections for receiving the binary audio data:
        self.clients = []
        # Browser websocket connections for receiving the event data:
        self.eventclients = []
        self.payload = None  # The buffered PCM frames into 200ms WAV file
        self.count = 0  # How many PCM frames I have in the buffer
        self.vapi_call_uuid = None
        self.vapi_connected = False

    def buffer(self, data):
        print 'buffering:', len(data)
        if self.count == 0:
            print 'initial batch'
            self.payload = WAV_HEADER + data
            self.count += 1
        elif self.count == 9:
            print 'broadcasting'
            self.payload += data
            self.broadcast(self.payload)
            self.count = 0
            self.payload = None
        else:
            self.payload += data
            self.count += 1

    def broadcast(self, payload):
        # print "Sending {} bytes".format(str(len(payload)))
        for conn in self.clients:
            conn.write_message(payload, binary=True)

    def broadcast_event(self, event):
        print "Sending Event {}".format(event)
        for conn in self.eventclients:
            conn.write_message(event)

    def process_event(self, event):
        logging.debug("PROCESSING EVENT: %s", event)
        if event['direction'] == "outbound" and event['status'] == "answered":
            logging.debug("Setting call UUID to: %s", event['uuid'])
            self.vapi_call_uuid = event['uuid']
            print "VAPI CALL ID SET AS {}".format(self.vapi_call_uuid)
        return True

    def check_clients(self):
        print "VAPI Connected: " + str(self.vapi_connected)
        logging.debug("Clients: %s, Connected: %s", self.clients, self.vapi_connected)
        if len(self.clients) == 1 and not self.vapi_connected:
            self.connect_vapi()
        elif len(self.clients) == 0 and self.vapi_connected:
            self.disconnect_vapi()
        else:
            return True

    def connect_vapi(self):
        logging.info("Instructing VAPI to connect")
        response = client.create_call({'to': [{
                "type": "websocket",
                "uri": "ws://{host}/socket".format(host=CONFIG.host),
                "content-type": "audio/l16;rate=16000",
                "headers": {
                    "app": "audiosocket"
                }
            }],
            'from': {'type': 'phone', 'number': CONFIG.phone_number},
            'answer_url': ['https://{host}/ncco'.format(host=CONFIG.host)]})
        logging.debug(repr(response))
        self.vapi_connected = True
        return True

    def disconnect_vapi(self):
        client.update_call(self.vapi_call_uuid, action='hangup')
        self.vapi_connected = False
        return True


state = State()


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("static/index.html",
                    phone_number=format_number(CONFIG.phone_number),
                    host=CONFIG.host)


class EnvErrorsHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("static/env_errors.html", missing_envs=CONFIG.missing_keys)


class EventHandler(tornado.web.RequestHandler):
    def post(self):
        event = json.loads(self.request.body)
        print "EVENT RECEIVED {}".format(json.dumps(event))
        state.process_event(event)
        state.broadcast_event(event)
        self.set_status(204)


class NCCOHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_header('Content-Type', 'application/json')
        self.write(json.dumps([
            {
                "action": "talk",
                "text": "Connecting to Audio Socket Conference",
            },
            {
                "action": "conversation",
                "name": "audiosocket",
                "eventUrl": ["https://{host}/event".format(host=CONFIG.host)],
            }
        ]))


class ServerWSHandler(tornado.websocket.WebSocketHandler):
    connections = []

    def open(self):
        print("VAPI Client Connected")
        self.connections.append(self)
        self.write_message('00000000', binary=True)

    def on_message(self, message):
        if type(message) == str:
            # print("Binary Message received {}".format(str(len(message))))
            self.write_message(message, binary=True)
            state.buffer(message)
        else:
            print(message)
            self.write_message('ok')

    def on_close(self):
        print("VAPI Client Disconnected")
        self.connections.remove(self)


class ClientWSHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        print("Browser Client Connected")
        state.clients.append(self)
        state.check_clients()

    def on_message(self, message):
        print("Browser Client Message Received")

    def on_close(self):
        print("Browser Client Disconnected")
        state.clients.remove(self)
        state.check_clients()


class ClientEventWSHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        print("Browser Client Connected")
        state.eventclients.append(self)

    def on_message(self, message):
        print("Browser Client Message Received")

    def on_close(self):
        print("Browser Client Disconnected")
        state.eventclients.remove(self)


def format_number(number):
    if not number.startswith("+"):
        number = "+" + number
    return phonenumbers.format_number(
        phonenumbers.parse(number, None),
        phonenumbers.PhoneNumberFormat.NATIONAL)


if CONFIG.fully_configured:
    client = nexmo.Client(
        key=CONFIG.api_key,
        secret=CONFIG.api_secret,
        application_id=CONFIG.app_id,
        private_key=CONFIG.private_key,
    )

    # The Server Config
    static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               'static/')
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
else:
    application = tornado.web.Application([
        (r"/", EnvErrorsHandler),
    ])

# Running It
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.getLogger().setLevel(logging.DEBUG)
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8000)
    tornado.ioloop.IOLoop.instance().start()
