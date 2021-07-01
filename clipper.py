from twitchAPI.twitch import Twitch
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import re
import json
import urllib.request as dl
import sys
from os.path import isfile, isdir, realpath, basename
from os.path import join as pjoin
from os import remove, makedirs, listdir
from datetime import datetime, timedelta
from argparse import ArgumentParser


def get_gdrive_files(credentials, clips, staging):
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile(credentials)
    drive = GoogleDrive(gauth)

    file_list = drive.ListFile({'q': "'root' in parents"}).GetList()
    for file1 in file_list:
        if file1['title'] == clips:
            clips_repo = file1['id']
        if file1['title'] == staging:
            staging_folder = file1['id']

    to_search = drive.ListFile({'q': f"'{staging_folder}' in parents"})
    to_search = to_search.GetList()
    if clips:
        to_add = drive.ListFile({'q': f"'{clips_repo}' in parents"}).GetList()
        to_search += to_add
    files = []

    while to_search:
        item = to_search.pop()
        if item["mimeType"] == "application/vnd.google-apps.folder":
            id1 = item['id']
            to_search += drive.ListFile({'q': f"'{id1}' in parents"}).GetList()
        else:
            clip_title = item['title']
            clip_id = clip_title.split(" _ ")[-1]
            files.append(clip_id)
            print("Total files found on Google Drive: " + str(len(files)),
                  end="\r")

    print("Total files found on Google Drive: " + str(len(files)))
    return files, staging_folder, drive


def get_urls(twitch, start, end, b_id, pagination=None,
             clippers=None, categories=None, regex=None,
             flags=[]):

    clips_list = []
    clippers = [clipper.lower() for clipper in clippers] if clippers else None
    categories = [
        category.lower() for category in categories
        ] if categories else None
    global game_ids

    clips = twitch.get_clips(broadcaster_id=b_id, first=100,
                             after=pagination, started_at=start,
                             ended_at=end)
    for clip in clips["data"]:
        thumb_url = clip["thumbnail_url"]
        clip_url = thumb_url.split("-preview", 1)[0] + ".mp4"
        game_id = clip["game_id"]
        creator = clip["creator_name"]
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
        title += " _ " + creator + " _ " + clip["id"]
        if (
                (clippers and creator.lower() not in clippers) or
                (categories and game.lower() not in categories) or
                (regex and not re.search(regex, c_title, *flags))
           ):
            pass
        else:
            clips_list.append([title, clip_url])

    cursor = clips["pagination"].get("cursor", "DONE")

    return clips_list, cursor


