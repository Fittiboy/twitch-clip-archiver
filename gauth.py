from pydrive.auth import GoogleAuth


gauth = GoogleAuth()
gauth.LocalWebserverAuth()

gauth.SaveCredentialsFile("credentials.txt")
