from dotenv.main import load_dotenv

load_dotenv(override=True)
import os
import nextcord
from nextcord.ext import commands
import constants
import sqlalchemy
from sqlalchemy import insert
from sqlalchemy.orm import Session
import database


def get_prefix(client, message):
    """Gets prefix for the bot"""
    # Check if in new server or DM
    if message.guild is not None and message.guild.id in database.PREFIXES:
        return database.PREFIXES[message.guild.id]
    else:
        return constants.DEFAULT_BOT_PREFIX


def main():
    activity = nextcord.Activity(
        type=nextcord.ActivityType.listening, name="confessionals"
    )
    intents = nextcord.Intents.default()
    intents.members = True
    intents.message_content = True
    client = commands.Bot(
        command_prefix=get_prefix,
        intents=intents,
        help_command=None,
        case_insensitive=True,
        activity=activity,
    )

    # Get the modules of all cogs whose directory structure is modules/<module_name>/cog.py
    for folder in os.listdir("modules"):
        if os.path.exists(os.path.join("modules", folder, "cog.py")):
            client.load_extension(f"modules.{folder}.cog")

    @client.event
    async def on_ready():
        """When the bot starts up"""
        for guild in client.guilds:
            if guild.id not in database.PREFIXES:
                database.PREFIXES[guild.id] = constants.DEFAULT_BOT_PREFIX
                # Add default prefix to DB
                with Session(database.DATABASE_ENGINE) as session:
                    stmt = sqlalchemy.insert(database.Prefixes).values(
                        server_id=guild.id,
                        server_name=guild.name,
                        prefix=constants.DEFAULT_BOT_PREFIX,
                    )
                    session.execute(stmt)
                    session.commit()
            print(
                f"{client.user.name} has connected to the following guild: "
                f"{guild.name} (id: {guild.id}) with prefix {database.PREFIXES[guild.id]}"
            )
            # Make sure there are at least empty entries for VERIFIEDS, and CUSTOM_COMMANDS for every guild we're in
            if guild.id not in database.VERIFIEDS:
                database.VERIFIEDS[guild.id] = []
            if guild.id not in database.TRUSTEDS:
                database.TRUSTEDS[guild.id] = []
            if guild.id not in database.SOLVERS:
                database.SOLVERS[guild.id] = []
            if guild.id not in database.TESTERS:
                database.TESTERS[guild.id] = []
            if guild.id not in database.CUSTOM_COMMANDS:
                database.CUSTOM_COMMANDS[guild.id] = {}
        # Populate default command list
        for command in client.commands:
            constants.DEFAULT_COMMANDS.append(command.qualified_name.lower())
            for alias in command.aliases:
                constants.DEFAULT_COMMANDS.append(alias.lower())

    @client.event
    async def on_guild_join(guild: nextcord.Guild):
        """When the bot joins a new guild, add it to the database for prefixes"""
        print(f"Joining {guild} -- Hi!")
        with Session(database.DATABASE_ENGINE) as session:
            stmt = insert(database.Prefixes).values(
                server_id=guild.id,
                server_name=guild.name,
                prefix=constants.DEFAULT_BOT_PREFIX,
            )
            session.execute(stmt)
            session.commit()
        database.PREFIXES[guild.id] = constants.DEFAULT_BOT_PREFIX
        database.VERIFIEDS[guild.id] = []
        database.TRUSTEDS[guild.id] = []
        database.SOLVERS[guild.id] = []
        database.TESTERS[guild.id] = []
        database.CUSTOM_COMMANDS[guild.id] = {}

    @client.event
    async def on_guild_remove(guild: nextcord.Guild):
        """When the bot leaves a guild, remove all database entries pertaining to that guild"""
        print(f"Leaving {guild} -- Bye bye!")
        with Session(database.DATABASE_ENGINE) as session:
            session.query(database.CustomCommands).filter_by(
                server_id=guild.id
            ).delete()
            session.commit()
            session.query(database.Prefixes).filter_by(server_id=guild.id).delete()
            session.commit()
            session.query(database.Verifieds).filter_by(server_id=guild.id).delete()
            session.commit()
            session.query(database.SheetTethers).filter_by(server_id=guild.id).delete()
            session.commit()
        database.PREFIXES.pop(guild.id)
        database.VERIFIEDS.pop(guild.id)
        database.TRUSTEDS.pop(guild.id)
        database.CUSTOM_COMMANDS.pop(guild.id)

    @client.event
    async def on_message(message: nextcord.Message):
        # We only want to respond to user messages
        if message.is_system() or message.author.id == client.user.id:
            return

        command_prefix = get_prefix(client, message)

        if message.clean_content.startswith(command_prefix):
            # If the command is a default one, just run it.
            command_name = message.clean_content.split()[0][
                len(command_prefix) :
            ].lower()
            if command_name in constants.DEFAULT_COMMANDS:
                await client.process_commands(message)
            # Don't use custom commands for DMs also I think this fixes a bug which gets an error when someone
            # uses a command right as the box is starting up.
            elif (
                message.guild is not None
                and message.guild.id in database.CUSTOM_COMMANDS
            ):
                command_return = None
                # check if custom command is in cache for that server
                if command_name in [
                    command.lower()
                    for command in database.CUSTOM_COMMANDS[message.guild.id].keys()
                ]:
                    command_return = database.CUSTOM_COMMANDS[message.guild.id][
                        command_name
                    ][0]

                # Command found in cache
                if command_return is not None:
                    # Image, so we use normal text.
                    if database.CUSTOM_COMMANDS[message.guild.id][command_name][1]:
                        await message.channel.send(command_return)
                    # Non-Image, so use embed.
                    else:
                        embed = nextcord.Embed(
                            description=command_return, color=constants.EMBED_COLOR
                        )
                        await message.channel.send(embed=embed)
                    return

                # The custom command is not in the cache
                # Query the DB to see if we have a command with that name
                with Session(database.DATABASE_ENGINE) as session:
                    # Checking for this server
                    result = (
                        session.query(database.CustomCommands)
                        .filter_by(
                            server_id_command=f"{message.guild.id} {command_name}"
                        )
                        .first()
                    )
                    # Check for global custom commands
                    if result is None:
                        result = (
                            session.query(database.CustomCommands)
                            .filter_by(
                                server_id_command=f"{constants.DB_GLOBAL} {command_name}"
                            )
                            .first()
                        )
                    if result is not None:
                        if result.image:
                            await message.channel.send(result.command_return)
                            return
                        else:
                            embed = nextcord.Embed(
                                description=result.command_return,
                                color=constants.EMBED_COLOR,
                            )
                            await message.channel.send(embed=embed)
                        # Adds to cache. NOTE - This adds to cache even if local or global
                        database.CUSTOM_COMMANDS[message.guild.id][command_name] = (
                            result.command_return,
                            result.image,
                        )

    client.run(os.getenv("DISCORD_TOKEN"))


if __name__ == "__main__":
    main()
