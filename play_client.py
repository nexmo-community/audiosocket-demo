#!/usr/bin/env python3

import tornado.websocket
from tornado import gen 
import sounddevice as sd
import soundfile as sf
import io


@gen.coroutine
def test_ws():
	count = 0
	client = yield tornado.websocket.websocket_connect("ws://audiosocket.sammachin.com:8000/browser")
	while True:
		message = yield client.read_message()
		data = io.BytesIO(message)
		
		
		
if __name__ == "__main__":
    tornado.ioloop.IOLoop.instance().run_sync(test_ws)
	
	