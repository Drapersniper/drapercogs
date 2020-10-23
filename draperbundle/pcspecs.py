# -*- coding: utf-8 -*-

import logging
from copy import copy
from operator import itemgetter

import discord
import regex
from discord.ext.commands.converter import Greedy
from redbot.core import commands
from redbot.core.utils.menus import DEFAULT_CONTROLS, menu

from .config_holder import ConfigHolder
from .constants import REPLACE_BRACKER
from .utilities import (
    get_all_user_rigs,
    get_date_time,
    get_date_string,
    get_member_activity,
)

__updated__ = "27-04-2019"

logger = logging.getLogger("red.drapercogs.pc_specs")


class PCSpecs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = ConfigHolder.PCSpecs

    @commands.group()
    async def specs(self, ctx: commands.Context):
        """Rig management"""

    @specs.group(name="show", invoke_without_command=True)
    async def _specs_show(self, ctx, *, show_all: str = None):  # @ReservedAssignment
        """Shows your info"""
        if ctx.invoked_subcommand is None:
            if show_all and show_all == "all":
                data = await get_all_user_rigs(
                    ctx.guild,
                    pm=False
                    if not isinstance(ctx.channel, discord.DMChannel)
                    else True,
                )
                if data:
                    discord_names = ""
                    embed_list = []
                    for rig_data, _, mention, _ in sorted(data, key=itemgetter(3, 1)):
                        if rig_data and mention:
                            if len(discord_names + f"{mention}\n") > 1000:
                                embed = discord.Embed(title=f"Users with a rig profile")
                                embed.add_field(
                                    name=f"Discord ID", value=discord_names, inline=True
                                )
                                embed_list.append(embed)
                                discord_names = ""
                            discord_names += f"{mention}\n"
                    if discord_names:
                        embed = discord.Embed(title=f"Users with a rig profile")
                        embed.add_field(
                            name=f"Discord ID", value=discord_names, inline=True
                        )
                        embed_list.append(embed)
                    # await embeder.send_webhook(embeds=embed_list)
                    await menu(
                        ctx,
                        pages=embed_list,
                        controls=DEFAULT_CONTROLS,
                        message=None,
                        page=0,
                        timeout=60,
                    )
                    embed_list = []
                else:
                    return await ctx.send("No one here has a rig profile with me")
            elif not show_all:
                embed = await self._get_member_rig(ctx, ctx.author)
                if embed:
                    await ctx.send(embed=embed)
            else:
                return await ctx.send_help()

    @_specs_show.command(name="member")
    async def _show_member(self, ctx, members: Greedy[discord.Member]):
        """Show Rig Data for multiple Members"""
        if members:
            embed_list = []
            members = list(set(members))
            for member in members:
                if member is None:
                    continue
                embed = None
                embed = await self._get_member_rig(ctx, member)
                if embed and isinstance(embed, discord.Embed):
                    embed_list.append(embed)
            if embed_list:
                await menu(ctx, embed_list, DEFAULT_CONTROLS)

    @specs.command(name="add")
    async def _specs_add(self, ctx: commands.Context):
        """Add your rig specs to your profile"""
        try:
            member = ctx.guild.get_member(ctx.author.id)
            rig_data = await self.config.user(member).rig.get_raw()
            rig_data_new = await self.update_rig(rig_data, ctx.author)
            rig_group = self.config.user(member)
            async with rig_group.rig() as rigs_data:
                for component, value in rig_data_new.items():
                    ring_component = {component: value}
                    rigs_data.update(ring_component)
            await ctx.author.send("I've updated your rig data")
        except discord.Forbidden:
            return await ctx.send(f"I can't DM you, {ctx.author.mention}")

    @specs.command(name="remove")
    async def _specs_remove(self, ctx: commands.Context, *, component: str):
        """Remove a component from your rig profile"""
        component_user = component
        member = ctx.message.guild.get_member(ctx.author.id)
        completed = 0
        try:
            rigs_data = await self.config.user(member).rig()
            rig_temp = copy(rigs_data)
            for component, _ in rig_temp.items():
                if component.lower() == component_user.strip().lower():
                    await ctx.send(f"Removed {component} from your rig")
                    rigs_data.pop(component, None)
            await self.config.user(member).rig.set(rigs_data)
            completed = 1
        except discord.Forbidden:
            return await ctx.send(f"I can't DM you, {ctx.author.mention}")

        if completed == 0:
            await ctx.send(
                "The provided component is not valid, no changes made to your rig"
            )

    async def update_rig(self, rig_data: dict, author: discord.User):
        def check(m):
            return m.author == author and isinstance(m.channel, discord.DMChannel)

        await author.send(
            'Each question you can enter "Cancel" or "Skip"'
            "\nCancel will stop all the question up to the point you gotten to"
            "\nSkip will skip that question and take you to the next question"
        )

        await author.send("What CPU do you have (Cancel|Skip)?")
        msg = await self.bot.wait_for("message", check=check)
        if msg and msg.content.lower().strip() not in ["cancel", "skip"]:
            rig_data["CPU"] = msg.content.strip()
        elif msg and msg.content.lower().strip() == "cancel":
            await author.send("Skipping the rest of the setup")
            return rig_data
        elif msg and msg.content.lower().strip() == "skip":
            await author.send("Skipping CPU, onto the next question we go")
            if not rig_data.get("CPU"):
                rig_data["CPU"] = None

        await author.send("What/How many GPUs do you have (Cancel|Skip)?")
        await author.send('NOTE: If more than 1 separate with "|"')
        msg = await self.bot.wait_for("message", check=check)
        if msg and msg.content.lower().strip() not in ["cancel", "skip"]:
            rig_data["GPU"] = msg.content.strip()
        elif msg and msg.content.lower().strip() == "cancel":
            await author.send("Skipping the rest of the setup")
            return rig_data
        elif msg and msg.content.lower().strip() == "skip":
            await author.send("Skipping GPU, onto the next question we go")
            if not rig_data.get("GPU"):
                rig_data["GPU"] = None

        await author.send("What/How much RAM do you have (Cancel|Skip)?")
        await author.send('NOTE: If more than 1 separate with "|"')
        msg = await self.bot.wait_for("message", check=check)
        if msg and msg.content.lower().strip() not in ["cancel", "skip"]:
            rig_data["RAM"] = msg.content.strip()
        elif msg and msg.content.lower().strip() == "cancel":
            await author.send("Skipping the rest of the setup")
            return rig_data
        elif msg and msg.content.lower().strip() == "skip":
            await author.send("Skipping RAM, onto the next question we go")
            if not rig_data.get("RAM"):
                rig_data["RAM"] = None

        await author.send("What motherboard do you have (Cancel|Skip)?")
        msg = await self.bot.wait_for("message", check=check)
        if msg and msg.content.lower().strip() not in ["cancel", "skip"]:
            rig_data["Motherboard"] = msg.content.strip()
        elif msg and msg.content.lower().strip() == "cancel":
            await author.send("Skipping the rest of the setup")
            return rig_data
        elif msg and msg.content.lower().strip() == "skip":
            await author.send("Skipping Motherboard, onto the next question we go")
            if not rig_data.get("Motherboard"):
                rig_data["Motherboard"] = None

        await author.send("What is your storage setup (Cancel|Skip)?")
        await author.send('NOTE: If more than 1 separate with "|"')
        msg = await self.bot.wait_for("message", check=check)
        if msg and msg.content.lower().strip() not in ["cancel", "skip"]:
            rig_data["Storage"] = msg.content.strip()
        elif msg and msg.content.lower().strip() == "cancel":
            await author.send("Skipping the rest of the setup")
            return rig_data
        elif msg and msg.content.lower().strip() == "skip":
            await author.send("Skipping Storage, onto the next question we go")
            if not rig_data.get("Storage"):
                rig_data["Storage"] = None

        await author.send("What Monitor do you have (Cancel|Skip)?")
        await author.send('NOTE: If more than 1 separate with "|"')
        msg = await self.bot.wait_for("message", check=check)
        if msg and msg.content.lower().strip() not in ["cancel", "skip"]:
            rig_data["Monitor"] = msg.content.strip()
        elif msg and msg.content.lower().strip() == "cancel":
            await author.send("Skipping the rest of the setup")
            return rig_data
        elif msg and msg.content.lower().strip() == "skip":
            await author.send("Skipping monitor, onto the next question we go")
            if not rig_data.get("Monitor"):
                rig_data["Monitor"] = None

        await author.send("What mouse do you have (Cancel|Skip)?")
        await author.send('NOTE: If more than 1 separate with "|"')
        msg = await self.bot.wait_for("message", check=check)
        if msg and msg.content.lower().strip() not in ["cancel", "skip"]:
            rig_data["Mouse"] = msg.content.strip()
        elif msg and msg.content.lower().strip() == "cancel":
            await author.send("Skipping the rest of the setup")
            return rig_data
        elif msg and msg.content.lower().strip() == "skip":
            await author.send("Skipping mouse, onto the next question we go")
            if not rig_data.get("Mouse"):
                rig_data["Mouse"] = None

        await author.send("What keyboard do you have (Cancel|Skip)?")
        await author.send('NOTE: If more than 1 separate with "|"')
        msg = await self.bot.wait_for("message", check=check)
        if msg and msg.content.lower().strip() not in ["cancel", "skip"]:
            rig_data["Keyboard"] = msg.content.strip()
        elif msg and msg.content.lower().strip() == "cancel":
            await author.send("Skipping the rest of the setup")
            return rig_data
        elif msg and msg.content.lower().strip() == "skip":
            await author.send("Skipping keyboard, onto the next question we go")
            if not rig_data.get("Keyboard"):
                rig_data["Keyboard"] = None

        await author.send("What headset do you have (Cancel|Skip)?")
        await author.send('NOTE: If more than 1 separate with "|"')
        msg = await self.bot.wait_for("message", check=check)
        if msg and msg.content.lower().strip() not in ["cancel", "skip"]:
            rig_data["Headset"] = msg.content.strip()
        elif msg and msg.content.lower().strip() == "cancel":
            await author.send("Skipping the rest of the setup")
            return rig_data
        elif msg and msg.content.lower().strip() == "skip":
            await author.send("Skipping headset, onto the next question we go")
            if not rig_data.get("Headset"):
                rig_data["Headset"] = None

        await author.send("What case do you have (Cancel|Skip)?")
        msg = await self.bot.wait_for("message", check=check)
        if msg and msg.content.lower().strip() not in ["cancel", "skip"]:
            rig_data["Case"] = msg.content.strip()
        elif msg and msg.content.lower().strip() == "cancel":
            await author.send("Skipping the rest of the setup")
            return rig_data
        elif msg and msg.content.lower().strip() == "skip":
            await author.send("Skipping case")
            if not rig_data.get("Case"):
                rig_data["Case"] = None

        return rig_data

    async def _get_member_rig(self, ctx: commands.Context, member: discord.Member):
        rig_data = await self.config.user(member).rig.get_raw()
        has_profile = [True for _, value in rig_data.items() if value]
        if not has_profile:
            await ctx.send(
                f"Member: {member.mention} does not have any rig data with me"
            )
            return None
        gaming_cog = ctx.bot.get_cog("GamingProfile")
        discord_user_name = member.display_name
        description = ""
        last_seen = (
            gaming_cog._cache.get(member.id)
            or await ConfigHolder.GamingProfile.user(member).seen()
        )

        if last_seen:
            last_seen_datetime = get_date_time(last_seen)
            last_seen_text = get_date_string(last_seen_datetime)
        else:
            last_seen_datetime = None
            last_seen_text = ""

        header = ""
        activity = get_member_activity(member)
        if activity:
            header += f"{activity}\n"
        description += header

        embed = discord.Embed(
            title=f"{discord_user_name}'{'s' if not discord_user_name.endswith('s') else ''} rig",
            description=description,
        )
        footer = ""
        if last_seen_datetime:
            if last_seen_text == "Now":
                footer += "Currently online"
            else:
                footer += f"Last online: {last_seen_text}"
        footer.strip()
        if footer:
            embed.set_footer(text=footer)

        component_field = ""
        component_name_field = ""
        for component, component_value in rig_data.items():
            new_line = ""
            if component_value:
                if "|" in component_value:
                    component_value = component_value.replace("|", "\n")
                else:
                    component_value = component_value.replace(",", "\n")
                if "\n" in component_value:
                    new_line = "\n" * component_value.count("\n")
                component_name_field += f"{component_value}\n"
                component_name_field = regex.sub(
                    REPLACE_BRACKER, "", component_name_field
                )
                component_field += f"{component}{new_line}\n"
        component_field = component_field.strip()
        component_name_field = component_name_field.strip()
        embed.add_field(name=f"Component", value=component_field, inline=True)
        embed.add_field(name=f"Component Name", value=component_name_field, inline=True)
        avatar = member.avatar_url or member.default_avatar_url
        embed.set_author(name=member.display_name, icon_url=avatar)
        return embed
