import os
import json

from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask import Flask, request

app = Flask(__name__)

@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()
    protocol, host, path = parse_message(data)
    if (len(path) > 0):
        song_id = extract_song_id(path)
    else:
        song_id = 0

    # Prevent bot replying to itself
    if data['name'] != 'Chatbot':
        if (protocol != 'NOT_HTTP_ERROR'):
            msg = 'Protocol: {}\nHost: {}\nPath: {}\nID: {}\n'.format(protocol, host, path, song_id)
            send_message(msg)
            add_song(song_id)

    return "OK", 200


def send_message(msg):
    url = 'https://api.groupme.com/v3/bots/post'

    data = {
        'bot_id' : os.getenv('GROUPME_BOT_ID'),
        'text' : msg,
    }

    request = Request(url, urlencode(data).encode())
    urlopen(request).read.decode()


def add_song(song_id):
    url = 'https://api.spotify.com/v1/playlists/{}/tracks'.format(os.getenv('PLAYLIST_ID'))

    headers = {
        'Accept' : 'application/json',
        'Content-Type' : 'application/json',
        'Authorization' : 'Bearer {}'.format(os.getenv('OAUTH_TOKEN'))
    }

    data = {
        'uris' : 'spotify:track:{}'.format(song_id)
    }

    request = Request(url, data=urlencode(data).encode(), headers=headers, method='POST')
    urlopen(request).read.decode()


def parse_message(data):
    # Get text from JSON data
    text = data['text']

    # Check if the msg is an HTTP URL
    protocol = text[:8]
    if (protocol != 'https://'):
        return ('NOT_HTTP_ERROR',0,0)
    
    # Retrieve other URI information
    host = text[8:24]
    path = text[25:]

    return (protocol, host, path)


def extract_song_id(path):
    delim_1 = 0
    delim_2 = 0
    for n in range(len(path)):
        if (path[n] == '/' and delim_1 == 0):
            delim_1 = n + 1
        if (path[n] == '?' and delim_2 == 0):
            delim_2 = n
    
    return path[delim_1:delim_2]