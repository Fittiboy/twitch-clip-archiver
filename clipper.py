from twitchAPI.twitch import Twitch
import json
import urllib.request as dl
import sys
from os.path import isfile
from datetime import datetime, timedelta


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

start = datetime(2021, 2, 1)

while True:
    if start.year == 2021 and start.month == 3:
        break
    all_urls = []
    pagination = None
    failed = []
    total = 0

    while pagination != "DONE":
        last_pagination = pagination
        new_urls, pagination = get_urls(pagination=pagination,
                                        start=start,
                                        end=start + timedelta(days=3))
        all_urls += new_urls
        print(len(all_urls))

    for url in all_urls:
        total += 1
        print("\n\n", url[0], url[1])
        dl_url = url[1]
        base_path = "/home/fitti/projects/clipper/smitten/"
        file_name = url[0]
        if isfile(base_path + file_name):
            continue
        print(str(total) + "\t" + base_path + file_name)
        try:
            dl.urlretrieve(dl_url, base_path + file_name,
                           reporthook=dl_progress)
        except Exception as e:
            failed.append(url)
            print(e)
            print("Failed")

    start += timedelta(days=3)
