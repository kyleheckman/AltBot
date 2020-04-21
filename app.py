import os
import json

from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask import Flask, request

app = Flask(__name__)

@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()
    protocol, host, path = parse_message(data)
    if (path != 0):
        song_id = extract_song_id(path)
    else:
        song_id = 0

    # Prevent bot replying to itself
    if data['name'] != 'Chatbot':
        if (protocol != 'NOT_HTTP_ERROR'):
            add_song(song_id)
            response = get_playlist_items()
            msg = 'RESPONSE:\n{}\n'.format(response)
            send_message(msg)

    return "OK", 200


def send_message(msg):
    url = 'https://api.groupme.com/v3/bots/post'

    data = {
        'bot_id' : os.getenv('GROUPME_BOT_ID'),
        'text' : msg,
    }

    request = Request(url, urlencode(data).encode())
    urlopen(request)
    

def add_song(song_id):
    url = 'https://api.spotify.com/v1/playlists/{}/tracks?uris=spotify%3Atrack%3A{}'.format(os.getenv('PLAYLIST_ID'), song_id)

    headers = {
        'Accept' : 'application/json',
        'Content-Type' : 'application/json',
        'Authorization' : 'Bearer {}'.format(os.getenv('OAUTH_TOKEN'))
    }

    request = Request(url, headers=headers, method='POST')
    try:
        urlopen(request)
    except HTTPError as err:
        if err.code == 401:
            get_initial_auth()


def get_playlist_items():
    url = 'https://api.spotify.com/v1/playlists/{}/tracks'.format(os.getenv('PLAYLIST_ID'))

    headers = {
        'Accept' : 'application/json',
        'Content-Type' : 'application/json',
        'Auhtorization' : 'Bearer {}'.format(os.getenv('OAUTH_TOKEN'))
    }

    request = Request(url, headers=headers, method='GET')
    return urlopen(request).read()


def get_initial_auth():
    url = 'https://accounts.spotify.com/authorize?client_id={}&response_type=code&redirect_uri={}&scope=playlist-modify-public%20playlist-modify-private'.format(os.getenv('APP_CLIENT_ID'), os.getenv('REDIRECT_URI'))

    #data = {
    #    'client_id' : os.getenv('APP_CLIENT_ID'),
    #    'response_type' : 'code',
    #    'redirect_uri' : os.getenv('REDIRECT_URI'),
    #    'scope' : 'playlist-modify-public playlist-modify-private'
    #}

    send_message(url)

    #request = Request(url, method='GET')
    #response = urlopen(request)
    #print(response)


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