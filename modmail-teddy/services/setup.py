import discord
from redbot.core import Config, commands
import logging

from .channel import ChannelService

log = logging.getLogger(name="red.bread.modmail")


class SetupService:
    def __init__(self, bot, config, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot: discord.Client = bot
        self.config = config

    @commands.command(name="tp")
    async def _send_test(self, ctx):
        await ctx.send("test")

    async def set_modmail_guild(self, guild_id: int):
        guild = await self.bot.get_guild(guild_id)
        if guild is None:
            raise ValueError("No guild found with that ID")
        if not isinstance(guild_id, int):
            raise ValueError("Guild ID must be an integer")
        await self.config.guild_id.set(guild_id)

    async def create_modmail_guild(self, name: str) -> discord.Guild:
        """
        Attempts to create guild
        :param name: The name of the guild to create
        :return: Guild

        """
        try:
            return await self.bot.create_guild(name=name)
        except discord.HTTPException as ex:
            # Bot is probably in more than 10 guilds
            # Bot accounts in more than 10 guilds are not allowed to create guilds.
            log.exception(msg=f"Failed to create guild with name {name}")

    async def append_allowed_role(self, role: discord.Role) -> list:
        """
        Appends role to list of allowed_roles in config
        :param role: Role to append
        :return: Updated list of roles appended
        """
        async with self.config.allowed_roles() as allowed_roles:
            if role.id not in allowed_roles:
                allowed_roles.append(role.id)
            return allowed_roles

    async def toggle_modmail_access(self, user: discord.Member) -> tuple:
        """
        Toggles permission for user to view/reply to modmails
        :param user: The user to toggle permissions
        :return: Before permission and after permissions
        """
        before = await self.config.user(user).view_access()
        after = await self.config.user(user).view_access.set(not before)

        return before, after
