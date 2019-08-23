from .base import ModmailTeddy


def setup(bot):
    bot.add_cog(ModmailTeddy(bot))
