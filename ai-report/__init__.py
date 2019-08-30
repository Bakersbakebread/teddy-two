from .main import AiReport


def setup(bot):
    bot.add_cog(AiReport(bot))
