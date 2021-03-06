import requests
import os

from dateutil import parser


class TwitchActions:
    def __init__(self):
        self.client_id = os.environ["CLIENT_ID"]
        self.client_secret = os.environ["CLIENT_SECRET"]
        self.token = None
        self.refresh_token()

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

        online = {user["user_name"]: parser.parse(user["started_at"]) for user in data}
        online = {}
        for user in data:
            user_data = {
                "started_at": parser.parse(user["started_at"]),
                "user_id": user["user_id"],
                "thumbnail_url": user["thumbnail_url"].format(width=400, height=230),
                "title": user["title"],
            }
            online[user["user_name"].lower()] = user_data

        return online

    def get_user_thumbnail(self, online_data):
        if not online_data:
            return
        self.refresh_token()
        url = "https://api.twitch.tv/helix/users?"
        url_users = ""
        for user_name, data in online_data.items():
            url_users += f"&id={data['user_id']}"
        url += url_users[1:]
        header = {"client-id": self.client_id, "Authorization": f"Bearer {self.token}"}
        result = requests.get(url, headers=header)

        data = result.json()["data"]

        for user_name in online_data.keys():
            for user_json in data:
                if user_json["login"] in online_data.keys():
                    online_data[user_name]["profile_image_url"] = user_json[
                        "profile_image_url"
                    ]

    def get_vod_url(self, user_id):
        self.refresh_token()
        url = "https://api.twitch.tv/helix/videos/"
        query = {"user_id": user_id}
        header = {"client-id": self.client_id, "Authorization": f"Bearer {self.token}"}

        result = requests.get(url, headers=header, params=query)

        data = result.json()["data"]
        if data:
            return data[0]["url"]
