import requests
import os


class TwitchActions:
    def __init__(self):
        self.client_id = os.environ["CLIENT_ID"]
        self.client_secret = os.environ["CLIENT_SECRET"]
        self.token = None

    def refresh_token(self):
        url = "https://id.twitch.tv/oauth2/token"
        query = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
        }
        result = requests.post(url, params=query)
        self.token = result.json()["access_token"]

    def is_live(self, users):
        if not users:
            return
        url = f"https://api.twitch.tv/helix/streams?user_login={users[0]}"
        for user in users[1:]:
            url += f"&user_login={user}"
        header = {"client-id": self.client_id, "Authorization": f"Bearer {self.token}"}
        result = requests.get(url, headers=header)
        if result.status_code == 401:
            self.refresh_token()
            header = {
                "client-id": self.client_id,
                "Authorization": f"Bearer {self.token}",
            }
            result = requests.get(url, headers=header)

        if result.status_code == 401:
            return None

        data = result.json()["data"]

        online = [user["user_name"] for user in data]
        return online
