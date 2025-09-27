import discord
import platform
from datetime import datetime
from discord import Interaction
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput
from utils.constants import RiftConstants
from typing import List


constants = RiftConstants()


class SuccessEmbed(discord.Embed):
    def __init__(self, title: str, description: str, **kwargs):
        super().__init__(
            title=title, description=description, color=discord.Color.green(), **kwargs
        )



class ErrorEmbed(discord.Embed):
    def __init__(self, title: str, description: str, **kwargs):
        super().__init__(
            title=title, description=description, color=discord.Color.red(), **kwargs
        )



class MissingArgsEmbed(discord.Embed):
    def __init__(self, param_name):
        super().__init__(
            title="",
            description=f"<:RiftFail:1421378112339312742> Please specify a {param_name}",
            color=discord.Color.red(),
        )



class BadArgumentEmbed(discord.Embed):
    def __init__(self):
        super().__init__(
            title="",
            description="<:RiftFail:1421378112339312742> You provided an incorrect argument type.",
            color=discord.Color.red(),
        )



class ForbiddenEmbed(discord.Embed):
    def __init__(self):
        super().__init__(
            title="",
            description="<:RiftFail:1421378112339312742> I couldn't send you a DM. Please check your DM settings.",
            color=discord.Color.red(),
        )



class MissingPermissionsEmbed(discord.Embed):
    def __init__(self):
        super().__init__(
            title="",
            description="<:RiftFail:1421378112339312742> You don't have the required permissions to run this command.",
            color=discord.Color.red(),
        )



class UserErrorEmbed(discord.Embed):
    def __init__(self, error_id):
        super().__init__(
            title="Something Went Wrong",
            description=f"Please contact [Rift Systems](https://discord.gg/EPaU5aWqCU) for support!\nError ID: `{error_id}`",
            color=discord.Color.red(),
        )
        


class AboutEmbed:
    @staticmethod
    def create_info_embed(
        uptime,
        guilds,
        users,
        latency,
        version,
        bot_name,
        bot_icon,
        shards,
        cluster,
        environment,
        command_run_time,
        thumbnail_url,
    ):
        embed = discord.Embed(
            description=(
                "Rift is an all-in-one server management and moderation, and staff management tool for ERLC based servers, You can use it to do operations like infractions, shift management, sessions, and more!"
            ),
            color=discord.Color.from_str("#2a2c30"),
        )

        embed.add_field(name="", value=(""), inline=False)

        embed.add_field(
            name="Rift Information",
            value=(
                f"> **Servers:** `{guilds:,}`\n"
                f"> **Users:** `{users:,}`\n"
                f"> **Uptime:** <t:{int((uptime.timestamp()))}:R>\n"
                f"> **Latency:** `{round(latency * 1000)}ms`"
            ),
            inline=True,
        )

        embed.add_field(
            name="System Information",
            value=(
                f"> **Language:** `Python`\n"
                f"> **Database:** `{version}`\n"
                f"> **Host OS:** `{platform.system()}`\n"
                f"> **Host:** `Nexure Solutions`"
            ),
            inline=True,
        )

        embed.add_field(name="", value=(""), inline=False)

        embed.set_footer(
            text=f"Cluster {cluster} | Shard {shards} | {environment} • {command_run_time}"
        )

        embed.set_author(name=bot_name, icon_url=bot_icon)
        embed.set_thumbnail(url=thumbnail_url)
        return embed



class AboutWithButtons:
    @staticmethod
    def create_view():
        view = View()

        support_server_button = Button(
            label="Support Server",
            emoji="<:chat:1421321278836441130>",
            style=discord.ButtonStyle.primary,
            url="https://discord.gg/EPaU5aWqCU",
        )
        
        website_button = Button(
            label="Website",
            emoji="<:LinkIcon:1421386466684047403>",
            style=discord.ButtonStyle.primary,
            url="https://riftsystems.xyz",
        )

        view.add_item(support_server_button)
        view.add_item(website_button)

        return view



class HelpCenterEmbed(discord.Embed):
    def __init__(self, description: str):
        super().__init__(
            title="Rift Help Center",
            description=description,
            color=constants.rift_embed_color_setup(),
        )



class NicknameSuccessEmbed(discord.Embed):
    def __init__(self, user, previous_name, new_name):
        super().__init__(
            title="Nickname Changed Successfully",
            description=(
                f"> **User**: {user.mention}\n"
                f"> **Previous Name**: ``{previous_name}``\n"
                f"> **New Name**: ``{new_name}``"
            ),
            color=discord.Color.green(),
        )



class RoleSuccessEmbed(discord.Embed):
    def __init__(self, title: str, description: str):
        super().__init__(
            title=title, description=description, color=discord.Color.green()
        )



class ChannelSuccessEmbed(discord.Embed):
    def __init__(self, title: str, description: str):
        super().__init__(
            title=title, description=description, color=discord.Color.green()
        )


