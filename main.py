import asyncio
import discord
import logging
import os
import pickle

from datetime import datetime
from twitch import TwitchActions

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


class TheBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.users_data = {}
        self.online_users = {}

        try:
            with open("data.dat", "rb") as fp:
                self.users_data = pickle.load(fp)
        except FileNotFoundError:
            logging.warning("Failed to load data")
        try:
            with open("online.dat", "rb") as fp:
                self.online_users = pickle.load(fp)
        except FileNotFoundError:
            logging.warning("Failed to load online")

        self.bg_task = self.loop.create_task(self.check_online())

    async def on_ready(self):
        logging.info("We have logged in as {0.user}".format(self))

    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.content.startswith("add"):
            user_login = message.content.split()[1]
            logging.info(f"Added user {user_login}")
            self.subscribe_user_channel(message.channel.id, user_login)
            await message.channel.send(f"Added user '{user_login}'!")

        if message.content.startswith("remove"):
            user_login = message.content.split()[1]
            logging.info(f"Removed user {user_login}")
            self.unssubscribe_user_channel(message.channel.id, user_login)
            await message.channel.send(f"Removed user '{user_login}'!")

    def subscribe_user_channel(self, channel, user_login):
        if not self.users_data.get(channel):
            self.users_data[channel] = []
        self.users_data[channel].append(user_login)
        self.dump_users()

    def unsubscribe_user_channel(self, channel, user_login):
        if not self.users_data.get(channel):
            return
        self.users_data[channel].remove(user_login)
        if not self.users_data[channel]:
            del self.users_data[channel]
        self.dump_users()

    def dump_users(self):
        with open("data.dat", "wb") as fp:
            pickle.dump(self.users_data, fp)

    async def edit_message(self, channel_id, user, message_id):
        channel = self.get_channel(channel_id)
        message = await channel.fetch_message(message_id)
        vod_url = twitch_client.get_vod_url(
            self.users_data[channel_id][user]["user_id"]
        )
        if "was online" in message.content:
            return
        await message.edit(
            content=f"{user} was online, check the vod: {vod_url}", embed=None
        )

    async def check_online(self):
        await self.wait_until_ready()
        while not self.is_closed():
            for channel, channel_data in self.users_data.items():
                online_users = twitch_client.is_live(channel_data)
                twitch_client.get_user_thumbnail(online_users)
                self.mark_online(online_users, channel)

            for channel_id, channel_data in self.online_users.items():
                channel = self.get_channel(channel_id)
                for user_login in channel_data.keys():
                    if not channel_data[user_login]["sent"]:
                        embed = discord.Embed(
                            title=online_users[user_login]["title"], colour=0x6441A4
                        )
                        embed.set_thumbnail(
                            url=online_users[user_login]["profile_image_url"]
                        )
                        embed.set_image(url=online_users[user_login]["thumbnail_url"])
                        logging.info(f"{user_login} is live!")
                        await channel.send(
                            f"{user_login} is live now! https://twitch.tv/{user_login}",
                            embed=embed,
                        )
                        self.online_users[channel_id][user_login]["sent"] = True
                        with open("online.dat", "wb") as fp:
                            pickle.dump(self.online_users, fp)
            await asyncio.sleep(3 * 60)

    def mark_online(self, users_data, channel):
        now = datetime.now()
        if not self.online_users.get(channel):
            self.online_users[channel] = {}
        for user, user_data in users_data.items():
            online_user = self.online_users[channel].get(user)
            self.online_users[channel][user] = {
                "started_at": user_data["started_at"],
                "updated_at": now,
                "user_id": user_data["user_id"],
                "thumbnail_url": user_data["thumbnail_url"],
                "sent": online_user is not None,
            }

        for user in self.users_data[channel]:
            online_user = self.online_users[channel].get(user)
            if online_user and online_user["updated_at"] != now:
                del self.online_users[channel][user]
        with open("online.dat", "wb") as fp:
            pickle.dump(self.online_users, fp)


twitch_client = TwitchActions()

client = TheBot()
client.run(os.environ["BOT_TOKEN"])
