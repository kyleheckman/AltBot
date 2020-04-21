import os
import json

from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask import Flask, request

app = Flask(__name__)

@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()
    parsed_msg = parse_message(data)

    # Prevent replying to itself
    if data['name'] != 'Chatbot':
        #if (parsed_msg != 'NOT_HTTP_MSG_ERROR')
        msg = 'Protocol: {}\nHost: {}\nPath: {}\n'.format(parsed_msg[0], parsed_msg[1], parsed_msg[2])
        send_message(msg)

    return "OK", 200

def send_message(msg):
    url = 'https://api.groupme.com/v3/bots/post'

    data = {
        'bot_id' : os.getenv('GROUPME_BOT_ID'),
        'text' : msg,
    }

    request = Request(url, urlencode(data).encode())
    #json = 
    urlopen(request).read.decode()

def parse_message(data):
    # Get text from JSON data
    text = data['text']

    # Check if the msg is an HTTP URL
    protocol = text[:8]
    if (protocol != 'https://'):
        return ('NOT_HTTP_MSG_ERROR',0,0)
    
    # Retrieve other URI information
    host = text[8:24]
    path = text[25:]

    return (protocol, host, path)