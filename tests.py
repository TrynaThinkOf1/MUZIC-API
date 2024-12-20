import requests

url = "http://127.0.0.1:6969"

def post_key():
    print(requests.post(f"{url}/key").content.decode('utf-8'))

def post_song():
