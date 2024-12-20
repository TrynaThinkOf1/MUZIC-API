import requests

url = "http://127.0.0.1:6969/song/post"
admin_key = "e5011778269baedc706ef559fd13f2443c8b78ffa7f816d5288d975e185f780d"
file_path = "../_bell1.mp3"

with open(file_path, "rb") as f:
    files = {"file": f}
    data = {
        "key": admin_key,
        "gov_name": "_bell1-iMovie Audio Effects Library"
    }
    response = requests.post(url, files=files, data=data)
    print(response.json())
