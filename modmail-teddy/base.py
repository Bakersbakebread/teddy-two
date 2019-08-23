import discord
from redbot.core import Config, commands
from .services.uservalidation import UserValidation
from .services.channel import ChannelService
from .services.messaging import ModmailThread
from .exceptions import *
from .casetypes import CASETYPES
from redbot.core import checks, modlog

import logging
import asyncio
#
# log = logging.getLogger("red.modmail")

GUILD = 561619840377552896

DEFAULT_USER = {
    "last_messaged": None,
    "thread_is_open": False,
    "current_thread": 0,
    "blocked": False,
    "threads":[]
}

DEFAULT_GLOBAL = {
    "threads": [],
    "new_cat_id":None,
    "active_cat_id":None,
    "modlog_id":None
}

class ModmailTeddy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=998877665544332211, force_registration=True
        )
        self.config.register_user(**DEFAULT_USER)
        self.config.register_global(**DEFAULT_GLOBAL)
        asyncio.create_task(self.register_casetypes())
        try:
            self.modcog = self.bot.get_cog("Mod")
        except:
            pass

        self.validate_user = UserValidation(self.bot, self.config)

    async def register_casetypes(self):
        # thanks wmod
        # Register casetypes with modlog
        for idx, c in enumerate(CASETYPES):
            try:
                # Try sending in the case data to ModLog - ternary operation in final param to allow undefined `audit_type`
                await modlog.register_casetype(
                    c["name"],
                    c["default_setting"],
                    c["image"],
                    c["case_str"],
                    (c["audit_type"] if "audit_type" in c else None),
                )
            except Exception as e:
                print(f"Case load {c['name']} failed - {e}")
                pass

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        author = message.author
        if not isinstance(message.channel, discord.abc.PrivateChannel):
            return
        if author == self.bot.user:
            return
        try:
            can_send = await self.validate_user.can_send_modmail(author)
        except UserIsBlocked:
            # log.info(f"Blocked user {author} - {author.id} attempted to send message")
            return await author.send(
                f"You have been blocked from sending modmail, \
                if you believe this is wrong please contact a Mod directly.")

        if not can_send:
            # user is currently waiting for a reply
            return await author.send(
                'Please wait for your previous message to be answered before sending another.')

        channel = \
            await ChannelService(author, message, self.config, self.bot.get_guild(GUILD)).create_new_channel()

        new_modmail_embed = await ModmailThread(author, message, self.config).create_and_save()

        await self.config.user(author).thread_is_open.set(True)
        await self.config.user(author).current_thread.set(channel.id)


        await channel.send(embed=new_modmail_embed)






