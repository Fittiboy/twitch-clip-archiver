## How to use?
1. Clone repo
2. `pip install -r requirements.txt`
3. `python clipper.py --help`
## How to automatically upload to Google Drive?
1. Acquire `client_secrets.json` (Follow "Get Your API Key" from [this guide](https://medium.com/analytics-vidhya/how-to-connect-google-drive-to-python-using-pydrive-9681b2a14f20))
2. Place it in the same directory as clipper.py
3. Run `python gauth.py` and authorize the application in your browser
4. Create a staging area folder (this is where clips will be uploaded into) at the top level of your Google Drive
5. (optional) Create a sorted clip repository with however many subfolders you want (years, months, single streams, etc.) at the top level of your Google Drive
6. Specify these folders by name with the `--staging_dir` and `--clips_dir` options respectively
