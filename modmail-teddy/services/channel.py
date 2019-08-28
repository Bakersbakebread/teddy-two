import discord
from ..exceptions import NoNewCategory
import logging

log = logging.getLogger("red.modmail")


class ChannelService:
    def __init__(self, member, message: discord.Message, config, guild: discord.Guild):
        self.member = member
        self.config = config
        self.guild = guild

    async def fmt_name(self, status):
        em = "📬" if status == "new" else "📤"
        return f"{em}-💭-{self.member.name}"

    async def thread_count(self):
        count = 0
        async with self.config.threads() as threads:
            for thread in threads:
                if thread["author_id"] == self.member.id:
                    count += 1
        return count

    async def fmt_topic(self):
        return "sharky smells"

    async def create_new_channel(self):
        channel_name = await self.fmt_name(status="new")
        category = discord.utils.find(
            lambda cat: cat.name == "new", self.guild.categories
        )
        topic = await self.fmt_topic()
        if category is None:
            # log.exception("No NEW category setup in server")
            raise NoNewCategory

        try:
            channel = await self.guild.create_text_channel(
                name=channel_name,
                category=category,
                reason="New modmail channel creation",
                topic=topic,
            )
        except discord.errors.Forbidden as e:
            log.exception(e.text)
            return None
        return channel
