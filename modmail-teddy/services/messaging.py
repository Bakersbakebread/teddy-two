import discord
from redbot.core.utils.common_filters import filter_invites

from redbot.cogs.mod.names import ModInfo


class ModmailThread:
    def __init__(self, member: discord.User, message: discord.Message, config, bot):
        self.member = member
        self.message = message
        self.config = config
        self.bot = bot

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
            text=("Member #{} | User ID: {}").format(member_number, user.id))

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
            attachments_string = f"**Attachments**\n {attached_list}"
        else:
            attachments_string = f" "

        description = (
            f"```{self.message.content}```\n"
            f"{attachments_string}"
        )

        return discord.Embed(description=description, title="Message contents", color=discord.Color.green())

    async def create_and_save(self) -> list:
        new_thread = await self.create_new_json()
        async with self.config.threads() as threads:
            threads.append(new_thread)

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

    async def create_new_json(self):
        author = self.message.author
        json_author = await self.author_to_json(author)
        json_message = {
            "author": json_author,
            "attachments": self.message.attachments,
            "content": self.message.content,
        }
        final_json = {
            "id": self.message.id,
            "author_id": author.id,
            "status": "new",
            "mod_assigned": None,
            "category": None,
            "created_at": self.message.created_at.strftime("%m/%d/%Y, %H:%M"),
            "thread": json_message,
            "reply": {},
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
