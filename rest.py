import nexmo

kf = open(PRIVATE_KEY_PATH, "r")
PRIVATE_KEY = kf.read()
kf.close()

client = nexmo.Client(key=API_KEY, secret=API_SECRET, application_id=APP_ID, private_key=PRIVATE_KEY)

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