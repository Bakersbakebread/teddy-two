import discord
from redbot.core import Config, commands
from redbot.core.commands import Greedy
from .services.uservalidation import UserValidation, yes_or_no
from .services.channel import ChannelService
from .services.messaging import ModmailThread
from .services.setup import SetupService
from .exceptions import *
from .casetypes import CASETYPES

from redbot.core import checks, modlog

import aiohttp

import logging
import asyncio

#
log = logging.getLogger("red.modmail")

GUILD = 614954723816112266

DEFAULT_USER = {
    "last_messaged": None,
    "thread_is_open": False,
    "current_thread": None,
    "view_access": False,
    "blocked": False,
    "threads": [],
    "type_holding": False,
}

DEFAULT_GLOBAL = {
    "threads": {},
    "archive": [],
    "modmail_type": "channel",
    "allowed_roles": [],
    "new_cat_id": None,
    "active_cat_id": None,
    "modlog_id": None,
    "guild_id": 614954723816112266,
    "fortnite_guild_id": 322850917248663552,
}


class ModmailTeddy(commands.Cog):
    def __init__(self, bot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot
        self.guild = self.bot.get_guild(GUILD)
        self.config = Config.get_conf(
            self, identifier=998877665544332211, force_registration=True
        )
        self.config.register_user(**DEFAULT_USER)
        self.config.register_global(**DEFAULT_GLOBAL)
        self.settings = SetupService(self.bot, self.config)
        asyncio.create_task(self.register_casetypes())
        try:
            self.modcog = self.bot.get_cog("Mod")
        except:
            pass

        self.validate_user = UserValidation(self.bot, self.config)

    async def send_to_owner(self, message):
        owner_id = self.bot.owner_id
        owner_obj = self.bot.get_user(owner_id)
        await owner_obj.send(message)

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
    async def on_guild_channel_delete(self, channel):
        pass

    async def is_modmail_thread(self, channel: discord.TextChannel):
        async with self.config.threads() as threads:
            if str(channel.id) in threads.keys():
                # the first message is always the user we want to reply to
                return True, threads[str(channel.id)][0]['author_id']
            else:
                return False, None

    @commands.Cog.listener(name="on_message")
    async def _on_mod_reply(self, message: discord.Message):
        if isinstance(message.channel, discord.abc.PrivateChannel):
            return
        if message.author.bot:
            return
        is_mod_channel, reply_to_id = await self.is_modmail_thread(message.channel)
        if not is_mod_channel:
            return
        reply_to_user = self.bot.get_user(reply_to_id)
        modmail_service = ModmailThread(message.author, message, self.config, self.bot)
        await modmail_service.create_and_save(message.channel)
        attachments = []
        for a in message.attachments:
            attachments.append(a.url)
        message_to_send = f"{message.content}\n{attachments if len(attachments) > 0 else ' '}"
        try:
            await reply_to_user.send(message_to_send)
        except discord.errors.HTTPException as e:
            await message.channel.send(f"Failed to send message: {e.text}")
            await message.add_reaction(emoji="❌")


    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        author = message.author
        if not isinstance(message.channel, discord.abc.PrivateChannel):
            return
        if author == self.bot.user:
            return
        try:
            can_send, current_thread = await self.validate_user.can_send_modmail(author)
        except UserIsBlocked:
            # log.info(f"Blocked user {author} - {author.id} attempted to send message")
            return await author.send(
                f"You have been blocked from sending modmail, \
                if you believe this is wrong please contact a Mod directly."
            )
        except WaitingForMessageType as exception:
            return await author.send(exception.args[0])

        modmail_service = ModmailThread(author, message, self.config, self.bot)

        if can_send:
            # user is currently waiting for a reply
            channel: discord.TextChannel = self.bot.get_guild(GUILD).get_channel(
                current_thread
            )
        else:
            try:
                # set holding
                await self.config.user(author).type_holding.set(True)

                message_type = await modmail_service.ask_for_type()
                guild = self.bot.get_guild(await self.config.guild_id())

                channel = await ChannelService(
                    author, self.config, guild
                ).create_new_channel()

            except NoNewCategory as e:
                # enforce categories for organising
                await self.send_to_owner(
                    f"Attempted to create modmail channel. Failed because `{e.args[0]}`"
                )
                log.warning(
                    f"Attempted to create modmail channel. Failed because `{e.args[0]}`"
                )
                return
            except discord.Forbidden as e:
                log.warning(
                    f"Attempted to create modmail channel. Failed because `{e.text}`"
                )
                return await self.send_to_owner(
                    f"Attempted to create modmail channel. Failed because `{e.text}`"
                )
            finally:
                await self.config.user(author).type_holding.set(False)

        new_modmail_embed = await modmail_service.create_and_save(channel)

        await self.config.user(author).thread_is_open.set(True)
        await self.config.user(author).current_thread.set(channel.id)

        if can_send and current_thread is not None:
            # only send the message contents and not user info :)
            await channel.send(embed=new_modmail_embed[1])
        else:
            for embed in new_modmail_embed:
                await channel.send(embed=embed)

    @commands.group(name="modmailset")
    async def _modmail_settings(self, ctx):
        pass

    @_modmail_settings.command()
    async def guild(self, ctx, guild: int = None):
        if guild is None:
            guild = ctx.guild.id

        guild = self.bot.get_guild(guild)
        if guild is None:
            return await ctx.send(
                f"`⛔ Invalid guild provided`\n"
                f"**The bot must be in the guild you are trying to assign.**\n"
                f"You can attempt to create a guild with `{ctx.prefix}modmailset createguild`"
            )

        # check if guild ID
        config_guild_id = await self.config.guild_id()
        if config_guild_id is not None:
            config_guild = self.bot.get_guild(config_guild_id)
            result = await yes_or_no(
                ctx,
                message=f"You currently have your guild set as: `{config_guild}` `({config_guild.id})`\n"
                f"Would you like to override this?",
            )
            if result:
                await self.config.guild_id.set(guild.id)
                return await ctx.send(
                    f"👍🏼 Guild has been set to `{guild}` `({guild.id})`"
                )
            else:
                return await ctx.send(
                    f"👉🏼 Okay, guild has remained as `{config_guild}` `({config_guild.id})`"
                )

    ### Roles
    @_modmail_settings.command()
    async def addroles(self, ctx, roles: Greedy[discord.Role]):
        fmt_roles = "\n".join([f"`{role.name}`" for role in roles])
        result = await yes_or_no(
            ctx,
            message=(
                f"**Granting these roles permissions to view / reply to modmail:**"
                f"\n\n{fmt_roles}\n\n"
                f"Continue?"
            ),
        )
        if result:
            for role in roles:
                await self.settings.append_allowed_role(role)
            await ctx.send(f"👍🏼 Added `{len(roles)}` roles to allowed roles.")
        else:
            await ctx.send("👍🏼 Okay. Nothing changed.")

    @_modmail_settings.command()
    async def viewroles(self, ctx):
        guild: discord.Guild = self.bot.get_guild(await self.config.guild_id())
        await ctx.send(
            "**Roles with view / reply access to modmail:**\n"
            + (
                "\n".join(
                    [
                        f"`{role.name}`"
                        for role in [
                        guild.get_role(role)
                        for role in await self.config.allowed_roles()
                    ]
                    ]
                )
            )
        )

    ### Users
    @_modmail_settings.command()
    async def addusers(self, ctx, users: Greedy[discord.Member]):
        for user in users:
            await self.config.user(user).view_access.set(True)
        await ctx.send("👍🏼 Users now have view / reply access")

    @_modmail_settings.command()
    async def delusers(self, ctx, users: Greedy[discord.Member]):
        for user in users:
            await self.config.user(user).view_access.set(False)
        await ctx.send("👍🏼 Users access have been removed.")

    @_modmail_settings.command()
    async def block(self, ctx, member: discord.Member):
        before = await self.config.user(member).blocked()
        await self.config.user(member).blocked.set(not before)
        await ctx.send(
            f"👍🏼 `{member}` has been " + ("`blocked`" if not before else "`unblocked`")
        )
