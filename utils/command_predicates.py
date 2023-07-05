from nextcord.ext import commands

def is_owner_or_admin():
    async def predicate(ctx):
        if ctx.message.guild is None:
            return False
        is_owner = await ctx.bot.is_owner(ctx.author)
        return is_owner or ctx.message.author.guild_permissions.administrator

    return commands.check(predicate)


def is_owner():
    async def predicate(ctx):
        if ctx.message.guild is None:
            return False
        return ctx.author == ctx.guild.owner

    return commands.check(predicate)
