import nexmo
from creds import *

client = nexmo.Client(key=API_KEY, secret=API_SECRET, application_id=APP_ID, private_key=PRIVATE_KEY)

response = client.create_call({
  'to': [{'type': 'phone', 'number': '447970513607'}],
  'from': {'type': 'phone', 'number': '447970513607'},
  'answer_url': ['http://s3.sammachin.com/talk.json']
})