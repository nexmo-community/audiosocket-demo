#! /usr/bin/env python

import sounddevice as sd
from ws4py.client.threadedclient import WebSocketClient
from struct import *
from scipy.io import wavfile
from utility import pcm2float

class DummyClient(WebSocketClient):
    def opened(self):
		print "Connected"
    def received_message(self, m):
		normalized = pcm2float(m, 'float32')	
		sd.play(normalized, 16000)
		
		
       
if __name__ == '__main__':
    try:
        ws = DummyClient('ws://audiosocket.sammachin.com:8000/browser', protocols=['http-only', 'chat'])
        ws.connect()
        ws.run_forever()
    except KeyboardInterrupt:
        ws.close()