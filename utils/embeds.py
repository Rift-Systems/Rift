import discord
import platform
from datetime import datetime, timezone
from discord import Interaction
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput
from utils.constants import RiftConstants
from typing import List, Optional


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
        

class DeveloperErrorEmbed(discord.Embed):
    def __init__(self, error, ctx, error_id):
        super().__init__(
            title="Something went wrong!",
            description=f"{error}",
            color=discord.Color.red(),
        )
        self.add_field(name="Error ID", value=f"__{error_id}__", inline=True)
        self.add_field(
            name="User", value=f"{ctx.author.mention}(**{ctx.author.id}**)", inline=True
        )
        self.add_field(
            name="Server Info",
            value=f"{ctx.guild.name}(**{ctx.guild.id}**)",
            inline=True,
        )
        self.add_field(
            name="Command",
            value=f"Name: {ctx.command.qualified_name}\nArgs: {ctx.command.params}",
            inline=True,
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
            timestamp=command_run_time,
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
            text=f"Cluster {cluster} | Shard {shards} | {environment}"
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


class PingCommandEmbed:
    @staticmethod
    def create_ping_embed(
        latency: float,
        database_connected: bool,
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
                    f"> **Database:** `{'Connected' if database_connected else 'Disconnected'}`\n"
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
    def _make(
        *,
        title: str,
        color: str | discord.Color,
        guild: discord.Guild,
        current_guild_count: int,
        timestamp: Optional[datetime] = None,
    ) -> discord.Embed:
        embed_color = color if isinstance(color, discord.Color) else discord.Color.from_str(color)

        e = discord.Embed(
            title=title,
            color=embed_color,
            timestamp=timestamp or datetime.now(timezone.utc),
        )

        if getattr(guild, "icon", None):
            e.set_thumbnail(url=guild.icon.url)

        info_value = (
            f"> - **Guild Name:** {guild.name}\n"
            f"> - **Guild ID:** `{guild.id}`\n"
            f"> - **Owner:** <@{guild.owner_id}> (`{guild.owner_id}`)\n"
            f"> - **Member Count:** `{guild.member_count}`\n"
            f"> - **Current Guild Count:** `{current_guild_count}`"
        )

        e.add_field(
            name="Guild Information",
            value=info_value,
            inline=True,
        )

        return e


    @staticmethod
    def create_guild_join_embed(
        guild: discord.Guild,
        current_guild_count: int,
        timestamp: Optional[datetime] = None,
    ) -> discord.Embed:
        return OnGuildEmbed._make(
            title="Joined a New Guild",
            color="#89ffbc",
            guild=guild,
            current_guild_count=current_guild_count,
            timestamp=timestamp,
        )


    @staticmethod
    def create_guild_remove_embed(
        guild: discord.Guild,
        current_guild_count: int,
        timestamp: Optional[datetime] = None,
    ) -> discord.Embed:
        return OnGuildEmbed._make(
            title="Removed From a Guild",
            color="#FFABAB",
            guild=guild,
            current_guild_count=current_guild_count,
            timestamp=timestamp,
        )
    
    
class UserInformationEmbed:
    def __init__(self, member, constants, rift):
        self.member = member
        self.constants = constants
        self.rift = rift


    async def fetch_guild_specific_badges(self):
        badges = []
        try:

            guild = self.rift.get_guild(1420889056174411898)
            guild_member = await guild.fetch_member(self.member.id)

            staff_roles = [1421718175338205256]  # Staff Role

            # Check for Rift Team, Rift Development, Rift Management, and Rift Support Team roles first
            
            if any(
                discord.utils.get(guild_member.roles, id=role_id)
                for role_id in [1421267029960167614]
            ):
                badges.append("> <:riftsystems:1421319259472003212> Rift Team")

            if any(
                discord.utils.get(guild_member.roles, id=role_id)
                for role_id in [1421267174991069244]
            ):
                badges.append("> <:riftsystems:1421319259472003212> Rift Development")

            if any(
                discord.utils.get(guild_member.roles, id=role_id)
                for role_id in [1421278574685720576]
            ):
                badges.append("> <:riftsystems:1421319259472003212> Rift Management")

            if any(
                discord.utils.get(guild_member.roles, id=role_id)
                for role_id in [1421279252451561564]
            ):
                badges.append("> <:riftsystems:1421319259472003212> Rift Support Team")

            if any(
                discord.utils.get(guild_member.roles, id=role_id)
                for role_id in [1421278534734839849]
            ):
                badges.append("> <:riftsystems:1421319259472003212> Rift Quality Assurance"
            )

            # Check for staff role second
            
            if any(discord.utils.get(guild_member.roles, id=role_id)
                for role_id in staff_roles):
                badges.append("> <:riftsystems:1421319259472003212> Rift Staff")

            # Check for Notable role third

            if any(
                discord.utils.get(guild_member.roles, id=role_id)
                for role_id in [1421279448631607357]
            ):
                badges.append("> <:Notable:1421908258129580115> Recognized User")


        except (discord.NotFound, discord.Forbidden):
            pass
        except Exception as e:
            print(f"Error fetching guild-specific badges: {e}")

        return badges


    def get_user_badges(self):
        flags = self.member.public_flags
        badges = []

        badge_map = {
            "hypesquad_bravery": "> <:sbHypeSquadBrave:1421716745399566346> HypeSquad Bravery",
            "hypesquad_brilliance": "> <:sbHypeSquadBrilliance:1421716796234534942> HypeSquad Brilliance",
            "hypesquad_balance": "> <:sbHypeSquadBalance:1421716836658970716> HypeSquad Balance",
            "verified_bot": "> <:sbVerified:1421717217703104603> Verified Bot",
            "early_supporter": "> <:staff:1421718058019323978> Early Supporter",
            "active_developer": "> <:ActiveDeveloper:1422234997850505356> Active Developer",
        }

        for flag, badge in badge_map.items():
            if getattr(flags, flag, False):
                badges.append(badge)

        return badges


    def get_permissions(self):
        permissions = [
            perm.replace("_", " ").title()
            for perm, value in self.member.guild_permissions
            if value
        ]
        return ", ".join(permissions[:10]) or "No Permissions"


    async def create_embed(self):
        try:

            # Basic user information

            user_mention = self.member.mention
            display_name = self.member.display_name
            user_id = self.member.id
            account_created = f"<t:{int(self.member.created_at.timestamp())}:F>"
            joined_server = (
                f"<t:{int(self.member.joined_at.timestamp())}:F>"
                if self.member.joined_at
                else "N/A"
            )

            roles = sorted(
                [role for role in self.member.roles if role.name != "@everyone"],
                key=lambda role: role.position,
                reverse=True,
            )[
                :10
            ]

            role_mentions = [role.mention for role in roles]
            role_count = len(role_mentions)

            # Fetch badges and permissions
            
            guild_badges = await self.fetch_guild_specific_badges()
            discord_badges = self.get_user_badges()
            badges = guild_badges + discord_badges
            permissions_display = self.get_permissions()

            # Create embed

            embed = discord.Embed(
                title=f"User Info - {display_name}",
                color=self.constants.rift_embed_color_setup(),
                timestamp=datetime.now(),
            )

            embed.add_field(
                name="**User Information**",
                value=(
                    f"> - **Mention:** {user_mention}\n"
                    f"> - **Display Name:** {display_name}\n"
                    f"> - **User ID:** {user_id}\n"
                    f"> - **Account Created:** {account_created}\n"
                    f"> - **Joined Server:** {joined_server}"
                ),
                inline=False,
            )

            embed.set_thumbnail(url=self.member.display_avatar.url)

            # Add badges and roles

            embed.add_field(
                name="Badges",
                value="\n".join(badges) if badges else "No badges",
                inline=False,
            )

            embed.add_field(
                name=f"Roles ({role_count})",
                value=", ".join(role_mentions) if role_mentions else "No Roles",
                inline=False,
            )

            embed.add_field(name="Permissions", value=permissions_display, inline=False)

            if self.member.bot:
                embed.set_footer(text="This user is a bot.")

            return embed


        except Exception as e:
            print(f"Error generating embed: {e}")
            return None
        
        
class RobloxUserEmbed(discord.Embed):
    @staticmethod
    def create(
        *,
        user_id: int,
        username: str,
        created: str,
        friends: int,
        followers: int,
        following: int,
        groups: int,
        avatar_url: str | None = None,
    ) -> discord.Embed:
        e = discord.Embed(
            title=username,
            color=discord.Color.from_str("#89ffbc"),
        )
        if avatar_url:
            e.set_thumbnail(url=avatar_url)

        info_value = (
            f"> - **Username:** {username}\n"
            f"> - **User ID:** `{user_id}`\n"
            f"> - **Created:** {created}\n"
            f"> - **Friends:** `{friends}`\n"
            f"> - **Followers:** `{followers}`\n"
            f"> - **Following:** `{following}`\n"
            f"> - **Groups:** `{groups}`"
        )
        e.add_field(
            name="Roblox Information",
            value=info_value,
            inline=True,
        )
        return e