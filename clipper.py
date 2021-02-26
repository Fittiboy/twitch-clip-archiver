from twitchAPI.twitch import Twitch
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import json
import urllib.request as dl
import sys
from os.path import isfile, isdir, realpath
from os import remove, makedirs
from datetime import datetime, timedelta
from argparse import ArgumentParser


def get_gdrive_files(credentials):
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile(credentials)
    drive = GoogleDrive(gauth)

    file_list = drive.ListFile({'q': "'root' in parents"}).GetList()
    for file1 in file_list:
        # Folder names currently hardcoded! Change them here
        if file1['title'] == "Clipsmitten Repository":
            id1 = file1['id']
        # and here!
        if file1['title'] == "Clips Staging Area":
            parent_id = file1['id']

    to_search = drive.ListFile({'q': f"'{parent_id}' in parents"}).GetList()
    to_search += drive.ListFile({'q': f"'{id1}' in parents"}).GetList()
    files = []

    while to_search:
        item = to_search.pop()
        if item["mimeType"] == "application/vnd.google-apps.folder":
            id1 = item['id']
            to_search += drive.ListFile({'q': f"'{id1}' in parents"}).GetList()
        else:
            files.append(item['title'])
            print("\rTotal files found on Google Drive: " + str(len(files)))

    return files


def get_urls(twitch, start, end, b_id, pagination=None):
    clips_list = []
    global game_ids

    clips = twitch.get_clips(broadcaster_id=b_id, first=100,
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
    sys.stdout.write(f"\rDownloading: {percent}%")
    sys.stdout.flush()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("streamer", help="name of the streamer to pull clips from",
                        type=str)
    parser.add_argument("--start_date", help="First day to start looking " +
                        "for clips (default: day the streamer's account was "+
                        "created)",
                        metavar="YYYY/MM/DD",
                        type=str)
    parser.add_argument("--end_date", help="Last day to look for clips." +
                        " (default: current day)",
                        metavar="YYYY/MM/DD",
                        type=str)
    parser.add_argument("--local", help="Store clips locally (only necessary "+
                        "if credentials.txt for Google Drive is present)",
                        action="store_true")
    args = parser.parse_args()

    filepath = realpath(__file__)
    filedir = "/".join(filepath.split("/")[:-1]) + "/"

    gdrive_credentials = filedir + "credentials.txt"

    if isfile(gdrive_credentials) and not args.local:
        files = get_gdrive_files(gdrive_credentials)
        gdrive = True
    elif args.local:
        print("Storing files locally.\n")
        gdrive = False
    else:
        print("No Google Drive credentials.txt found. Storing files locally.\n")
        gdrive = False

    try:
        with open("apis.json") as apis_file:
            apis = json.load(apis_file)
            t_id = apis["t_id"]
            t_t = apis["t_t"]
    except FileNotFoundError:
        e_msg = """\t\tNo apis.json found. Please create a file with that name
        and the following template:

        {
            "t_id": "Your Twitch Client ID here",
            "t_t": "Your Twitch Client Secret here"
        }

        Include the quotation marks and curly brackets!"""
        raise FileNotFoundError(e_msg)

    game_ids = {}

    twitch = Twitch(t_id, t_t)
    twitch.authenticate_app([])
    try:
        streamer = twitch.get_users(logins=args.streamer)["data"][0]
    except IndexError:
        raise Exception("Streamer not found!")
    b_id = streamer["id"]

    if args.start_date:
        try:
            year, month, day = [int(num) for num in args.start_date.split("/")]
        except Exception:
            raise Exception("Please provice a correct start date in the " +
                            "format YYYY/MM/DD")
    else:
        year, month, day = streamer["created_at"].split("-")
        day = day.split("T")[0]
        year, month, day = [int(num) for num in [year, month, day]]
    start = datetime(year, month, day)

    if args.end_date:
        try:
            year, month, day = [int(num) for num in args.end_date.split("/")]
        except Exception:
            raise Exception("Please provice a correct end date in the " +
                            "format YYYY/MM/DD")
        end = datetime(year, month, day)
    else:
        end = datetime.now()

    null_date = datetime(1970, 1, 1)
    end_sec = (end - null_date).total_seconds()

    while True:
        start_sec = (start - null_date).total_seconds()
        if start_sec > end_sec:
            print("\nAll clips checked!")
            print("Note that sometimes, the Twitch API seems to miss " +
                  "clips. Consider re-running the program with the " +
                  "same settings.")
            break

        all_urls = []
        pagination = None
        total = 0
        datestring = start.strftime("%a, %Y/%B/%d")

        while pagination != "DONE":
            last_pagination = pagination
            new_urls, pagination = get_urls(twitch=twitch,
                                            start=start,
                                            end=start + timedelta(days=1),
                                            b_id=b_id,
                                            pagination=pagination)
            all_urls += new_urls
            print(f"\rClips created on {datestring}: " + str(len(all_urls)))

        for url in all_urls:
            total += 1
            dl_url = url[1]
            base_path = filedir + f"clips/{args.streamer}/"
            if not isdir(base_path):
                makedirs(base_path, exist_ok=True)
            file_name = url[0]
            if gdrive and file_name in files:
                continue
            elif isfile(base_path + file_name):
                continue
            try:
                print(str(total) + "\t" + base_path + file_name)
                dl.urlretrieve(dl_url, base_path + file_name,
                               reporthook=dl_progress)
                if gdrive:
                    upload = drive.CreateFile({'title': file_name ,'parents': [{'id': parent_id}]})
                    upload.SetContentFile(base_path + file_name)
                    upload.Upload()
                    remove(base_path + file_name)
                print()
            except Exception as e:
                print(e)
                if not isfile(base_path + "failed.txt"):
                    with open("failed.txt", "w"):
                        pass
                with open("failed.txt", "a") as failed_file:
                    failed_file.write(url[0] + " - " + url[1])
                print(file_name + ": FAILED!")

        start += timedelta(days=1)
