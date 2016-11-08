#!/usr/bin/python

import tornado.websocket
from tornado import gen 

#header = 'RIFF\x88\xd55\x00WAVEfmt \x10\x00\x00\x00\x03\x00\x01\x00D\xac\x00\x00\x10\xb1\x02\x00\x04\x00 \x00fact\x04\x00\x00\x00Pu\r\x00PEAK\x10\x00\x00\x00\x01\x00\x00\x00\xfe\xd2\x1dX\xa8\xe7i?\xd8C\x01\x00data@\xd55\x00'
header = ''
@gen.coroutine
def test_ws():
	f = open("sound.wav", "wb")
	f.write(header)
	count = 500
	client = yield tornado.websocket.websocket_connect("ws://audiosocket.sammachin.com:8000/browser")
	while (count > 0):
		msg = yield client.read_message()
		print count
		f.write(msg)
		count -= 1
	f.close()
		

if __name__ == "__main__":
    tornado.ioloop.IOLoop.instance().run_sync(test_ws)