import discord
# import logging
#
# log = logging.getLogger("red.modmail")

class ChannelService:
    def __init__(self, member, message: discord.Message, config, guild: discord.Guild):
        self.member = member
        self.config = config
        self.guild = guild

    async def fmt_name(self, status):
        em = "📬" if status == "new" else "📤"
        return f"{em}-{self.member.id}"

    async def thread_count(self):
        count = 0
        async with self.config.threads() as threads:
            for thread in threads:
                if thread['author_id'] == self.member.id:
                    count += 1
        return count

    async def fmt_topic(self):
        return "return string of user info here"

    async def create_new_channel(self):
        channel_name = await self.fmt_name(status='new')
        category = [x for x in self.guild.categories if x.name.lower() == "new"]
        topic = await self.fmt_topic()
        try:
            category = category[0]
        except:
            # log.exception("No NEW category setup in server")
            return await self.guild.owner.send("Please setup modmail server with a 'NEW' category")

        channel = await self.guild.create_text_channel(
            name=channel_name,
            category= category,
            reason="New modmail channel creation",
            topic = topic
        )
        return channel







