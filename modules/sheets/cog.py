from utils import discord_utils, google_utils, logging_utils
from modules.sheets import sheets_constants
import modules.solved
import constants
from discord.ext import commands
import discord
import os
import gspread


class SheetsCog(commands.Cog, name="Sheets"):
    """A collection of commands for Google Sheests management"""
    def __init__(self, bot):
        self.bot = bot
        self.gspread_client = google_utils.create_gspread_client()
        self.category_tether_tab = self.gspread_client.open_by_key(os.getenv("MASTER_SHEET_KEY")).worksheet(sheets_constants.CATEGORY_TAB)

    @commands.command(name="addsheettether", aliases=["editsheettether", "tether", "edittether", "addtether"])
    @commands.has_any_role(*constants.VERIFIED)
    async def addsheettether(self, ctx, sheet_key_or_link: str = None):
        """Add a sheet to the current channel's category"""
        logging_utils.log_command("addsheettether", ctx.channel, ctx.author)

        # Get category information
        curr_cat = ctx.message.channel.category.name
        curr_cat_id = str(ctx.message.channel.category_id)
        curr_guild = ctx.guild.name

        proposed_sheet = self.addsheettethergeneric(sheet_key_or_link, curr_guild, curr_cat, curr_cat_id)

        if proposed_sheet:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"{constants.SUCCESS}!",
                            value=f"The category **{curr_cat}** is now tethered to the "
                                  f"[Google sheet at link]({proposed_sheet.url})",
                            inline=False)
            await ctx.send(embed=embed)
        # If we can't open the sheet, send an error and return
        else:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"{constants.FAILED}!",
                            value=f"Sorry, we can't find a sheet there. "
                                  f"Did you forget to set your sheet as 'Anyone with the link can edit'?",
                            inline=False)
            await ctx.send(embed=embed)
            return

    @commands.command(name="addchannelsheettether",
                      aliases=["editchannelsheettether",
                               "channeltether",
                               "editchanneltether",
                               "addchanneltether",
                               "chantether"])
    @commands.has_any_role(*constants.VERIFIED)
    async def addchannelsheettether(self, ctx, sheet_key_or_link: str):
        """Add a sheet to the current channel"""
        logging_utils.log_command("addchannelsheettether", ctx.channel, ctx.author)

        # Get channel information
        curr_chan = str(ctx.message.channel)
        curr_chan_id = str(ctx.message.channel.id)
        curr_guild = str(ctx.guild)

        proposed_sheet = self.addsheettethergeneric(sheet_key_or_link, curr_guild, curr_chan, curr_chan_id)

        if proposed_sheet:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"Successful",
                            value=f"The channel **{curr_chan}** is now tethered to the "
                                  f"[Google sheet at link]({proposed_sheet.url})",
                            inline=False)
            await ctx.send(embed=embed)
        # If we can't open the sheet, send an error and return
        else:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"{constants.FAILED}!",
                            value=f"Sorry, we can't find a sheet there. "
                                  f"Did you forget to set your sheet as 'Anyone with the link can edit'?",
                            inline=False)
            await ctx.send(embed=embed)
            return

    @commands.command(name="removesheettether", aliases=["deletetether", "removetether"])
    @commands.has_any_role(*constants.VERIFIED)
    async def removesheettether(self, ctx):
        """Remove the sheet-category tethering"""
        logging_utils.log_command("removesheettether", ctx.channel, ctx.author)
        # Get category and channel information
        curr_cat = ctx.message.channel.category.name
        curr_cat_id = str(ctx.message.channel.category_id)
        curr_chan = ctx.message.channel.name
        curr_chan_id = str(ctx.message.channel.id)

        curr_chan_or_cat_cell = self.findsheettether(curr_chan_id, curr_cat_id)

        # If the tethering exists, remove it from the sheet.
        if curr_chan_or_cat_cell:
            curr_sheet_link = self.category_tether_tab.cell(curr_chan_or_cat_cell.row, curr_chan_or_cat_cell.col + 2).value
            self.category_tether_tab.delete_row(curr_chan_or_cat_cell.row)
            embed = discord_utils.create_embed()
            embed.add_field(name=f"{constants.SUCCESS}",
                            value=f"The channel tether to [sheet]({curr_sheet_link}) has been removed!",
                            inline=False)
            await ctx.send(embed=embed)
        else:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"{constants.FAILED}",
                            value=f"The category **{curr_cat}** or the channel **{curr_chan}** "
                                  f"are not tethered to any Google sheet.",
                            inline=False)
            await ctx.send(embed=embed)
            return

    @commands.command(name="channelsheetcreatetab",
                      aliases=["channelsheetcrab",
                               "cheetcrab",
                               "chancrab"])
    @commands.has_any_role(*constants.VERIFIED)
    async def channelsheetcreatetab(self, ctx, chan_name: str, *args):
        """
        Create a new channel,
        then a New tab on the sheet that is currently tethered to this category,
        then pins things"""
        logging_utils.log_command("channelsheetcreatetab", ctx.channel, ctx.author)
        embed = discord_utils.create_embed()
        # Cannot make a new channel if the category is full
        if discord_utils.category_is_full(ctx.channel.category):
            embed.add_field(name=f"{constants.FAILED}!",
                            value=f"Category `{ctx.channel.category.name}` is already full, max limit is 50 channels.")
            # reply to user
            await ctx.send(embed=embed)
            return
        # new channel created (or None)
        new_chan = await discord_utils.createchannelgeneric(ctx.guild, ctx.channel.category, chan_name)
        # Error creating channel
        if not new_chan:
            embed.add_field(name=f"{constants.FAILED}!",
                            value=f"Forbidden! Have you checked if the bot has the required permisisons?")
            await ctx.send(embed=embed)
            return

        to_pin = []
        for s in args:
            to_pin.append(str(s))

        tab_name = chan_name.replace("#", "").replace("-", " ")

        # Get category and channel information
        curr_cat_id = str(ctx.message.channel.category_id)
        curr_chan_id = str(ctx.message.channel.id)

        curr_sheet_link, newsheet = await self.sheetcreatetabgeneric(ctx, ctx.channel, ctx.channel.category, tab_name)

        # Error, already being handled at the generic function
        if not curr_sheet_link or not newsheet or not newsheet.id:
            return

        # This link is customized for the newly made tab
        final_sheet_link = curr_sheet_link + "/edit#gid=" + str(newsheet.id)

        try:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"Success!",
                            value=f"Tab **{tab_name}** has been created at [Tab link]({final_sheet_link}).",
                            inline=False)
            msg = await new_chan.send(embed=embed)
            await msg.pin()

            for s in to_pin:
                embed = discord.Embed(description=s)
                msg = await new_chan.send(embed=embed)
                await msg.pin()
        except Exception:
            return

        embed = discord_utils.create_embed()
        embed.add_field(name=f"Success!",
                         value=f"Channel `{chan_name}` created as {new_chan.mention}, posts pinned!",
                         inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="chancrabsorted", aliases=["chancrabs"])
    @commands.has_any_role(*constants.VERIFIED)
    async def channelsheetcreatetabsorted(self, ctx: commands.context):
        await self.channelsheetcreatetab(ctx)
        #TODO : Move modules.solved.reorderchannels (or maybe sort_channels) to discord_utils then call here
        #await self.reorderchannels(ctx)

    @commands.command(name="displaysheettether", aliases=["showsheettether", "showtether", "displaytether"])
    @commands.has_any_role(*constants.VERIFIED)
    async def displaysheettether(self, ctx):
        """Find the sheet the category is current tethered too"""
        logging_utils.log_command("displaysheettether", ctx.channel, ctx.author)
        # Get category information
        curr_cat = str(ctx.message.channel.category)
        curr_cat_id = str(ctx.message.channel.category_id)
        curr_chan = str(ctx.message.channel)
        curr_chan_id = str(ctx.message.channel.id)

        curr_chan_cell = self.findsheettether(curr_chan_id, curr_cat_id)

        if curr_chan_cell:
            curr_sheet_link = self.category_tether_tab.cell(curr_chan_cell.row, curr_chan_cell.col + 2).value
            embed = discord_utils.create_embed()
            embed.add_field(name=f"Result",
                            value=f"The channel **{curr_chan}** is currently tethered to the "
                                  f"[Google sheet at link]({curr_sheet_link})",
                            inline=False)
            await ctx.send(embed=embed)
        else:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"Error",
                            value=f"Neither the category **{curr_cat}** nor the channel **{curr_chan}** "
                                  f"are tethered to any Google sheet.",
                            inline=False)
            await ctx.send(embed=embed)
            return

    @commands.command(name="sheetcreatetab", aliases=["sheettab", "sheetcrab"])
    @commands.has_any_role(*constants.VERIFIED)
    async def sheetcreatetab(self, ctx, *args):
        """Create a New tab on the sheet that is currently tethered to this category"""
        logging_utils.log_command("sheetcreatetab", ctx.channel, ctx.author)
        if len(args) < 1:
            embed = discord_utils.create_no_argument_embed("Tab Name")
            await ctx.send(embed=embed)
            return

        tab_name = " ".join(args)

        curr_chan = ctx.messsage.channel
        curr_cat = ctx.message.channel.category
        curr_sheet_link, newsheet = await self.sheetcreatetabgeneric(ctx, curr_chan, curr_cat, tab_name)

        # Error, already being handled at the generic function
        if not curr_sheet_link or not newsheet.id:
            return

        # This link is customized for the newly made tab
        final_sheet_link = curr_sheet_link + "/edit#gid=" + str(newsheet.id)

        embed = discord_utils.create_embed()
        embed.add_field(name=f"Success!",
                         value=f"Tab **{tab_name}** has been created at [Tab link]({final_sheet_link}).",
                         inline=False)
        msg = await ctx.send(embed=embed)
        await msg.pin()

    def addsheettethergeneric(self, sheet_key_or_link, curr_guild, curr_catorchan, curr_catorchan_id) -> gspread.Spreadsheet:
        """Add a sheet to the current channel"""
        # We accept both sheet keys or full links
        proposed_sheet = self.get_sheet_from_key_or_link(sheet_key_or_link)
        # If we can't open the sheet, send an error and return
        if not proposed_sheet:
            return None

        # If the channel already has a sheet, then we update it.
        # Otherwise, we add the channel to our master sheet to establish the tether
        try:
            # Search first column for the channel
            curr_catorchan_cell = self.category_tether_tab.find(curr_catorchan_id, in_column=1)
            #TODO: Lock sheet?
            # Prepare Row and update values
            row_vals = [[curr_catorchan_id, curr_guild + " - " + curr_catorchan, proposed_sheet.url]]
            rownum = "A" + str(curr_catorchan_cell.row) + ":C" + str(curr_catorchan_cell.row)
            self.category_tether_tab.update(rownum, row_vals)
        except gspread.exceptions.CellNotFound:
            # Cell isn't found, so we add a new row to the sheet to establish the tether
            values = [curr_catorchan_id, curr_guild + " - " + curr_catorchan, proposed_sheet.url]
            self.category_tether_tab.append_row(values)
        return proposed_sheet

    def findsheettether(self, curr_chan_id, curr_cat_id):
        """For finding the appropriate sheet tethering for a given category or channel"""
        curr_chan_or_cat_cell = None
        try:
            # Search first column for the channel
            curr_chan_or_cat_cell = self.category_tether_tab.find(curr_chan_id, in_column=1)
        except gspread.exceptions.CellNotFound:
            # If there is no tether for the specific channel, check if there is one for the category.
            try:
                # Search first column for the category
                curr_chan_or_cat_cell = self.category_tether_tab.find(curr_cat_id, in_column=1)
            except gspread.exceptions.CellNotFound:
                pass

        return curr_chan_or_cat_cell

    def get_sheet_from_key_or_link(self, sheet_key_or_link: str) -> gspread.Spreadsheet:
        """Takes in a string, which could be a google sheet key or URL"""
        # Assume the str is a URL
        try:
            sheet = self.gspread_client.open_by_url(sheet_key_or_link)
            return sheet
        except gspread.exceptions.APIError:
            return None
        # Given str was not a link
        except gspread.exceptions.NoValidUrlKeyFound:
            pass
        # Assume the str is a sheet key
        try:
            sheet = self.gspread_client.open_by_key(sheet_key_or_link)
            return sheet
        # Entity Not Found
        except gspread.exceptions.APIError:
            return None

    async def sheetcreatetabgeneric(self, ctx, curr_chan, curr_cat, tab_name):
        """Actually creates the sheet and handles errors"""
        curr_sheet_link = None
        newsheet = None

        curr_chan_or_cat_cell = self.findsheettether(str(curr_chan.id), str(curr_cat.id))

        if curr_chan_or_cat_cell:
            curr_sheet_link = self.category_tether_tab.cell(curr_chan_or_cat_cell.row, curr_chan_or_cat_cell.col + 2).value
        else:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"Error",
                            value=f"The category **{curr_cat.name}** or the channel **{curr_chan.name}** are not "
                                  f"tethered to any Google sheet.",
                            inline=False)
            await ctx.send(embed=embed)
            return curr_sheet_link, newsheet

        # Make sure the template tab exists on the sheet.
        try:
            curr_sheet = self.gspread_client.open_by_url(curr_sheet_link)
            template_id = curr_sheet.worksheet("Template").id
        # Error when we can't open the curr sheet link
        except gspread.exceptions.APIError:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"Error",
                            value=f"I'm unable to open the tethered [sheet]({curr_sheet_link}). "
                                  f"Did the permissions change?",
                            inline=False)
            await ctx.send(embed=embed)
            return curr_sheet_link, newsheet
        # Error when the sheet has no template tab
        except gspread.exceptions.WorksheetNotFound:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"Error",
                            value=f"The [sheet]({curr_sheet_link}) has no tab named 'Template'. "
                                  f"Did you forget to add one?",
                            inline=False)
            await ctx.send(embed=embed)
            return curr_sheet_link, newsheet
        # Make sure tab_name does not exist
        try:
            curr_sheet.worksheet(tab_name)
            # If there is a tab with the given name, that's an error!
            embed = discord_utils.create_embed()
            embed.add_field(name=f"Error",
                            value=f"The [Google sheet at link]({curr_sheet_link}) already has a tab named "
                                  f"**{tab_name}**. Cannot create a tab with same name.",
                            inline=False)
            await ctx.send(embed=embed)
            return curr_sheet_link, newsheet
        except gspread.exceptions.WorksheetNotFound:
            # If the tab isn't found, that's good! We will create one.
            pass

        # Try to duplicate the template tab and rename it to the given name
        try:
            # Index of 4 is hardcoded for Team Arithmancy server
            newsheet = curr_sheet.duplicate_sheet(source_sheet_id=template_id,
                                                  new_sheet_name=tab_name,
                                                  insert_sheet_index=4)
        except gspread.exceptions.APIError:
            embed = discord_utils.create_embed()
            embed.add_field(name=f"Error",
                            value=f"Could not duplicate 'Template' tab in the "
                                  f"[Google sheet at link]({curr_sheet_link}). "
                                  f"Is the permission set up with 'Anyone with link can edit'?",
                            inline=False)
            await ctx.send(embed=embed)
            return curr_sheet_link, None

        return curr_sheet_link, newsheet

def setup(bot):
    bot.add_cog(SheetsCog(bot))
