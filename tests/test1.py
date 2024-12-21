import requests

url = "http://45.79.216.238:6969/song/post"
admin_key = "f7272cbd210ff6c64ec8cd9699c39510757a9a14e0c5a095affe58063e91ac31"
file_path = "./songs/fear.mp3"

def upload():
    with open(file_path, "rb") as f:
        files = {"file": f}
        data = {
            "key": admin_key,
            "gov_name": "FEAR.-Kendrick Lamar"
        }
        response = requests.post(url, files=files, data=data)
        print(response.json())
def download():
    response = requests.get(f"{url}/get", json={"key": admin_key, "song_id": 2})
    print(response.json())

upload()