from sys import argv
import json
import requests


with open("apis.json") as apis_file:
    client_id = json.load(apis_file)["t_id"]

headers = {"Client-ID": f"{client_id}", "Accept": "application/vnd.twitchtv.v5+json"}
url = f"https://api.twitch.tv/kraken/users?login=starsmitten"
r = requests.get(url, headers=headers).json()

for dict in r['users']:
    print(dict['display_name'] + " - " + dict['_id'])
