import discord
from redbot.core.utils.common_filters import filter_invites
from ..enums import ThreadStatus
from .uservalidation import message_type_reaction
from datetime import datetime
from redbot.cogs.mod.names import ModInfo


class ModmailThread:
    def __init__(self, member: discord.User, message: discord.Message, config, bot):
        self.member = member
        self.message = message
        self.config = config
        self.bot = bot
        self.created_at = self.message.created_at

    async def build_user_info_embed(self):
        """Stolen from core red cogs and adapted where needed.."""
        user = self.member
        message = self.message
        fortnite_guild_id = await self.config.fortnite_guild_id()
        fortnite_guild = self.bot.get_guild(fortnite_guild_id)
        user = fortnite_guild.get_member(user.id)

        roles = user.roles[-1:0:-1]

        activity = "Chilling in {} status".format(user.status)
        if user.activity is None:  # Default status
            pass
        elif user.activity.type == discord.ActivityType.playing:
            activity = "Playing {}".format(user.activity.name)
        elif user.activity.type == discord.ActivityType.streaming:
            activity = "Streaming [{}]({})".format(
                user.activity.name, user.activity.url
            )
        elif user.activity.type == discord.ActivityType.listening:
            activity = "Listening to {}".format(user.activity.name)
        elif user.activity.type == discord.ActivityType.watching:
            activity = "Watching {}".format(user.activity.name)

        if roles:
            roles = ", ".join([x.name for x in roles])
        else:
            roles = None

        joined_at = user.joined_at
        since_created = (message.created_at - user.created_at).days

        if joined_at is not None:
            since_joined = (message.created_at - joined_at).days
            user_joined = joined_at.strftime("%d %b %Y %H:%M")
        else:
            since_joined = "?"
            user_joined = "Unknown"

        user_created = user.created_at.strftime("%d %b %Y %H:%M")
        voice_state = user.voice
        member_number = (
            sorted(
                fortnite_guild.members, key=lambda m: m.joined_at or message.created_at
            ).index(user)
            + 1
        )

        created_on = "{}\n({} days ago)".format(user_created, since_created)
        joined_on = "{}\n({} days ago)".format(user_joined, since_joined)

        embed = discord.Embed(color=discord.Color.green(), description=activity)

        embed.add_field(name="Joined Discord on", value=created_on)
        embed.add_field(name="Joined Official Fortnite server on", value=joined_on)
        if roles is not None:
            embed.add_field(name="Roles", value=roles, inline=False)
        if voice_state and voice_state.channel:
            embed.add_field(
                name="Current voice channel",
                value="{0.mention} ID: {0.id}".format(voice_state.channel),
                inline=False,
            )
        embed.set_footer(
            text=("Member #{} | User ID: {}").format(member_number, user.id)
        )

        name = str(user)
        name = " ~ ".join((name, user.nick)) if user.nick else name
        name = filter_invites(name)

        if user.avatar:
            avatar = user.avatar_url_as(static_format="png")
            embed.set_author(name=name, url=avatar)
            embed.set_thumbnail(url=avatar)
        else:
            embed.set_author(name=name)

        return embed

    async def build_thread_message_embed(self):

        attachments_urls = [
            self.message.attachments.url
            for self.message.attachments in self.message.attachments
        ]
        attached_list = "\n".join(attachments_urls)

        if self.message.attachments:
            attachments_string = f"```\n{attached_list}\n```"
        else:
            attachments_string = f" "

        description = f"```{self.message.content}⠀⠀```\n"

        embed = discord.Embed(
            description=description,
            title="Message contents",
            color=discord.Color.green(),
            timestamp=self.created_at,
        )
        embed.set_footer(text=f"New message received from {self.member}")
        if len(attachments_urls) > 0:
            embed.add_field(name="Attachments", value=attachments_string)
            embed.set_image(url=attachments_urls[0])

        return embed

    async def create_and_save(self, channel: discord.TextChannel) -> list:
        new_thread = await self.create_new_json(channel)
        async with self.config.threads() as threads:
            if str(channel.id) in threads.keys():
                threads[str(channel.id)].append(new_thread)
            else:
                threads[channel.id] = [new_thread]

        return [
            await self.build_user_info_embed(),
            await self.build_thread_message_embed(),
        ]

    async def create_save_reply(self, user_id):
        new_reply = await self.create_new_reply_json()
        async with self.config.threads() as threads:
            for thread in threads:
                if thread["author_id"] == user_id:
                    thread["reply"] = new_reply

        return new_reply

    async def create_new_json(self, channel: discord.TextChannel) -> dict:
        attachments = [a.url for a in self.message.attachments]
        author = self.message.author
        final_json = {
                "id": self.message.id,
                "author_id": author.id,
                "category": None,
                "created_at": self.created_at.timestamp(),
                "content": self.message.content,
                "attachments": attachments

        }
        return final_json

    async def create_new_reply_json(self):
        json_message = {
            "id": self.message.id,
            "author": await self.author_to_json(self.member),
            "content": self.message.content,
        }

        final_json = {
            "id": self.message.id,
            "created_at": self.message.created_at.strftime("%m/%d/%Y, %H:%M"),
            "thread": json_message,
        }
        return final_json

    async def author_to_json(self, author):
        json_author = {
            "id": author.id,
            "name": author.name,
            "discriminator": author.discriminator,
            "avatar": str(author.avatar_url),
            "created_at": author.created_at.isoformat(),
        }
        return json_author

    async def ask_for_type(self):
        msg_ctx = await self.bot.get_context(self.message)
        embed = discord.Embed(
        color=discord.Color.green(),
        title=f"Thank-you for contacting the mod team, {self.message.author.mention}\n\n",
        description=(
            f"In order for us to assist you further, "
            f"please react below to the corresponding category of your message.\n\n"
        ),
        )
        embed.add_field(
        name="⚠ - To report another user.",
        value=(
            f"**Please provide as much information as possible.**\n"
            f"You can attach screenshots and images to your message.\n"
        ),
        )
        embed.add_field(
        name="💬 - To submit a suggestion or feedback",
        inline=False,
        value=f"Please make your feedback into one formed message as multiples are not accepted.",
        )
        embed.set_footer(text="Abuse of this facility will not be tolerated.")

        result = await message_type_reaction(msg_ctx, embed)

        return result
