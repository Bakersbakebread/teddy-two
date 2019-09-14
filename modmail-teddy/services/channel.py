import discord
from ..exceptions import NoNewCategory
from ..enums import ThreadStatus
import logging


log = logging.getLogger("red.modmail")


class ChannelService:
    def __init__(self, member, config, guild: discord.Guild):
        self.member = member
        self.config = config
        self.guild = guild

    async def fmt_name(self, status: ThreadStatus) -> str:
        text, emoji = status.value
        return f"{emoji}-{text}-{self.member.name}"

    async def thread_count(self) -> int:
        count = 0
        async with self.config.threads() as threads:
            for thread in threads:
                if thread["author_id"] == self.member.id:
                    count += 1
        return count

    async def fmt_topic(self) -> str:
        return "sharky smells"

    async def create_new_category(self, name: str):
        overwrites = {
            self.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            self.guild.me: discord.PermissionOverwrite(read_messages=True),
        }
        await self.guild.create_category(
            name=name, overwrites=overwrites, reason="Modmail category creation"
        )

    async def create_new_channel(self) -> discord.TextChannel:
        channel_name = await self.fmt_name(status=ThreadStatus.NEW)
        category = discord.utils.find(
            lambda cat: cat.name == "new", self.guild.categories
        )
        topic = await self.fmt_topic()
        if category is None:
            # log.exception("No NEW category setup in server")
            raise NoNewCategory("No new category in modmail server")

        channel = await self.guild.create_text_channel(
            name=channel_name,
            category=category,
            reason="New modmail channel creation",
            topic=topic,
        )
        return channel
