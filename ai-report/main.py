import discord
from discord import utils
from redbot.core import Config, commands
import aiohttp
import logging

log = logging.getLogger(name="red.bread.aireport")

DEFAULT_USER = {"previous_walls": 0, "previous_lfg": 0, "previous_account": 0, "negative": 0, "neutral": 0, "positive":0 }

DEFAULT_GLOBAL = {"fortnite_guild_id": 322850917248663552, "negative": 0, "neutral": 0, "positive":0}

DEFAULT_MEMBER = { "negative": 0, "neutral": 0, "positive":0 }


class AiReport(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=15957534545, force_registration=True
        )
        self.config.register_global(**DEFAULT_GLOBAL)
        self.config.register_user(**DEFAULT_USER)
        self.config.register_member(**DEFAULT_MEMBER)

    async def send_to_mods(self, message=None, embed=None) -> discord.Message:
        fortnite_guild_id = await self.config.fortnite_guild_id()
        fortnite_guild: discord.Guild = self.bot.get_guild(fortnite_guild_id)
        channel = fortnite_guild.get_channel(379814757030690816)

        if message:
            msg = await channel.send(message)
        if embed:
            msg = await channel.send(embed=embed)

        return msg

    @commands.Cog.listener(name="on_wall_text")
    async def _process_wall_text(self, message: discord.Message):

        wall_text_sent = await self.config.user(message.author).previous_walls()
        await self.config.user(message.author).previous_walls.set(wall_text_sent + 1)

        current_wall_text_sent = await self.config.user(message.author).previous_walls()

        message_wall_text = (
            (message.content[:75] + "....")
            if len(message.content.split()) > 25
            else message.content
        )

        embed = discord.Embed(
            color=discord.Color.gold(),
            title="Possible wall text\n",
            description=f"{message.author} | Author ID: `{message.author.id}`\n"
            f"[Jump to message]({message.jump_url})\n"
            f"Message:\n `{message_wall_text}`",
        )
        embed.add_field(
            name="Previous walltext sent", value=f"{current_wall_text_sent} times"
        )
        embed.set_footer(text=f"!! {message.author.id}")
        msg: discord.Message = await self.send_to_mods(embed=embed)

        log.info(
            f"Wall Text found: {message.author.id} in channel {message.channel} ({message.channel.id})"
        )

    @commands.Cog.listener(name="on_account_selling")
    async def _process_account_selling(self, message: discord.Message):
        previous_account = await self.config.user(message.author).get_raw(
            "previous_account"
        )
        await self.config.user(message.author).previous_account.set(
            previous_account + 1
        )
        new_account = await self.config.user(message.author).get_raw("previous_account")
        embed = discord.Embed(
            color=discord.Color.orange(),
            title="Possible account selling\n",
            description=f"Author ID: `{message.author.id}`\n"
            f"[Jump to message]({message.jump_url})\n",
        )
        embed.set_thumbnail(
            url="https://dummyimage.com/400/ff0000/ffffff.png&text=Account"
        )
        embed.set_author(
            name=f"{message.author} - {message.author.id}",
            icon_url=message.author.avatar_url,
        )
        embed.add_field(
            name="Previous account messages",
            value=f"{message.author} has sent `{new_account}` messages about selling/trading/gifting an account.",
        )
        embed.add_field(name="Message Content", value=f"```{message.content}```")
        embed.set_footer(text=f"!wban {message.author.id} [[account]]")
        await self.send_to_mods(embed=embed)
        log.info(
            f"Account selling message: {message.author.id} in channel {message.channel} ({message.channel.id})"
        )

    @commands.Cog.listener(name="on_incorrect_channel_lfg")
    async def _process_incorrect_lfg_channel(self, message: discord.Message):
        previous_lfg = await self.config.user(message.author).previous_lfg()
        await self.config.user(message.author).previous_lfg.set(previous_lfg + 1)
        new_lfg = await self.config.user(message.author).previous_lfg()
        embed = discord.Embed(
            color=discord.Color.red(),
            title="Possible off-topic LFG Message in #fortnite-general\n",
            description=f"\nAuthor ID: `{message.author.id}`\n"
            f"[Jump to message]({message.jump_url})",
        )
        embed.set_author(
            name=f"{message.author} - {message.author.id}",
            icon_url=message.author.avatar_url,
        )
        embed.set_thumbnail(url="https://dummyimage.com/500/ffb700/000000.png&text=LFG")
        embed.add_field(
            name="Previous LFG messages",
            value=f"{message.author} has sent `{new_lfg}` LFG messages into #fortnite-general",
        )
        embed.add_field(name="Message Content", value=f"```{message.content}```")
        embed.set_footer(text=f"!wsimple {message.author.id} [[lfgS]]")
        await self.send_to_mods(embed=embed)
        log.info(
            f"LFG Message found: {message.author.id} in channel {message.channel} ({message.channel.id})"
        )

    @commands.Cog.listener(name="on_banned_word")
    async def _process_banned_word(self, message: discord.Message, entity_value):
        embed = discord.Embed(
            color=discord.Color.red(),
            title="Possible filtered word\n",
            description=f"\nAuthor ID: `{message.author.id}`\n"
            f"[Jump to message]({message.jump_url})\n"
            f"Sent in: {message.channel.mention}",
        )
        embed.set_author(
            name=f"{message.author} - {message.author.id}",
            icon_url=message.author.avatar_url,
        )
        embed.set_thumbnail(url="https://dummyimage.com/500/ffb700/000000.png&text=WORD")
        embed.add_field(
            name="Triggered value",
            value=entity_value,
        )
        embed.add_field(name="Message Content", value=f"```{message.content}```")
        await self.send_to_mods(embed=embed)
        log.info(
            f"BADWORD Message found: {message.author.id} in channel {message.channel} ({message.channel.id})"
        )

    @commands.Cog.listener(name="on_update_sentiment")
    async def _process_sentiment(self, message:discord.Message, sentiment_value):

        author = message.author
        previous_neg = await self.config.member(author).negative()
        previous_pos = await self.config.member(author).positive()
        previous_neut = await self.config.member(author).neutral()
        glob_previous_neg = await self.config.negative()
        glob_previous_pos = await self.config.positive()
        glob_previous_neut = await self.config.neutral()

        if sentiment_value == 'negative':
            await self.config.negative.set(glob_previous_neg + 1)
            await self.config.member(author).negative.set(previous_neg + 1)

        if sentiment_value == 'neutral':
            await self.config.neutral.set(glob_previous_neut + 1)
            await self.config.member(author).neutral.set(previous_neut + 1)

        if sentiment_value == 'positive':
            await self.config.positive.set(glob_previous_pos + 1)
            await self.config.member(author).positive.set(previous_pos + 1)

    @commands.command()
    async def sentiment(self, ctx, member: discord.Member = None):
        """
        Grab the defined sentiments for user provided, shows guild if none provided

        Net score is defined as : (Positive + Neutral Conversations – Negative Conversations) / Total Conversations.
        """
        glob_previous_neg = await self.config.negative()
        glob_previous_pos = await self.config.positive()
        glob_previous_neut = await self.config.neutral()

        if member:
            previous_neg = await self.config.member(member).negative()
            previous_pos = await self.config.member(member).positive()
            previous_neut = await self.config.member(member).neutral()

            total_conversations = (previous_pos + previous_neg + previous_neut)
            try:
                net_score = ((previous_pos + previous_neut) - previous_neg) / total_conversations
            except ZeroDivisionError:
                net_score = 0.0

            description = f"Total Converations: `{total_conversations}`\n\n" \
                f"Positive: `{previous_pos}`\n" \
                f"Negative: `{previous_neg}`\n" \
                f"Neutral: `{previous_neut}`\n\n" \
                f"Total net score: `{net_score}`"

            embed = discord.Embed(title="Sentiment for User", description=description, color=discord.Color.blue())
            embed.set_author(name=f"{member} - {member.id}", icon_url=member.avatar_url)

            await ctx.send(embed = embed)

        else:
            total_conversations = (glob_previous_pos + glob_previous_neg + glob_previous_neut)
            try:
                net_score = ((glob_previous_pos + glob_previous_neut) - glob_previous_neg) / total_conversations
            except ZeroDivisionError:
                net_score = 0.0

            description = f"Total Converations: `{total_conversations}`\n\n" \
                f"Positive: `{glob_previous_pos}`\n" \
                f"Negative: `{glob_previous_neg}`\n" \
                f"Neutral: `{glob_previous_neut}`\n\n" \
                f"Total net score: `{net_score}`"

            embed = discord.Embed(title="Official Fortnite Discord Sentiment",
                                  description=description,
                                  color=discord.Color.blue())
            embed.set_author(name=f"{ctx.guild.name}", icon_url=ctx.guild.icon_url)

            await ctx.send(embed = embed)


    @commands.Cog.listener(name="on_message")
    async def ai_takeover(self, message: discord.Message):
        headers = {"Authorization": "Bearer PYETRJV4XAARAEQBEVQE7KAX4QXLVPRO"}
        fortnite_guild_id = await self.config.fortnite_guild_id()
        fortnite_guild = self.bot.get_guild(fortnite_guild_id)

        if isinstance(message.channel, discord.abc.PrivateChannel):
            return

        if message.author.bot:
            return

        if message.channel.id == 446492143578775573:
            return

        if 322850917248663552 != message.guild.id:
            return

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(
                f"https://api.wit.ai/message?v=20190826&q={message.content}"
            ) as resp:
                entities = await resp.json()
                values = entities.get("entities")

                try:
                    x = message.content.split()
                    is_wall_text = sum((itm.count(x[0]) for itm in x)) > 25
                    is_maybe_wall_text = len(x[0]) > 800
                    if is_wall_text or is_maybe_wall_text:
                        self.bot.dispatch("wall_text", message)
                except IndexError:
                    # message probably one word long
                    pass

                try:
                    if values:
                        bad_words = values['bad_words']
                        if bad_words[0]['confidence'] > 0.7:
                            self.bot.dispatch('banned_word', message, values['bad_words'][0]['value'])
                except KeyError:
                    pass

                try:
                    if values:
                        sentiment = values['sentiment']
                        if sentiment[0]['confidence'] > 0.7:
                            log.info(f"({message.author} Sentiment analysis: {message.content} : {sentiment[0]['value']}")
                            self.bot.dispatch("update_sentiment", message, sentiment[0]['value'])
                except KeyError:
                    pass

                try:
                    if values:
                        intent = values["intent"]
                        if (
                            intent[0]["value"] == "account_selling"
                            and intent[0]["confidence"] > 0.7
                        ):
                            self.bot.dispatch("account_selling", message)

                        if (
                            message.channel.id == 338017726394138624
                            and intent[0]["value"] == "LFG"
                            and intent[0]["confidence"] > 0.7
                        ):
                            self.bot.dispatch("wrong_channel_lfg", message)
                except IndexError:
                    pass
                except KeyError:
                    pass
                log.debug(f"({message.author} : {message.content} Values: {values}")

