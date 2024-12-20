import requests

url = "http://127.0.0.1:6969/key/create"
admin_key = "e5011778269baedc706ef559fd13f2443c8b78ffa7f816d5288d975e185f780d"
file_path = "../_bell1.mp3"

with open(file_path, "rb") as f:
    files = {"file": f}
    response = requests.post(url, headers={"Content-Type": "application/json"}, files=files, json={"key": admin_key, "gov_name": "_bell1-iMovie Audio Effects Library"})
    print(response.json())
