import os
import json

#from urllib.error import HTTPError
#from urllib.parse import urlencode
#from urllib.request import Request, urlopen
import requests
from base64 import b64encode
from flask import Flask, request

app = Flask(__name__)

@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()
    protocol, host, path = parse_message(data)
    if (host != 0 and path != 0):
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


@app.route('/authenticate', methods=['GET'])
def authentication():
    auth_code = request.args['code']
    #os.environ['AUTH_CODE'] = str(auth_code)

    url = 'https://accounts.spotify.com/api/token'

    data = {
        'grant_type' : 'authorization_code',
        'code' : auth_code,
        'redirect_uri' : os.getenv('REDIRECT_URI')
    }

    auth_hdr = b64encode(os.getenv('APP_CLIENT_ID') + ':' + os.getenv('APP_CLIENT_SECRET'))
    headers = {
        'Authorization' : 'Basic {}'.format(auth_hdr)
    }

    response = requests.post(url, json=data, headers=headers)
    print("AUTH CODE: {}".format(auth_code))
    print('RES: {}'.format(response.json()))

    return "OK", 200


def send_message(msg):
    url = 'https://api.groupme.com/v3/bots/post'

    data = {
        'bot_id' : os.getenv('GROUPME_BOT_ID'),
        'text' : msg,
    }

    response = requests.post(url, data=data)
    

def add_song(song_id):
    url = 'https://api.spotify.com/v1/playlists/{}/tracks?uris=spotify%3Atrack%3A{}'.format(os.getenv('PLAYLIST_ID'), song_id)

    headers = {
        'Accept' : 'application/json',
        'Content-Type' : 'application/json',
        'Authorization' : 'Bearer {}'.format(os.getenv('OAUTH_TOKEN'))
    }

    response = requests.post(url, headers=headers)
    print('OAUTH: {}'.format(response.status_code))
    if response.status_code == 401:
        get_initial_auth()


def get_playlist_items():
    url = 'https://api.spotify.com/v1/playlists/{}/tracks'.format(os.getenv('PLAYLIST_ID'))

    headers = {
        'Accept' : 'application/json',
        'Content-Type' : 'application/json',
        'Auhtorization' : 'Bearer {}'.format(os.getenv('OAUTH_TOKEN'))
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 401:
        response = 0
    return response


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