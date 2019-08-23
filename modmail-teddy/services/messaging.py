import discord

class ModmailThread:
    def __init__(self, member: discord.User, message: discord.Message, config):
        self.member = member
        self.message = message
        self.config = config

    async def build_thread_embed(self):
        author = self.message.author

        attachments_urls = [
            self.message.attachments.url for self.message.attachments in self.message.attachments
        ]
        attached_list = "\n".join(attachments_urls)

        if self.message.attachments:
            attachments_string = f"**Attachments**\n {attached_list}"
        else:
            attachments_string = f" "

        description = (
            f"**Author** \n"
            f" `ID: {author.id}` \n\n"
            f"**Message Content**\n"
            f"```{self.message.content}```\n"
            f"{attachments_string}"
        )

        em = discord.Embed(
            title=f"📬 New modmail",
        description= description)
        em.set_author(name=f"{self.member.name}#{self.member.discriminator}")
        em.set_thumbnail(url=self.member.avatar_url)

        return em


    async def create_and_save(self) -> discord.Embed:
        new_thread = await self.create_new_json()
        async with self.config.threads() as threads:
            threads.append(new_thread)

        embed = await self.build_thread_embed()
        return embed

    async def create_save_reply(self, user_id):
        new_reply = await self.create_new_reply_json()
        async with self.config.threads() as threads:
            for thread in threads:
                if thread['author_id'] == user_id:
                    thread['reply'] = new_reply

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