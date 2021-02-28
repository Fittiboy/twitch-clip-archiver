## (Prologue: Using the utility in Windows)
*(The tool now works fine in Windows, though the filenames will be missing a lot of special characters!)*
The clip titles contain many special characters, which Windows is too scared to touch (? and : are scary, I get it!).  
This is totally fine though, since you can simply activate a feature called [Windows Subsystems for Linux](https://docs.microsoft.com/en-us/windows/wsl/),
which allows you to use the tool anyway,
by installing a Linux distribution *inside* of your Windows installation. (Shockingly, this is an official Windows feature).
1. Open your start menu and type "Turn Windows features on or off"
2. Click on the search result that matches this name
3. In this list, tick the box next to "Windows Subsystems for Linux"
4. Hit OK and reboot
5. Open the Microsoft Store from the start menu and install Ubuntu LTS 20.04
6. Launch Ubuntu, and wait for it to fully install
7. Create a username and password when prompted (it will look like nothing is happening when typing your password, thuogh this is intentional!)

Congratulations! You now have Linux running inside Windows!
Now simply [paste](https://devblogs.microsoft.com/commandline/copy-and-paste-arrives-for-linuxwsl-consoles/)
and run this chain of commands:  
`sudo apt update ; sudo apt upgrade ; sudo apt install python3 python3-pip git`  
(this should ask you for your password).
Now you can follow the instructions below.

## How to use?
1. Clone repo `git clone https://github.com/Fittiboy/twitch-clip-archiver`
2. Navigate into cloned directory `cd twitch-clip-archiver`
3. Installed required packages `pip install -r requirements.txt`
4. Create your `apis.json` file (see [next section](#how-to-acquire-a-client-id-and-secret))
5. Run the command with the --help flag for more info `python clipper.py --help`

## How to acquire a Client ID and secret?
1. Go to your [Twitch Developer Console](https://dev.twitch.tv/console/apps) (log in with your Twitch account)
2. Click "Register Your Application"
3. Make up some unique name (this is mostly irrelevant)
4. type "http://localhost" (remove the quotes) into the "OAuth Redirect URLs" field (no need to hit the "Add" button)
5. Select "Other" as Category and type "Clip archival tool" or something close to that into the "Other Details" field
6. Hit "Create"
7. Click on "Manage"
8. Click on "New Secret"
9. Copy the Client ID and the Client Secret and put them into a file called `apis.json` in the "twitch-clip-archiver" folder  

`apis.json` file template:
```json
{
    "t_id": "Client ID",
    "t_t": "Client Secret"
}
```
(keep all quotation marks, but replace the Client ID and Client Secret with your actual ID and Secret)

## How to automatically upload to Google Drive?
1. Acquire `client_secrets.json` (Follow "Get Your API Key" from [this guide](https://medium.com/analytics-vidhya/how-to-connect-google-drive-to-python-using-pydrive-9681b2a14f20))
2. Place it in the same directory as clipper.py (make sure it's called `client_secrets.json`)
3. Run `python gauth.py` and authorize the application in your browser (this will create `credentials.txt` and you will not have to authorize every time you run `python clipper.py`)
4. Create a staging area folder (this is where clips will be uploaded into) at the top level of your Google Drive
5. (optional) Create a sorted clip repository with however many subfolders you want (years, months, single streams, etc.) at the top level of your Google Drive
6. Specify these folders by name with the `--staging_dir` and `--clips_dir` options respectively when running `python clipper.py`
