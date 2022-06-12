from typing import Union

import nextcord
from emoji import EMOJI_ALIAS_UNICODE_ENGLISH as EMOJIS
from nextcord.ext import commands

import constants
from utils import command_predicates, discord_utils, logging_utils


class RoleManagementCog(commands.Cog, name="Role Management"):
    """Role Management Commands"""

    def __init__(self, bot):
        self.bot = bot

    #################
    # ROLE COMMANDS #
    #################

    @command_predicates.is_trusted()
    @commands.command(name="assignrole", aliases=["makerole", "createrole", "addrole"])
    async def assignrole(
        self,
        ctx,
        rolename: Union[nextcord.Role, nextcord.Member, str],
        *args: Union[nextcord.Member, str],
    ):
        """Assign a role to a list of users. If the role does not already exist, then creates the role.
        You may name the role or the users (nick or username) instead. Mentioning either is also guaranteed to work, but pings them.
        The role created is always mentionable by all users.

        Note that if the role is not already created, it cannot share name with a user. Use `~clonerole` or manually to create the role first.

        Permission Category : Trusted Roles only.
        Usage: `~assignrole "RoleName" "User3" "User2"`
        Usage: `~assignrole @RoleName here (Everyone who can see this channel, including BBN)`
        Usage: `~assignrole "NewRoleName" @User1`
        Usage: `~assignrole "NewRolename"` (if no users given, just creates the role)
        """
        logging_utils.log_command("assignrole", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        if isinstance(rolename, nextcord.Member):
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"Role name given is same as {rolename.mention}. Did you forget to specify a rolename?",
                inline=False,
            )
            await ctx.send(embed=embed)
            return

        role_to_assign = None
        if isinstance(rolename, str):
            roles = await ctx.guild.fetch_roles()
            for role in roles:
                if role.name.lower() == rolename.lower():
                    role_to_assign = role
                    break
        else:
            role_to_assign = rolename

        # Cannot find the role, so we'll make one
        if not role_to_assign:
            try:
                role_to_assign = await ctx.guild.create_role(name=rolename)
                await role_to_assign.edit(mentionable=True)
                embed.add_field(
                    name=f"Created role {rolename}",
                    value=f"Could not find role `{rolename}`, so I created it.",
                    inline=False,
                )
            except nextcord.Forbidden:
                embed.add_field(
                    name=f"{constants.FAILED}!",
                    value=f"I couldn't find role `{rolename}`, so I tried to make it. But I don't have "
                    f"permission to add a role in this server. Do I have the `add_roles` permission?",
                    inline=False,
                )
                await ctx.send(embed=embed)
                return

        if args[0] == "here":
            args = ctx.channel.members

        users_with_role_list = []
        for unclean_username in args:
            if isinstance(unclean_username, nextcord.Member):
                user = unclean_username
            else:
                embed.add_field(
                    name="Error Finding User!",
                    value=f"Could not find user `{unclean_username}`. Did you ping them? Raw usernames needs to be exact.",
                    inline=False,
                )
                continue
            # Assign the role
            if role_to_assign in user.roles:
                embed.add_field(
                    name="Error Assigning Role!",
                    value=f"{user.mention} already has {role_to_assign.mention} role. No need to assign.",
                    inline=False,
                )
            else:
                try:
                    await user.add_roles(role_to_assign)
                    users_with_role_list.append(user)
                except nextcord.Forbidden:
                    embed.add_field(
                        name="Error Assigning Role!",
                        value=f"I could not assign {role_to_assign.mention} to `{user.mention}`. Either this role is "
                        f"too high up on the roles list for them, or I do not have permissions to give "
                        f"them this role. Please ensure I have the `manage_roles` permission.",
                        inline=False,
                    )
        if len(users_with_role_list) < 1:
            embed.insert_field_at(
                0,
                name="Complete!",
                value=f"Did not assign role {role_to_assign.mention} to anyone.",
                inline=False,
            )
        else:
            embed.add_field(
                name=f"{constants.SUCCESS}!",
                value=f"Added the {role_to_assign.mention} role to {', '.join([user.mention for user in users_with_role_list])}",
                inline=False,
            )
        await ctx.send(embed=embed)

    @command_predicates.is_trusted()
    @commands.command(name="unassignrole", aliases=["removerole"])
    async def unassignrole(
        self,
        ctx,
        rolename: Union[nextcord.Role, str],
        *args: Union[nextcord.Member, str],
    ):
        """Unassigns a role from a list of users.
        To not ping them, you may name the role or the users (nick or username) instead. Mentioning either is also guaranteed to work.

        Permission Category : Trusted Roles only.
        Usage: `~unassignrole @RoleName @User1 @User2`
        Usage: `~unassignrole "RoleName" @User1`
        """
        logging_utils.log_command("unassignrole", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        role_to_unassign = None
        if isinstance(rolename, str):
            roles = await ctx.guild.fetch_roles()
            for role in roles:
                if role.name.lower() == rolename.lower():
                    role_to_unassign = role
                    break
        else:
            role_to_unassign = rolename

        if not role_to_unassign:
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"I can't find `{rolename}` in this server. Make sure you check the spelling and punctuation!",
                inline=False,
            )
            await ctx.send(embed=embed)
            return

        if len(args) < 1:
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"No users provided! You must give at least one user to unassign.",
                inline=False,
            )
            await ctx.send(embed=embed)
            return

        users_with_role_list = []
        for unclean_username in args:
            if isinstance(unclean_username, nextcord.Member):
                user = unclean_username
            else:
                embed.add_field(
                    name="Error Finding User!",
                    value=f"Could not find user `{unclean_username}`. Perhaps check your spelling or try mentioning the user instead.",
                    inline=False,
                )
                continue

            # Unassign the role
            try:
                if role_to_unassign not in user.roles:
                    embed.add_field(
                        name="Error Unassigning Role!",
                        value=f"{user.mention} does not have {role_to_unassign.mention} role to unassign.",
                        inline=False,
                    )
                else:
                    await user.remove_roles(role_to_unassign)
                    users_with_role_list.append(user)
            except nextcord.Forbidden:
                embed.add_field(
                    name="Error Unassigning Role!",
                    value=f"I could not unsassign {role_to_unassign.mention} from `{user.mention}`. Either this role is "
                    f"too high up on the roles list for them, or I do not have permissions to give "
                    f"them this role. Please ensure I have the `manage_roles` permission.",
                    inline=False,
                )
        if len(users_with_role_list) < 1:
            embed.insert_field_at(
                0,
                name="Complete!",
                value=f"Did not unassign role {role_to_unassign.mention} from anyone.",
                inline=False,
            )
        else:
            embed.add_field(
                name=f"{constants.SUCCESS}!",
                value=f"Removed the {role_to_unassign.mention} role from {', '.join([user.mention for user in users_with_role_list])}",
                inline=False,
            )
        await ctx.send(embed=embed)

    @command_predicates.is_trusted()
    @commands.command(name="clonerole", aliases=["syncrole"])
    async def clonerole(
        self,
        ctx,
        oldrole: Union[nextcord.Role, str],
        newrole: Union[nextcord.Role, str],
    ):
        """Clones a role to another role in the Server.
        If the role does not already exist, then creates the role, else just copies the permissions.

        This copies server-wide permissions but not Category specific ones. See `~clonecat` for that.
        This does not copy the colour of roles either.

        The role can be mentioned or named.

        Permission Category : Trusted Roles only.
        Usage: `~clonerole @RoleName "NewRoleName"`
        Usage: `~clonerole @RoleName @RoleName2`
        """
        logging_utils.log_command("clonerole", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        oldrole_as_role = None
        if isinstance(oldrole, str):
            roles = await ctx.guild.fetch_roles()
            for role in roles:
                if role.name.lower() == oldrole.lower():
                    oldrole_as_role = role
                    break
        else:
            oldrole_as_role = oldrole

        newrole_as_role = None
        if isinstance(newrole, str):
            roles = await ctx.guild.fetch_roles()
            for role in roles:
                if role.name.lower() == newrole.lower():
                    newrole_as_role = role
                    break
        else:
            newrole_as_role = newrole

        if not oldrole_as_role:
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"I couldn't find role `{oldrole}` to clone! Perhaps check your spelling and try again.",
                inline=False,
            )
            await ctx.send(embed=embed)
            return

        # Cannot find the role, so we'll make one
        if not newrole_as_role:
            try:
                newrole_as_role = await ctx.guild.create_role(
                    name=newrole,
                    permissions=oldrole_as_role.permissions,
                    hoist=oldrole_as_role.hoist,
                    mentionable=oldrole_as_role.mentionable,
                )

                embed.add_field(
                    name=f"{constants.SUCCESS}!",
                    value=f"Clone rolename {oldrole_as_role.mention} as {newrole_as_role.mention}.",
                    inline=False,
                )
            except nextcord.Forbidden:
                embed.add_field(
                    name=f"{constants.FAILED}!",
                    value=f"I tried to make `{newrole}`, but I don't have "
                    f"permission to add a role in this server. Do I have the `add_roles` permission?",
                    inline=False,
                )
                await ctx.send(embed=embed)
                return
        else:
            try:
                await newrole_as_role.edit(
                    permissions=oldrole_as_role.permissions,
                    hoist=oldrole_as_role.hoist,
                    mentionable=oldrole_as_role.mentionable,
                )
                embed.add_field(
                    name=f"{constants.SUCCESS}!",
                    value=f"{newrole_as_role.mention} already existed. Synced rolename {oldrole_as_role.mention}'s permissions in this server as {newrole_as_role.mention}.",
                    inline=False,
                )
            except nextcord.Forbidden:
                embed.add_field(
                    name=f"{constants.FAILED}!",
                    value=f"I tried to edit {newrole_as_role.mention}, but I don't have "
                    f"permission to edit a role in this server. Do I have the `manage_roles` permission?",
                    inline=False,
                )
                await ctx.send(embed=embed)
                return
        await ctx.send(embed=embed)

    @command_predicates.is_owner_or_admin()
    @commands.command(name="deleterole")
    async def deleterole(self, ctx, rolename: Union[nextcord.Role, str]):
        """Delete a role from the server

        Permission Category : Admin or Bot Owner only.
        Usage: `~deleterole "RoleName"`
        Usage: `~deleterole @RoleMention`
        """
        logging_utils.log_command("deleterole", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        role_to_delete = None
        if isinstance(rolename, nextcord.Role):
            role_to_delete = rolename
        # The input was not an int (i.e. the user gave the name of the role (e.g. ~deleterole rolename))
        else:
            # Search over all roles
            roles = await ctx.guild.fetch_roles()
            for role in roles:
                if role.name.lower() == rolename.lower():
                    role_to_delete = role
                    break
            if role_to_delete is None:
                embed.add_field(
                    name=f"{constants.FAILED}!",
                    value=f"I can't find `{rolename}` in this server. Make sure you check the spelling and punctuation!",
                    inline=False,
                )
                await ctx.send(embed=embed)
                return
        # Delete the role or error if it didn't work.
        try:
            role_name = role_to_delete.name
            await role_to_delete.delete()
            embed.add_field(
                name=f"{constants.SUCCESS}!",
                value=f"Removed role `{role_name}`",
                inline=False,
            )
            await ctx.send(embed=embed)
            return
        except nextcord.Forbidden:
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"I don't have permission to add or remove a role in this server. Do I have the `add_roles` permission?",
                inline=False,
            )
            await ctx.send(embed=embed)
            return

    @commands.command(name="listroles", aliases=["lsroles", "listrole", "lsrole"])
    async def listroles(self, ctx, rolename: Union[nextcord.Role, str] = ""):
        """List all roles in the server, or all users under a given role.

        Usage:`~listroles` (All roles in the server)
        Usage:`~listrole @RoleName` (List all users with role @RoleName)
        """
        logging_utils.log_command("listroles", ctx.guild, ctx.channel, ctx.author)
        embed = discord_utils.create_embed()

        if rolename == "":
            roles = await ctx.guild.fetch_roles()
            roles_sorted = sorted(roles, key=lambda x: x.position, reverse=True)
            rolestext = f"{', '.join([role.mention for role in roles_sorted])}"
            roles.sort(key=lambda x: x.position, reverse=True)
            embed.add_field(name=f"Roles in {ctx.guild.name}", value=rolestext)
            await ctx.send(embed=embed)
            return

        role_to_list = None
        if isinstance(rolename, nextcord.Role):
            role_to_list = rolename
        # The input was not an int (i.e. the user gave the name of the role (e.g. ~deleterole rolename))
        else:
            # Search over all roles
            roles = await ctx.guild.fetch_roles()
            for role in roles:
                if role.name.lower() == rolename.lower():
                    role_to_list = role
                    break
            if role_to_list is None:
                embed.add_field(
                    name=f"{constants.FAILED}!",
                    value=f"I can't find `{rolename}` in this server. Make sure you check the spelling and punctuation!",
                    inline=False,
                )
                await ctx.send(embed=embed)
                return

        allusers = f"{', '.join([user.mention for user in role_to_list.members])}"
        if allusers == "":
            allusers = "(This role has no members)"
        embed.add_field(
            name=f"Members in {role_to_list} = {len(role_to_list.members)}",
            value=allusers,
            inline=False,
        )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(RoleManagementCog(bot))
