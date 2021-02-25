from twitchAPI.twitch import Twitch
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import json
import urllib.request as dl
import sys
from os.path import isfile
from os import remove
from datetime import datetime, timedelta, datetime


gauth = GoogleAuth()
gauth.LoadCredentialsFile("credentials.txt")

drive = GoogleDrive(gauth)

file_list = drive.ListFile({'q': "'root' in parents"}).GetList()
for file1 in file_list:
    if file1['title'] == "Clipsmitten Repository":
        id1 = file1['id']
    if file1['title'] == "Clips Staging Area":
        parent_id = file1['id']

to_search = drive.ListFile({'q': f"'{id1}' in parents"}).GetList()
to_search += drive.ListFile({'q': f"'{parent_id}' in parents"}).GetList()
files = []

while to_search:
    item = to_search.pop()
    if item["mimeType"] == "application/vnd.google-apps.folder":
        id1 = item['id']
        to_search += drive.ListFile({'q': f"'{id1}' in parents"}).GetList()
    else:
        files.append(item['title'])
        print("Total files found on Google Drive: " + str(len(files)), end='\r')

print("Total files found on Google Drive: " + str(len(files)))


with open("apis.json") as apis_file:
    apis = json.load(apis_file)


game_ids = {}


def get_urls(start, end, pagination=None):
    clips_list = []
    global game_ids
    global apis

    t_id = apis["t_id"]
    t_t = apis["t_t"]

    twitch = Twitch(t_id, t_t)
    twitch.authenticate_app([])

    clips = twitch.get_clips(broadcaster_id="61852275", first=100,
                             after=pagination, started_at=start,
                             ended_at=end)
    for clip in clips["data"]:
        thumb_url = clip["thumbnail_url"]
        clip_url = thumb_url.split("-preview", 1)[0] + ".mp4"
        game_id = clip["game_id"]
        game = game_ids.get(game_id, None)
        if not game:
            game = twitch.get_games(game_ids=game_id)
            try:
                game = game["data"][0]["name"]
            except IndexError:
                game = "NOGAME"
            game = " ".join(game.split("/"))
            game_ids[game_id] = game
        c_title = " ".join(clip["title"].split("/"))
        title = clip["created_at"] + " _ " + game + " _ " + c_title
        title += " _ " + clip["creator_name"] + " _ " + clip["id"]
        clips_list.append([title, clip_url])

    cursor = clips["pagination"].get("cursor", "DONE")

    return clips_list, cursor

def dl_progress(count, block_size, total_size):
    percent = int(count * block_size * 100 / total_size)
    sys.stdout.write("\r...%d%%" % percent)
    sys.stdout.flush()

start = datetime(2021, 1, 11)

while True:
    now = datetime.now()
    if start.year == now.year and start.month == now.month + 1:
        break
    all_urls = []
    pagination = None
    total = 0
    datestring = now.strftime("%a, %Y/%B/%d")

    while pagination != "DONE":
        last_pagination = pagination
        new_urls, pagination = get_urls(pagination=pagination,
                                        start=start,
                                        end=start + timedelta(days=1))
        all_urls += new_urls
        print(f"Clips created on {datestring}: " + str(len(all_urls)), end='\r')

    print(f"Clips created on {datestring}: " + str(len(all_urls)))

    for url in all_urls:
        total += 1
        dl_url = url[1]
        base_path = "/home/fitti/projects/clipper/smitten/"
        file_name = url[0]
        if file_name in files:
            continue
        try:
            print(str(total) + "\t" + base_path + file_name)
            dl.urlretrieve(dl_url, base_path + file_name,
                           reporthook=dl_progress)
            upload = drive.CreateFile({'title': file_name ,'parents': [{'id': parent_id}]})
            upload.SetContentFile(base_path + file_name)
            upload.Upload()
            print()
            remove(base_path + file_name)
        except Exception as e:
            print(e)
            with open("failed.txt", "a") as failed_file:
                failed_file.write(url[0] + " - " + url[1])
            print("FAILED!")
            raise e

    start += timedelta(days=1)
