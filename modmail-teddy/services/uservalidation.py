import discord
from ..exceptions import UserIsBlocked, WaitingForMessageType
from redbot.core.utils.predicates import ReactionPredicate
from redbot.core.utils.menus import start_adding_reactions


class UserValidation:
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config

    async def can_send_modmail(self, user: discord.User):
        """
        Checks if user is blocked and returns current thread, if one is found
        :param user: The user to check
        :return: current_thread
        """
        blocked = await self.config.user(user).get_raw("blocked")
        type_waiting = await self.config.user(user).get_raw("type_holding")
        if blocked:
            raise UserIsBlocked
        if type_waiting:
            raise WaitingForMessageType(
                "Please choose type of message you wish to send"
            )
        thread_open = await self.config.user(user).get_raw("thread_is_open")
        current_thread = await self.config.user(user).get_raw("current_thread")

        if thread_open:
            return True, current_thread
        else:
            return False, None


async def yes_or_no(ctx, message) -> bool:
    msg = await ctx.send(message)
    start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)

    pred = ReactionPredicate.yes_or_no(msg, ctx.author)
    await ctx.bot.wait_for("reaction_add", check=pred)
    await msg.delete()
    return pred.result


async def message_type_reaction(ctx, embed: discord.Embed, emojis: list = None):
    msg: discord.Message = await ctx.send(embed=embed)
    if emojis is None:
        emojis = ["⚠", "💬"]
    start_adding_reactions(msg, emojis)

    pred = ReactionPredicate.with_emojis(emojis, msg)
    await ctx.bot.wait_for("reaction_add", check=pred)
    await msg.delete()
    await ctx.send("Thank-you. Someone will reply shortly, please be patient")
    return pred.result
    # pred.result is now the index of the letter in `emojis`
