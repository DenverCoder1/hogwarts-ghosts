import asyncio
import copy
from typing import Optional

import nextcord
from nextcord.ext import application_checks, commands

import constants
from utils import discord_utils, logging_utils

from .create_channel import CreateChannelView
from .select_category import SelectCategoryView


async def _autocomplete_categories(_, interaction: nextcord.Interaction, input: str):
    """
    Autocomplete categories for the interaction.
    """
    categories = interaction.guild.categories if interaction.guild else []
    category_names = [c.name for c in categories]
    if input:
        category_names = [c for c in category_names if c.lower().startswith(input.lower())]
    await interaction.response.send_autocomplete(category_names)


class ConfessionalRequest(commands.Cog, name="Confessional Request"):
    """Channel request button system"""

    def __init__(self, bot: commands.Bot):
        self._bot = bot
        self._persistent_view_added = False
        self.BUTTON_TEXT = "Create Confessional Channel"
        self.EMBED_TITLE_SUFFIX = " Channel Request"

    @commands.Cog.listener()
    async def on_ready(self):
        if not self._persistent_view_added:
            self._persistent_view_added = True
            button_view = CreateChannelView(self.BUTTON_TEXT, self.EMBED_TITLE_SUFFIX)
            self._bot.add_view(button_view)

    @commands.command(name="ticketbtn", aliases=["ticketbutton", "ticket"])
    @commands.has_permissions(administrator=True)
    async def ticketbtn(self, ctx: commands.Context):
        """Creates a button for creating a confessional channel"""
        if ctx.guild is None:
            return await ctx.send("This command can only be used in a server")
        logging_utils.log_command("ticketbtn", ctx.guild, ctx.channel, ctx.author)
        # prompt for a category
        category_view = SelectCategoryView(categories=ctx.guild.categories, ctx=ctx)
        category_msg = await ctx.reply(f"Please select a category", view=category_view)
        await category_view.wait()
        category = category_view.dropdown.selected_category
        await category_msg.delete()
        if category is None:
            return await ctx.send("No category selected", delete_after=3)
        # create the button view
        button_view = CreateChannelView(
            label=self.BUTTON_TEXT,
            title_suffix=self.EMBED_TITLE_SUFFIX,
            ctx=ctx,
        )
        embed = nextcord.Embed(
            title=f"{category.name}{self.EMBED_TITLE_SUFFIX}",
            description=f'If you want to write confessionals in {category.name}, click "{self.BUTTON_TEXT}" below. This will make a private confessional channel for you where spectators and dead players can read your thoughts!',
            color=0x009999,
        )
        await ctx.send(embed=embed, view=button_view)
        await ctx.message.delete()

    @commands.command(name="close")
    @commands.has_permissions(administrator=True)
    async def close(self, ctx: commands.Context):
        """Archives and closes the channel that the user is currently in"""
        # check that the topic is a user mention
        logging_utils.log_command("close", ctx.guild, ctx.channel, ctx.author)
        ticket_channel = ctx.channel
        if not getattr(ticket_channel, "topic", "").startswith("<@"):
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value="You are not in a confessional channel",
            )
            return await ctx.send(embed=embed)
        assert ctx.guild is not None
        assert isinstance(ticket_channel, nextcord.TextChannel)
        archivechannel_cmd = self._bot.get_command("archivechannel")
        assert isinstance(archivechannel_cmd, commands.Command)
        archives_channel = nextcord.utils.find(
            lambda c: c.name == f"channel-archives", ctx.guild.text_channels
        )
        if archives_channel is None:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value="#channel-archives channel was not found",
            )
            return await ctx.send(embed=embed)
        embed = discord_utils.create_embed()
        embed.add_field(name=f"Archiving in progress", value=f"This may take a while.")
        progress_msg = await ctx.send(embed=embed)
        # create a context where the message is the last message in the archive channel
        fake_ctx = copy.copy(ctx)
        fake_ctx.channel = archives_channel  # type: ignore
        # execute "~archivechannel #<ticket-channel>"
        archive_message: Optional[nextcord.Message] = await archivechannel_cmd(
            fake_ctx, ticket_channel
        )
        # check that the new last message contains the attachment
        if archive_message is None and archives_channel.last_message is not None:
            archive_message = archives_channel.last_message
        if archive_message is None and archives_channel.last_message_id is not None:
            archive_message = await archives_channel.fetch_message(archives_channel.last_message_id)
        # failure to archive the channel
        if not archive_message or not archive_message.attachments or archive_message.embeds:
            print(
                "The channel was not archived properly. "
                f"{archive_message} {archive_message.attachments} {archive_message.embeds}"
            )
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}",
                value=f"The channel was not archived properly. See {archives_channel.mention} for more information.",
            )
            await progress_msg.edit(embed=embed)
            await ctx.send(
                f"{ticket_channel.topic}, this channel may have too many attachments! "
                "Please let us know when your attachments have been saved so we can delete your channel."
            )
            return
        # successfuly archived the channel
        embed = discord_utils.create_embed()
        embed.add_field(
            name=f"{constants.SUCCESS}",
            value=f"The channel has been archived and will now be deleted.",
        )
        await progress_msg.edit(embed=embed)
        # send a message in the #mod-log channel
        mod_log_channel = nextcord.utils.find(
            lambda c: c.name == "mod-log", ctx.guild.text_channels
        )
        if mod_log_channel is not None:
            embed = nextcord.Embed(
                title="Confessional channel closed",
                description=f"#{ticket_channel.name} by {ticket_channel.topic} has been archived and deleted by {ctx.author.mention}",
                color=0x009999,
            )
            embed.set_author(
                name=str(ctx.author),
                icon_url=ctx.author.display_avatar.url,
            )
            embed.set_footer(text=f"ID: {ctx.author.id}")
            embed.timestamp = nextcord.utils.utcnow()
            await mod_log_channel.send(embed=embed)
        # delete the channel
        await asyncio.sleep(2)
        await ticket_channel.delete()

    @commands.command(name="sortcategory", aliases=["sortcat"])
    @commands.has_permissions(manage_channels=True)
    async def sortcategory(self, ctx: commands.Context, category_name: str):
        logging_utils.log_command("sortcategory", ctx.guild, ctx.channel, ctx.author)

        category = await discord_utils.find_category(ctx, category_name)

        if category is None:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"Could not find category `{category_name}`",
            )
            # reply to user
            await ctx.send(embed=embed)
            return

        if discord_utils.category_is_sorted(category):
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.SUCCESS}!",
                value=f"Category `{category_name}` is already sorted",
            )
            # reply to user
            await ctx.send(embed=embed)
            return

        embed = discord_utils.create_embed()
        embed.add_field(
            name=f"Sorting in progress",
            value=f"This may take a few seconds.",
        )
        response = await ctx.send(embed=embed)

        await discord_utils.sort_category(category)

        if not discord_utils.category_is_sorted(category):
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"Sorting of category `{category_name}` failed. Please try again.",
            )
            await response.edit(embed=embed)
            return

        embed = discord_utils.create_embed()
        embed.add_field(
            name=f"{constants.SUCCESS}",
            value=f"Sorted category `{category.name}`",
        )
        await response.edit(embed=embed)

    @nextcord.slash_command()
    async def phase(
        self,
        interaction: nextcord.Interaction,
        category_name: str = nextcord.SlashOption(
            name="category", autocomplete_callback=_autocomplete_categories
        ),
        image: nextcord.Attachment = nextcord.SlashOption(),
    ):
        """Send a phase image to all channels in a given category.

        Arguments:
            category_name: The name of the category to send the phase image to.
            image: The image to send.
        """
        await interaction.response.defer()

        ctx: commands.Context = discord_utils.interaction_to_fake_ctx(interaction)  # type: ignore

        logging_utils.log_command("/phase", ctx.guild, ctx.channel, ctx.author)  # type: ignore

        category = await discord_utils.find_category(ctx, category_name)  # type: ignore

        if category is None:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"Could not find category `{category_name}`",
            )
            # reply to user
            await interaction.send(embed=embed)
            return

        if not category.text_channels:
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.SUCCESS}!",
                value=f"Category `{category_name}` has no channels to send to",
            )
            # reply to user
            await interaction.send(embed=embed)
            return

        if not isinstance(interaction.channel, nextcord.TextChannel) or not isinstance(
            interaction.user, nextcord.Member
        ):
            embed = discord_utils.create_embed()
            embed.add_field(
                name=f"{constants.FAILED}!",
                value=f"An error occurred with the channel or user",
            )
            # reply to user
            await interaction.send(embed=embed)
            return

        for channel in category.text_channels:
            if not channel.permissions_for(interaction.user).send_messages:
                embed = discord_utils.create_embed()
                embed.add_field(
                    name=f"{constants.FAILED}!",
                    value=f"You do not have permission to send messages in {channel.mention}",
                )
                # reply to user
                await interaction.send(embed=embed)

            try:
                await channel.send(content=image.url)
            except nextcord.HTTPException:
                embed = discord_utils.create_embed()
                embed.add_field(
                    name=f"{constants.FAILED}!",
                    value=f"The bot could not send the image to {channel.mention}",
                )
                # reply to user
                await interaction.send(embed=embed)
                return

        embed = discord_utils.create_embed()
        embed.add_field(
            name=f"{constants.SUCCESS}!",
            value=f"Sent the image to all channels in {category_name}",
        )
        # reply to user
        await interaction.send(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(ConfessionalRequest(bot))
