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

WAV_HEADER = b'RIFF$\xe2\x04\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>' \
             b'\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\x00\xe2\x04\x00'

jinja = jinja2.Environment(
    loader=jinja2.FileSystemLoader(searchpath="./templates")
)
app = Sanic()

CONFIG = Config()

log = logging.getLogger("audiosocket")


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

    async def buffer(self, data):
        if self.count == 0:
            self.payload = WAV_HEADER + data
            self.count += 1
        elif self.count == 9:
            self.payload += data
            await self.broadcast(self.payload)
            self.count = 0
            self.payload = None
        else:
            self.payload += data
            self.count += 1

    async def broadcast(self, payload):
        # print "Sending {} bytes".format(str(len(payload)))
        for conn in self.clients:
            await conn.send(payload)

    async def broadcast_event(self, event):
        for conn in self.eventclients:
            msg = json.dumps(event).encode("utf-8")
            await conn.send(msg)

    def process_event(self, event):
        if event['direction'] == "outbound" and event['status'] == "answered":
            self.vapi_call_uuid = event['uuid']
        return True

    def check_clients(self):
        if len(self.clients) == 1 and not self.vapi_connected:
            self.connect_vapi()
        elif len(self.clients) == 0 and self.vapi_connected:
            self.disconnect_vapi()
        else:
            return True

    def connect_vapi(self):
        log.info("Instructing VAPI to connect")
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
    state.process_event(event)
    await state.broadcast_event(event)
    return response.raw(b'', status=204)


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
    connections.add(websocket)
    await websocket.send(b'00000000')
    try:
        while True:
            message = await websocket.recv()
            if type(message) == bytes:
                await websocket.send(message)
                await state.buffer(message)
            else:
                await websocket.send('ok')
    finally:
        connections.remove(websocket)


@app.websocket("/browser")
async def client_ws_handler(request, websocket):
    state.clients.append(websocket)
    state.check_clients()
    try:
        while True:
            await websocket.recv()
    finally:
        state.clients.remove(websocket)
        state.check_clients()


@app.websocket("/browserevent")
async def browser_event_ws_handler(request, websocket):
    state.eventclients.append(websocket)
    try:
        while True:
            await websocket.recv()
    finally:
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

    if CONFIG.fully_configured:
        client = nexmo.Client(
            key=CONFIG.api_key,
            secret=CONFIG.api_secret,
            application_id=CONFIG.app_id,
            private_key=open(CONFIG.private_key).read(),
        )

    # The Server Config
    static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               'static/')
    app.static('/s', static_path)
    app.run(port=CONFIG.port)


# Running It
if __name__ == "__main__":
    main()
