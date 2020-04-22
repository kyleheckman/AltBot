import os
import json
import six
import requests
from base64 import b64encode
from flask import Flask, request

app = Flask(__name__)


#
# Routes for Flask
#

# Default route
# Receives requests from GroupMe bot whenever a user submits a message
@app.route('/', methods=['POST'])
def webhook():
    # Retrieve JSON data from submitted massage, decompose into protocol, host, path
    data = request.get_json()
    protocol, host, path = parse_message(data)

    # Extract Spotify URI of the song if applicable
    if (host != 0 and path != 0):
        song_id = extract_song_id(path)
    else:
        song_id = 0

    # Prevent bot replying to itself
    if data['name'] != 'Chatbot':
        # Run this routine if a song was submitted
        if (protocol != 'NOT_HTTP_ERROR'):
            track_list = []
            status_code = get_playlist_items(track_list)
            if (status_code != 200):
                if (status_code == 401):
                    res = get_authorization()
                    if (res == 1):
                        get_playlist_items(track_list)
                    else:
                        send_message('Authentication Given... Resend Link')
                        return 'OK', 200
                else:
                    return 'Bad Request', 400

            status_code = add_song(song_id)
            if (status_code != 200):
                if (status_code == 401):
                    res = get_authorization()
                    if (res == 1):
                        add_song(song_id)
                    else:
                        send_message('Authentication Given... Resend Link')
                        return 'OK', 200
                else:
                    return 'Bad Request', 400

    # Return with HTTP status code 200
    return 'OK', 200


# Authentication route for Spotify Web API token handling
# Is the redirect URI for the Spotify Application Client
# Only called during initial authentication, subsequent accesses are handled by refresh tokens
@app.route('/authenticate', methods=['GET'])
def authentication():
    auth_code = request.args['code']

    # Spotify Web API endpoint for requesting OAuth tokens
    url = 'https://accounts.spotify.com/api/token'

    # HTTP request payload for requesting access and refresh tokens
    data = {
        'grant_type' : 'authorization_code',
        'code' : auth_code,
        'redirect_uri' : os.getenv('REDIRECT_URI')
    }

    # Authentication header for HTTP request, contains base64 encoded Client ID and Client Secret
    # for the Spotify Application Client
    auth_hdr = os.getenv('APP_CLIENT_ID') + ':' + os.getenv('APP_CLIENT_SECRET')
    auth_hdr = b64encode(six.text_type(auth_hdr).encode('ascii'))
    headers = {
        'Authorization' : 'Basic {}'.format(auth_hdr.decode('ascii'))
    }

    # Send the HTTP request, store the result in response
    response = requests.post(url, data=data, headers=headers)
    
    print("JSON: {}".format(response.json()))
    print("RAW: {}".format(response))
    # Set environment variables for auth tokens
    os.environ['OAUTH_TOKEN'] = response.json()['access_token']
    os.environ['REFRESH_TOKEN'] = response.json()['refresh_token']

    return "OK", 200


#
# Support Functions
#

# Sends a message from the GroupMe bot to the group chat
def send_message(msg):
    # GroupMe bot API endpoint for sending messages through a bot
    url = 'https://api.groupme.com/v3/bots/post'

    # HTTP request payload for sending messages
    data = {
        'bot_id' : os.getenv('GROUPME_BOT_ID'),
        'text' : msg,
    }

    # Send the HTTP request, store the result in response
    response = requests.post(url, data=data)

    # Return with the response HTTP status code
    return response.status_code
    

# Adds a song submitted in GroupMe to the desired playlist
def add_song(song_id):
    # Spotify Web API endpoint for playlist tracks
    url = 'https://api.spotify.com/v1/playlists/{}/tracks?uris=spotify%3Atrack%3A{}'.format(os.getenv('PLAYLIST_ID'), song_id)

    # HTTP request headers, includes OAuth token for authentication
    headers = {
        'Accept' : 'application/json',
        'Content-Type' : 'application/json',
        'Authorization' : 'Bearer {}'.format(os.getenv('OAUTH_TOKEN'))
    }

    # Send the HTTP request, store the result in response
    response = requests.post(url, headers=headers)
    
    # Return with the response HTTP status code
    return response.status_code


# Retrieves a list of tracks in a playlist
def get_playlist_items(track_list):
    # Spotify Web API endpoint for tracks in a playlist
    url = 'https://api.spotify.com/v1/playlists/{}/tracks'.format(os.getenv('PLAYLIST_ID'))

    # HTTP request headers, includes OAuth token for authentication
    headers = {
        'Accept' : 'application/json',
        'Content-Type' : 'application/json',
        'Auhtorization' : 'Bearer {}'.format(os.getenv('OAUTH_TOKEN'))
    }

    # Send the HTTP request, store the result in response
    response = requests.get(url, headers=headers)
    print('PLAYLIST: {}'.format(response.json()))
    
    # Return with the reponse HTTP status code
    return response.status_code


# Generate link to authorize this app to access user Spotify account information
def get_authorization():
    # Sporify endpoint for this app to request access to user account info
    url = 'https://accounts.spotify.com/api/token'

    # HTTP request payload to request a refreshed OAuth token
    data = {
        'grant_type' : 'refresh_token',
        'refresh_token' : os.getenv('REFRESH_TOKEN')
    }

    # Authentication header for HTTP request, contains base64 encoded Client ID and Client Secret
    # for the Spotify Application Client
    auth_hdr = os.getenv('APP_CLIENT_ID') + ':' + os.getenv('APP_CLIENT_SECRET')
    auth_hdr = b64encode(six.text_type(auth_hdr).encode('ascii'))
    headers = {
        'Authorization' : 'Basic {}'.format(auth_hdr.decode('ascii'))
    }

    # Send the HTTP request, store the result in response
    response = requests.post(url, data=data, headers=headers)
    
    if (response.status_code == 200):
        os.environ['OAUTH_TOKEN'] = response.json()['access_token']
        return 1
    else:
        # Spotify Account endpoint to for this app to request access to user account info
        url = 'https://accounts.spotify.com/authorize?client_id={}&response_type=code&redirect_uri={}&scope=playlist-modify-public%20playlist-modify-private'.format(os.getenv('APP_CLIENT_ID'), os.getenv('REDIRECT_URI'))

        # Sends the link to the GroupMe group chat
        send_message(url)
        return 2


# Parse the text body of receives messages
# If text is a properly formatted URL, decompose into protocol, host, path
# Else return with error message
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


# Parse the path of a Spotify song link to extract the Spotify URI for the song
def extract_song_id(path):
    delim_1 = 0
    delim_2 = 0
    for n in range(len(path)):
        if (path[n] == '/' and delim_1 == 0):
            delim_1 = n + 1
        if (path[n] == '?' and delim_2 == 0):
            delim_2 = n
    
    return path[delim_1:delim_2]