def dl_progress(count, block_size, total_size):
    percent = int(count * block_size * 100 / total_size)
    sys.stdout.write(f"\rDownloading: {percent}%")
    sys.stdout.flush()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("streamers",
                        help="names of the streamers to pull clips from",
                        nargs="+",
                        type=str)
    parser.add_argument("--start_date",
                        help="first day to start looking "
                        "for clips (default: day the streamer's account was "
                        "created)",
                        metavar="YYYY/MM/DD",
                        type=str)
    parser.add_argument("--end_date",
                        help="last day to look for clips"
                        " (default: current day)",
                        metavar="YYYY/MM/DD",
                        type=str)
    parser.add_argument("--clips_dir",
                        help="directory to check for already"
                        " uploaded clips in Google Drive (must be in root)",
                        metavar="directory",
                        type=str)
    parser.add_argument("--staging_dir",
                        help="staging directory to upload new "
                        "clips to in Google Drive (must be in root, included"
                        " in search for already uploaded clips)",
                        metavar="directory",
                        type=str)
    parser.add_argument("--local",
                        help="store clips locally (only necessary "
                        "if credentials.txt for Google Drive is present)",
                        action="store_true")
    parser.add_argument("--clippers",
                        help="only download clips made by these accounts",
                        metavar="usernames",
                        nargs="*",
                        type=str)
    parser.add_argument("--categories",
                        help="only download clips from these categorys/games "
                        "(some non-game categories like Just Chatting "
                        "don't get reported by the API, type \"NOGAME\" "
                        "for these if you notice they're missing)",
                        metavar="games",
                        nargs="*",
                        type=str)
    parser.add_argument("--regex",
                        help="only download clips matching the regular "
                        "expression given "
                        "(see https://docs.python.org/3/library/re.html)",
                        metavar="search term",
                        type=str)
    parser.add_argument("-c", "--case_insensitive",
                        help="if regex is provided, setting this flag will "
                        "make the regular expression case-insensitive.",
                        action="store_true")
    args = parser.parse_args()

    filepath = realpath(__file__)
    filename = basename(filepath)
    filedir = filepath[:-len(filename)]

    gdrive_credentials = pjoin(filedir, "credentials.txt")

    if isfile(gdrive_credentials) and not args.local:
        try:
            files, staging_folder, drive = get_gdrive_files(gdrive_credentials,
                                                            args.clips_dir,
                                                            args.staging_dir)
        except UnboundLocalError:
            raise Exception("Staging directory not specified! Please set " +
                            "--staging_dir")
        gdrive = True
    elif args.local:
        print("Storing files locally.\n")
        gdrive = False
    else:
        print("No Google Drive credentials.txt found. Storing files locally.")
        print()
        gdrive = False
    if gdrive and not args.staging_dir:
        parser.error("No --staging_dir directory specified")

    try:
        apis = pjoin(filedir, "apis.json")
        with open(apis) as apis_file:
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

    failed = 0
    game_ids = {}
    b_ids = {}
    start = None

    twitch = Twitch(t_id, t_t)
    twitch.authenticate_app([])
    for streamer in args.streamers:
        try:
            _streamer = twitch.get_users(logins=streamer)["data"][0]
            year, month, day = _streamer["created_at"].split("-")
            day = day.split("T")[0]
            new_start = datetime(*map(int, [year, month, day]))
            if not start or new_start < start:
                start = new_start
        except IndexError:
            raise Exception("Streamer not found: " + streamer)
        b_ids[streamer] = _streamer["id"]

    if args.start_date:
        try:
            year, month, day = [int(num) for num in args.start_date.split("/")]
            start = datetime(year, month, day)
        except Exception:
            raise Exception("Please provice a correct start date in the " +
                            "format YYYY/MM/DD")

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

        for streamer, b_id in b_ids.items():
            print(f"\n\tStreamer: {streamer}\n")
            total = 0
            pagination = None
            all_urls = []
            datestring = start.strftime("%a, %Y/%B/%d")

            while pagination != "DONE":
                last_pagination = pagination
                new_urls, pagination = get_urls(twitch=twitch,
                                                start=start,
                                                end=start + timedelta(days=1),
                                                b_id=b_id,
                                                pagination=pagination,
                                                clippers=args.clippers,
                                                categories=args.categories,
                                                regex=args.regex,
                                                flags=[re.I] if
                                                args.case_insensitive else [])
                all_urls += new_urls
                print(f"Clips created on {datestring}: " + str(len(all_urls)),
                      end="\r")

            print(f"Clips created on {datestring}: " + str(len(all_urls)))
            base_path = pjoin(filedir, "clips", streamer)
            if not isdir(base_path):
                makedirs(base_path, exist_ok=True)
            exist_clips = listdir(base_path)
            exist_ids = [filename.split(" _ ")[-1] for filename in exist_clips]

            for url in all_urls:
                total += 1
                dl_url = url[1]
                file_name = url[0] + ".mp4"
                clip_id = file_name.split(" _ ")[-1]
                if sys.platform.startswith("win"):
                    file_name = file_name.strip().replace(" ", "_")
                    file_name = re.sub(r'(?u)[^-\w.]', "", file_name)
                fullpath = pjoin(base_path, file_name)
                if gdrive and clip_id in files:
                    continue
                elif clip_id in exist_ids and not gdrive:
                    continue
                try:
                    print(str(total) + "/" + str(len(all_urls)) + "\t" +
                          fullpath)
                    dl.urlretrieve(dl_url, fullpath,
                                   reporthook=dl_progress)
                    if gdrive:
                        upload = drive.CreateFile({'title': file_name,
                                                  'parents': [{
                                                          'id': staging_folder
                                                          }]})
                        upload.SetContentFile(fullpath)
                        upload.Upload()
                        remove(fullpath)
                    print()
                except KeyboardInterrupt as e:
                    remove(fullpath)
                    raise e
                except Exception as e:
                    failed += 1
                    print(e)
                    if not isfile(base_path + "failed.txt"):
                        with open("failed.txt", "w"):
                            pass
                    with open("failed.txt", "a") as failed_file:
                        failed_file.write(url[0] + " - " + url[1])
                    print(file_name + ": FAILED!")

        start += timedelta(days=1)

    if failed:
        print(f"\n{str(failed)} clips not downloaded!"
              " Check failed.txt and try downloading them manually.")
