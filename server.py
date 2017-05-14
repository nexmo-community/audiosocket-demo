#!/usr/bin/env python

import json
import logging
import os.path

import nexmo
import phonenumbers

import jinja2
from sanic import Sanic
from sanic import response

from creds import Config

WAV_HEADER = 'RIFF$\xe2\x04\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>' \
             '\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\x00\xe2\x04\x00'

jinja = jinja2.Environment(
    loader=jinja2.FileSystemLoader(searchpath="./templates")
)
app = Sanic()

CONFIG = Config()


class State:
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
        logging.debug('buffering: %d', len(data))
        if self.count == 0:
            logging.debug('initial batch')
            self.payload = WAV_HEADER + data
            self.count += 1
        elif self.count == 9:
            logging.debug('broadcasting')
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
        logging.debug("Sending Event %s", event)
        for conn in self.eventclients:
            conn.write_message(event)

    def process_event(self, event):
        logging.debug("PROCESSING EVENT: %s", event)
        if event['direction'] == "outbound" and event['status'] == "answered":
            logging.debug("Setting call UUID to: %s", event['uuid'])
            self.vapi_call_uuid = event['uuid']
            logging.debug("VAPI CALL ID SET AS %s", self.vapi_call_uuid)
        return True

    def check_clients(self):
        logging.debug("Clients: %s, Connected: %s", self.clients, self.vapi_connected)
        if len(self.clients) == 1 and not self.vapi_connected:
            self.connect_vapi()
        elif len(self.clients) == 0 and self.vapi_connected:
            self.disconnect_vapi()
        else:
            return True

    def connect_vapi(self):
        logging.info("Instructing VAPI to connect")
        call_response = client.create_call({
            'to': [{
                "type": "websocket",
                "uri": "ws://{host}/socket".format(host=CONFIG.host),
                "content-type": "audio/l16;rate=16000",
                "headers": {
                    "app": "audiosocket"
                }
            }],
            'from': {'type': 'phone', 'number': CONFIG.phone_number},
            'answer_url': ['https://{host}/ncco'.format(host=CONFIG.host)]
        })
        logging.debug(repr(call_response))
        self.vapi_connected = True
        return True

    def disconnect_vapi(self):
        client.update_call(self.vapi_call_uuid, action='hangup')
        self.vapi_connected = False
        return True


state = State()


@app.route("/")
async def index_handler(request):
    if CONFIG.fully_configured:
        return response.html(jinja.get_template("index.html").render(
            phone_number=format_number(CONFIG.phone_number),
            host=CONFIG.host))
    else:
        return response.html(jinja.get_template("env_errors.html").render(
            missing_envs=CONFIG.missing_keys))


@app.route("/event", methods=["POST", ])
async def event_handler(request):
    event = request.json
    logging.debug("EVENT RECEIVED %s", json.dumps(event))
    state.process_event(event)
    state.broadcast_event(event)
    return response.raw('', status=204)


@app.route("/ncco")
async def ncco_handler(request):
    return response.json([
        {
            "action": "talk",
            "text": "Connecting to Audio Socket Conference",
        },
        {
            "action": "conversation",
            "name": "audiosocket",
            "eventUrl": ["https://{host}/event".format(host=CONFIG.host)],
        }
    ])


connections = set()


@app.websocket("/socket")
async def server_ws_handler(request, websocket):
    logging.debug("VAPI Client Connected")
    connections.add(websocket)
    await websocket.send('00000000', binary=True)
    try:
        while True:
            message = await websocket.recv()
            if type(message) == str:
                await websocket.send(message, binary=True)
                state.buffer(message)
            else:
                logging.debug(message)
                await websocket.send('ok')
    finally:
        logging.debug("VAPI Client Disconnected")
        connections.remove(websocket)


@app.websocket("/browser")
async def client_ws_handler(request, websocket):
    logging.debug("Browser Client Connected")
    state.clients.append(websocket)
    state.check_clients()
    try:
        while True:
            await websocket.recv()
            logging.debug("Browser Client Message Received")
    finally:
        logging.debug("Browser Client Disconnected")
        state.clients.remove(websocket)
        state.check_clients()


@app.websocket("/browserevent")
async def browser_event_ws_handler(request, websocket):
    logging.debug("Browser Client Connected")
    state.eventclients.append(websocket)
    try:
        while True:
            await websocket.recv()
            logging.debug("Browser Client Message Received")
    finally:
        logging.debug("Browser Client Disconnected")
        state.eventclients.remove(websocket)


def format_number(number):
    if not number.startswith("+"):
        number = "+" + number
    return phonenumbers.format_number(
        phonenumbers.parse(number, None),
        phonenumbers.PhoneNumberFormat.NATIONAL)


def main():
    global client

    logging.basicConfig(level=logging.INFO)
    logging.getLogger().setLevel(logging.DEBUG)

    client = nexmo.Client(
        key=CONFIG.api_key,
        secret=CONFIG.api_secret,
        application_id=CONFIG.app_id,
        private_key=CONFIG.private_key,
    )

    # The Server Config
    static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               'static/')
    app.static('/s', static_path)
    app.run(port=CONFIG.port)


# Running It
if __name__ == "__main__":
    main()