class SearchResultEmbed(discord.Embed):
    def __init__(
        self,
        title: str,
        description: str,
        case_number: int,
        collection: str,
        details: str,
    ):
        super().__init__(
            title=title,
            description=description,
            color=constants.rift_embed_color_setup(),
        )
        self.add_field(name="Case Number", value=case_number, inline=False)
        self.add_field(name="Collection", value=collection, inline=False)
        self.add_field(name="Details", value=details, inline=False)



class PingCommandEmbed:
    @staticmethod
    def create_ping_embed(
        latency: float,
        database_latency: int,
        uptime,
        shard_info: List[dict],
        page: int = 0,
    ):
        embed = discord.Embed(
            title="<:riftsystems:1421319259472003212> Rift",
            color=constants.rift_embed_color_setup(),
        )

        if page == 0:
            embed.add_field(
                name="<:settings:1421385210167033979> **Network Information**",
                value=(
                    f"> **Latency:** `{round(latency * 1000)}ms` \n"
                    f"> **Database:** `{'Connected' if database_latency else 'Disconnected'}`\n"
                    f"> **Uptime:** <t:{int(uptime.timestamp())}:R>"
                ),
                inline=False,
            )
        else:
            embed.add_field(name="**Sharding Information**", value="", inline=False)

            start_index = (page - 1) * 5
            end_index = start_index + 5
            shards_to_display = shard_info[start_index:end_index]

            for shard in shards_to_display:
                embed.add_field(
                    name=f"<:clock:1421385310666883135> **Shard {shard['id']}**",
                    value=f"> **Latency:** `{shard['latency']}ms` \n> **Guilds:** `{shard['guilds']}`",
                    inline=False,
                )

        return embed



class PrefixEmbed(discord.Embed):
    def __init__(self, current_prefix: str):
        super().__init__(
            title="",
            description=f"The current prefix for this server is `{current_prefix}`.",
            color=constants.rift_embed_color_setup(),
        )



class PrefixSuccessEmbed(discord.Embed):
    def __init__(self, new_prefix: str):
        super().__init__(
            title="",
            description=f"<:RiftSuccess:1421378019167309888> Prefix successfully changed to `{new_prefix}`.",
            color=discord.Color.green(),
        )


class PrefixSuccessEmbedNoneChanged(discord.Embed):
    def __init__(self, new_prefix: str):
        super().__init__(
            title="",
            description=f"The current prefix for this server is `{new_prefix}`.",
            color=discord.Color.green(),
        )

class OnGuildEmbed:
    @staticmethod
    def create_guild_join_embed(
        guild,
        current_guild_count,
    ):
        embed = discord.Embed(
            title="Joined a New Guild",
            color=discord.Color.from_str("#89ffbc")
        )

        embed.add_field(
            name="Guild",
            value=f"{guild.name} (ID: {guild.id})",
            inline=True
        )
        embed.add_field(
            name="Member Count",
            value=str(guild.member_count),
            inline=True
        )
        embed.add_field(
            name="Owner Info",
            value=f"{guild.owner} (ID: {guild.owner.id})" if guild.owner else "Owner not found",
            inline=True
        )
        embed.add_field(
            name="Current Guild Count",
            value=str(current_guild_count),
            inline=True
        )

        return embed

    def create_guild_remove_embed(
        guild,
        current_guild_count,
    ):
        embed = discord.Embed(
            title="Removed From a Guild",
            color=discord.Color.from_str("#eb0909")
        )

        embed.add_field(
            name="Guild",
            value=f"{guild.name} (ID: {guild.id})",
            inline=True
        )
        embed.add_field(
            name="Member Count",
            value=str(guild.member_count),
            inline=True
        )
        embed.add_field(
            name="Owner Info",
            value=f"{guild.owner} (ID: {guild.owner.id})" if guild.owner else "Owner not found",
            inline=True
        )
        embed.add_field(
            name="Current Guild Count",
            value=str(current_guild_count),
            inline=True
        )

        return embed
    
class OnCommandEmbed:
    @staticmethod
    def create_command_embed(
        command_name: str,
        user,
        guild,
        channel,
        timestamp: datetime,
        args: str = "None",
    ):
        embed = discord.Embed(
            title=f"Command Used: {command_name}",
            color=discord.Color.from_str("#89ffbc"),
            timestamp=timestamp
        )

        embed.add_field(
            name="User",
            value=f"{user} (ID: {user.id})",
            inline=True
        )
        embed.add_field(
            name="Guild",
            value=f"{guild.name} (ID: {guild.id})" if guild else "DM (No Guild)",
            inline=True
        )
        embed.add_field(
            name="Owner Info",
            value=f"{guild.owner} (ID: {guild.owner.id})" if guild and guild.owner else "Owner not found",
            inline=True
        )
        embed.add_field(
            name="Channel",
            value=f"{channel} (ID: {channel.id})",
            inline=True
        )
        embed.add_field(
            name="Arguments",
            value=args,
            inline=False
        )

        return embed