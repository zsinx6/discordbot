import discord
import logging
import os
import pickle

from twitch import TwitchActions

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

client = discord.Client()


@client.event
async def on_ready():
    logging.info("We have logged in as {0.user}".format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith("$hello"):
        await message.channel.send("Hello!")

    if message.content.startswith("add"):
        user_login = message.content.split()[1]
        bot.subscribe_user_channel(message.channel.id, message.author.id, user_login)
        await message.channel.send(f"Added user '{user_login}'!")

    if message.content.startswith("remove"):
        user_login = message.content.split()[1]
        bot.unssubscribe_user_channel(message.channel.id, message.author.id, user_login)
        await message.channel.send(f"Removed user '{user_login}'!")


class TheBot:
    def __init__(self):
        self.users_data = {}
        try:
            with open("data.json", "rb") as fp:
                self.users_data = pickle.load(fp)
        except FileNotFoundError:
            logging.warning("Failed to load json")

    def subscribe_user_channel(self, channel, user, user_login):
        if not self.users_data.get(user):
            self.users_data[user] = {channel: {"user_login": []}}
        self.users_data[user][channel]["user_login"].append(user_login)
        self.dump_users()

    def unsubscribe_user_channel(self, channel, user, user_login):
        if not self.users_data.get(user):
            return
        self.users_data[user][channel]["user_login"].remove(user_login)
        if not self.users_data[user][channel]["user_login"]:
            del self.users_data[user][channel]
        if not self.users_data[user]:
            del self.users_data[user]
        self.dump_users()

    def dump_users(self):
        with open("data.json", "wb") as fp:
            pickle.dump(self.users_data, fp)


twitch_client = TwitchActions()
bot = TheBot()
client.run(os.environ["BOT_TOKEN"])
