import nextcord
from nextcord.ext import commands
from nextcord.ext.commands.core import command
import psycopg2
from sqlalchemy.orm import Session
import sqlalchemy
from utils import discord_utils, logging_utils, command_predicates
import database
from database import models
import constants
from typing import Union


class AdminCog(commands.Cog, name="Admin"):
    """Commands for bot management by admins and bot owners"""

    def __init__(self, bot):
        self.bot = bot

    @command_predicates.is_owner_or_admin()
    @commands.command(name="addverified",
        aliases=["addverifieds"],
        )
    async def addverified(
        self,
        ctx,
        role_or_rolename: Union[nextcord.Role, str],
        role_permissions: str = "Verified",
    ):
        """Add a new verified category for a given role on this server. Only available to server admins or bot owners.

        A lot of bot commands can only be used by Verified, so this command is necessary before people can use them.

        Category : Admin or Bot Owner Roles only.
        Usage: `~addverified @Verified Verified`
        Usage: `~addverified @everyone Verified`
        """
        logging_utils.log_command("addverified", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        if role_permissions not in database.VERIFIED_CATEGORIES:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"`role_permissions` must be in {', '.join(database.VERIFIED_CATEGORIES)}, "
                f"but you supplied {role_permissions}",
            )
            await ctx.send(embed=embed)
            return

        # Get role. Allow people to use the command by pinging the role, or just naming it
        if isinstance(role_or_rolename, str):
            # Search over all roles and see if we get a match.
            roles = await ctx.guild.fetch_roles()
            for role in roles:
                if role.name.lower() == role_or_rolename.lower():
                    role_to_assign = role
                    break
        else:
            role_to_assign = role_or_rolename

        # Ensure role exists
        if not role_to_assign:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"Error!",
                value=f"I couldn't find role {role_or_rolename}",
                inline=False,
            )
            await ctx.send(embed=embed)
            return

        with Session(database.DATABASE_ENGINE) as session:
            # TODO: Figure out how to catch the duplicate unique key error so I can insert first, then find if exists.
            result = (
                session.query(database.Verifieds)
                .filter_by(
                    role_id_permissions=f"{role_to_assign.id}_{role_permissions}"
                )
                .first()
            )
            if result is None:
                stmt = sqlalchemy.insert(database.Verifieds).values(
                    role_id=role_to_assign.id,
                    role_name=role_to_assign.name,
                    server_id=ctx.guild.id,
                    server_name=ctx.guild.name,
                    permissions=role_permissions,
                    role_id_permissions=f"{role_to_assign.id}_{role_permissions}"
                )
                session.execute(stmt)
                session.commit()
            else:
                embed = discord_utils.create_embed()
                embed.add_field(
                    name=f"{constants.FAILED}!",
                    value=f"Role {role_to_assign.mention} is already `{result.permissions}`!",
                )
                await ctx.send(embed=embed)
                return

        if role_permissions == models.VERIFIED:
            if ctx.guild.id in database.VERIFIEDS:
                database.VERIFIEDS[ctx.guild.id].append(role_to_assign.id)
            else:
                database.VERIFIEDS[ctx.guild.id] = [role_to_assign.id]
        elif role_permissions == models.TRUSTED:
            if ctx.guild.id in database.TRUSTEDS:
                database.TRUSTEDS[ctx.guild.id].append(role_to_assign.id)
            else:
                database.TRUSTEDS[ctx.guild.id] = [role_to_assign.id]

        embed.add_field(
            name=constants.SUCCESS,
            value=f"Added the role {role_to_assign.mention} for this server set to `{role_permissions}`",
            inline=False,
        )
        await ctx.send(embed=embed)

    @command_predicates.is_owner_or_admin()
    @commands.command(
        name="lsverifieds",
        aliases=["listverifieds", "verifieds", "lsverified", "listverified"],
    )
    async def lsverifieds(self, ctx, role_permissions: str = "Verified"):
        """List all roles in Verified Permissions within the server.

        Category : Admin or Bot Owner Roles only.
        Usage: `~listverifieds`
        """
        logging_utils.log_command("lsverifieds", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        if role_permissions not in database.VERIFIED_CATEGORIES:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"`role_permissions` must be in {', '.join(database.VERIFIED_CATEGORIES)}, "
                f"but you supplied {role_permissions}",
            )
            await ctx.send(embed=embed)
            return

        cache_map = {
            models.VERIFIED: database.VERIFIEDS,
            models.TRUSTED: database.TRUSTEDS,
            # TODO: Tester will always return null here because we don't save it as a cache,
            # but this setup will allow us to add new categories without bloating this command.
            models.TESTER: []
        }

        if (
            ctx.guild.id in cache_map[role_permissions]
            and len(cache_map[role_permissions][ctx.guild.id]) > 0
        ):
            embed.add_field(
                name=f"{role_permissions}s for {ctx.guild.name}",
                value=f"{' '.join([ctx.guild.get_role(role).mention for role in cache_map[role_permissions][ctx.guild.id]])}",
                inline=False
            )
        else:
            embed.add_field(
                name=f"No {role_permissions} roles for {ctx.guild.name}",
                value=f"Set up {role_permissions} roles with `{ctx.prefix}addverified`",
                inline=False
            )
        await ctx.send(embed=embed)

    @command_predicates.is_owner_or_admin()
    @commands.command(
        name="commonmemberguilds",
    )
    async def commonmemberguilds(
        self,
        ctx,
        guild_1: Union[nextcord.CategoryChannel, str],
        guild_2: Union[nextcord.CategoryChannel, str],
    ):
        """List all users in common between 2 guilds that the bot is in.

        Category : Admin or Bot Owner Roles only.
        See also : `~lsguilds`
        Usage: `~commonmemberguilds "Guild1" "Guild2"`
        """
        logging_utils.log_command(
            "commonmemberguilds", ctx.guild, ctx.channel, ctx.author
        )
        embed = discord_utils.create_embed()

        guild_1_guild = await discord_utils.find_guild(ctx, guild_1)

        guild_2_guild = await discord_utils.find_guild(ctx, guild_2)

        if guild_1_guild is None:
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"There is no guild named `{guild_1}`. Please double check the spelling.",
            )
            await ctx.send(embed=embed)
            return

        if guild_2_guild is None:
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"There is no guild named `{guild_2}`. Please double check the spelling.",
            )
            await ctx.send(embed=embed)
            return

        members_guild_1 = guild_1_guild.members
        members_guild_2 = guild_2_guild.members

        members_common = [
            member for member in members_guild_1 if member in members_guild_2
        ]

        if len(members_common) > 0:
            embed.add_field(
                name=f"Members common",
                value=f"Members common in `{guild_1}` and `{guild_2}`\n"
                f"{' '.join([member.mention for member in members_common])}",
                inline=False,
            )
        else:
            embed.add_field(
                name=f"No members in common",
                value=f"The bot has no members in common between `{guild_1}` and `{guild_2}`",
                inline=False,
            )
        await ctx.send(embed=embed)

    @command_predicates.is_owner_or_admin()
    @commands.command(
        name="lsguilds",
        aliases=["listguilds"],
    )
    async def lsguilds(self, ctx):
        """List all guilds that the bot is in.

        Category : Admin or Bot Owner Roles only.
        Usage: `~lsguilds`
        """
        logging_utils.log_command("lsguilds", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        guilds = ctx.bot.guilds

        if len(guilds) > 0:
            embed.add_field(
                name=f"Guilds for {ctx.bot.user.name}",
                value=f"Guilds for {ctx.bot.user.mention}\n"
                f"{' '.join(['`'+guild.name+'`' for guild in guilds])}",
                inline=False,
            )
        else:
            embed.add_field(
                name=f"No guilds for the bot",
                value="The bot is currently not in any guilds.",
                inline=False,
            )
        await ctx.send(embed=embed)

    @command_predicates.is_owner_or_admin()
    @commands.command(
        name="rmverified", aliases=["removeverified","removeverifieds","rmverifieds", "rmtrusted", "removetrusted"]
    )
    async def rmverified(self, ctx, role_or_rolename: Union[nextcord.Role, str], role_permissions: str = "Verified"):
        """Remove a role from the list of verifieds/trusteds. Only available to server admins or bot owners.
        May supply a role category (e.g. `Verified`, `Trusted`)

        Category : Admin or Bot Owner Roles only.
        Usage: `~rmverified @Verified`
        Usage: `~rmverified @Trusted Trusted`
        """
        logging_utils.log_command("rmverified", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        if role_permissions not in database.VERIFIED_CATEGORIES:
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"`role_permissions` must be in {', '.join(database.VERIFIED_CATEGORIES)}, "
                f"but you supplied {role_permissions}",
            )
            await ctx.send(embed=embed)
            return
        
        role_to_remove = None
        # Get role. Allow people to use the command by pinging the role, or just naming it
        if isinstance(role_or_rolename, nextcord.Role):
            role_to_remove = role_or_rolename
        else:
            # Search over all roles and see if we get a match.
            roles = await ctx.guild.fetch_roles()
            for role in roles:
                if role.name.lower() == role_or_rolename.lower():
                    role_to_remove = role
                    break
            if not role_to_remove:
                embed.add_field(
                    name=f"{constants.FAILED}",
                    value=f"Sorry, I can't find role {role_or_rolename}.",
                )
                await ctx.send(embed=embed)
                return

        with Session(database.DATABASE_ENGINE) as session:
            result = (
                session.query(database.Verifieds)
                .filter_by(server_id=ctx.guild.id, role_id_permissions=f"{role_to_remove.id}_{role_permissions}")
                .first()
            )
            if result is None:
                embed.add_field(
                    name=f"{constants.FAILED}",
                    value=f"Role {role_to_remove.mention} is not {role_permissions} in {ctx.guild.name}",
                )
                await ctx.send(embed=embed)
                return
            else:
                session.delete(result)
                session.commit()

        if (
            role_permissions == models.VERIFIED
            and role_to_remove.id in database.VERIFIEDS[ctx.guild.id]
        ):
            database.VERIFIEDS[ctx.guild.id].pop(
                database.VERIFIEDS[ctx.guild.id].index(role_to_remove.id)
            )
        elif (
            role_permissions == models.TRUSTED
            and role_to_remove.id in database.TRUSTEDS[ctx.guild.id]
        ):
            database.TRUSTEDS[ctx.guild.id].pop(
                database.TRUSTEDS[ctx.guild.id].index(role_to_remove.id)
            )

        embed.add_field(
            name=f"{constants.SUCCESS}",
            value=f"Removed {role_to_remove.mention} from {role_permissions} in {ctx.guild.name}",
        )
        await ctx.send(embed=embed)

    @command_predicates.is_owner_or_admin()
    @commands.command(name="setprefix")
    async def setprefix(self, ctx, prefix: str):
        """Sets the bot prefix for the server.

        Category : Admin or Bot Owner Roles only.
        Usage: `~setprefix !`
        """
        logging_utils.log_command("setprefix", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        with Session(database.DATABASE_ENGINE) as session:
            session.query(database.Prefixes).filter_by(server_id=ctx.guild.id).update(
                {"prefix": prefix}
            )
            session.commit()
        database.PREFIXES[ctx.message.guild.id] = prefix
        embed.add_field(
            name=constants.SUCCESS,
            value=f"Prefix for this server set to {prefix}",
            inline=False,
        )
        await ctx.send(embed=embed)

    @command_predicates.is_owner_or_admin()
    @commands.command(
        name="reloaddatabasecache", aliases=["reloaddbcache", "dbcachereload"]
    )
    async def reloaddatabasecache(self, ctx):
        """Reloads the custom command cache. This is useful when we're editing commands or playing with the Database.

        Category : Admin or Bot Owner Roles only.
        Usage: `~reloaddatabasecache`
        """
        logging_utils.log_command(
            "reloaddatabasecache", ctx.guild, ctx.channel, ctx.author
        )
        embed = discord_utils.create_embed()

        # Reset custom commands, verifieds, and prefixes for that server
        database.CUSTOM_COMMANDS[ctx.guild.id] = {}
        database.VERIFIEDS[ctx.guild.id] = []
        database.TRUSTEDS[ctx.guild.id] = []

        with Session(database.DATABASE_ENGINE) as session:
            custom_command_result = (
                session.query(database.CustomCommands)
                .filter_by(server_id=ctx.guild.id)
                .all()
            )
            if custom_command_result is not None:
                for custom_command in custom_command_result:
                    # Populate custom command dict
                    database.CUSTOM_COMMANDS[ctx.guild.id][
                        custom_command.command_name.lower()
                    ] = (custom_command.command_return, custom_command.image)
            embed.add_field(
                name=f"{constants.SUCCESS}",
                value="Successfully reloaded command cache.",
                inline=False,
            )

            verified_result = (
                session.query(database.Verifieds)
                .filter_by(server_id=ctx.guild.id)
                .all()
            )
            if verified_result is not None:
                for verified in verified_result:
                    if verified.permissions == models.VERIFIED:
                        database.VERIFIEDS[ctx.guild.id].append(verified.role_id)
                    elif verified.permissions == models.TRUSTED:
                        database.TRUSTEDS[ctx.guild.id].append(verified.role_id)
            embed.add_field(
                name=f"{constants.SUCCESS}!",
                value="Successfully reloaded verifieds cache.",
                inline=False,
            )

            prefix_result = (
                session.query(database.Prefixes)
                .filter_by(server_id=ctx.guild.id)
                .first()
            )
            if prefix_result is not None:
                database.PREFIXES[ctx.guild.id] = prefix_result.prefix
            else:
                database.PREFIXES[ctx.guild.id] = constants.DEFAULT_BOT_PREFIX
            embed.add_field(
                name=f"{constants.SUCCESS}!",
                value="Successfully reloaded prefixes cache.",
                inline=False,
            )

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(AdminCog(bot))
