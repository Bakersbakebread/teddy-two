import discord
from ..exceptions import UserIsBlocked


class UserValidation:
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config

    async def can_send_modmail(self, user: discord.User):
        blocked = await self.config.user(user).get_raw("blocked")
        if blocked:
            raise UserIsBlocked
        thread_open = await self.config.user(user).get_raw("thread_is_open")
        if thread_open:
            return False
        return True
