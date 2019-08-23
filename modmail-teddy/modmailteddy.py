import discord
from redbot.core import Config, commands

class ModmailTeddy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Config.get_conf(
            self, identifier=998877665544332211, force_registration=True
        )