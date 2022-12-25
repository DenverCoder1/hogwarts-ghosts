from nextcord.ext import commands

import database


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


def is_tester():
    async def predicate(ctx):
        if ctx.message.author.guild_permissions.administrator:

            return True
        if ctx.message.guild is None:
            return False
        if ctx.guild.id in database.TESTERS:
            for role in ctx.author.roles:
                role_id = role.id
                if role_id in database.TESTERS[ctx.guild.id]:
                    return True
            return False
        else:
            return False

    return commands.check(predicate)


def is_solver():
    async def predicate(ctx):
        if ctx.message.author.guild_permissions.administrator:

            return True
        if ctx.message.guild is None:
            return False
        if ctx.guild.id in database.SOLVERS:
            for role in ctx.author.roles:
                role_id = role.id
                if role_id in database.SOLVERS[ctx.guild.id]:
                    return True
            return False
        else:
            return False

    return commands.check(predicate)


def is_verified():
    async def predicate(ctx):
        if ctx.message.author.guild_permissions.administrator:

            return True
        if ctx.message.guild is None:
            return False
        if ctx.guild.id in database.VERIFIEDS:
            for role in ctx.author.roles:
                role_id = role.id
                if role_id in database.VERIFIEDS[ctx.guild.id]:
                    return True
            return False
        else:
            return False

    return commands.check(predicate)


def is_trusted():
    async def predicate(ctx):
        if ctx.message.author.guild_permissions.administrator:

            return True
        if ctx.message.guild is None:
            return False
        if ctx.guild.id in database.TRUSTEDS:
            for role in ctx.author.roles:
                role_id = role.id
                if role_id in database.TRUSTEDS[ctx.guild.id]:
                    return True
            return False

    return commands.check(predicate)
