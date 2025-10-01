# ==========================================================================================================
# This file is for commands that have to do with management services such as server management or user
# management, for example viewing or altering user information. Running lookups on Discord users, linking,
# unlinking and editing server link for in-game servers or even Discord servers.
# ==========================================================================================================

import discord
import aiomysql
from typing import Literal, Dict, Optional, Callable, Awaitable
from discord.ext import commands
from utils.constants import RiftConstants
from utils.utils import RiftContext
from utils.embeds import UserInformationEmbed
from utils.modals import AddUserModal

constants = RiftConstants()
SocialPlatformType = Literal["Twitter", "Instagram", "Snapchat", "Youtube", "GitHub", "TikTok"]

def _platform_url(platform: str, username: str) -> str:
    platform = platform.lower()
    if platform == "instagram":
        return f"https://instagram.com/{username}"
    if platform == "snapchat":
        return f"https://snapchat.com/add/{username}"
    if platform == "youtube":
        return f"https://youtube.com/@{username}"
    if platform == "github":
        return f"https://github.com/{username}"
    if platform == "tiktok":
        return f"https://tiktok.com/@{username}"
    return f"https://x.com/{username}"


class SocialLinksButton(discord.ui.Button):
    def __init__(
        self,
        user_id: int,
        fetch_links: Callable[[int], Awaitable[Dict[str, str]]],
    ):
        super().__init__(
            label="Social Links",
            style=discord.ButtonStyle.gray,
            custom_id=f"social_links_{user_id}",
            emoji="<:LinkIcon:1421386466684047403>",
        )
        self.user_id = user_id
        self.fetch_links = fetch_links


    async def callback(self, interaction: discord.Interaction):
        try:
            links = await self.fetch_links(self.user_id)

            if not links:
                await interaction.response.send_message(
                    "This user has no social links.", ephemeral=True
                )
                return

            embed = discord.Embed(
                title="Social Links",
                description="",
                color=getattr(interaction.client, "base_color", discord.Color.green()),
            )

            for platform, username in links.items():
                embed.add_field(
                    name=platform.title(),
                    value=_platform_url(platform, username),
                    inline=False,
                )

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(
                f"An error occurred: {str(e)}", ephemeral=True
            )
            print(f"Error in social links callback: {str(e)}")


class ManagementCommandCog(commands.Cog):
    def __init__(self, rift):
        self.rift = rift
        self.constants = constants
        

    async def _ensure_pool(self):
        if not self.constants.pool:
            await self.constants.connect()


    async def _get_social_links(self, user_id: int) -> Dict[str, str]:
        await self._ensure_pool()
        async with self.constants.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    "SELECT platform, username FROM user_social_links WHERE user_id=%s",
                    (user_id,),
                )
                rows = await cur.fetchall()
        return {row["platform"].lower(): row["username"] for row in rows}


    async def _set_social_link(self, user_id: int, platform: str, username: str) -> None:
        await self._ensure_pool()
        async with self.constants.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    """
                    INSERT INTO user_social_links (user_id, platform, username)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE username = VALUES(username)
                    """,
                    (user_id, platform.lower(), username),
                )
                await conn.commit()


    async def _remove_social_link(self, user_id: int, platform: str) -> int:
        await self._ensure_pool()
        async with self.constants.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    "DELETE FROM user_social_links WHERE user_id=%s AND platform=%s",
                    (user_id, platform.lower()),
                )
                affected = cur.rowcount
                await conn.commit()
                return affected
            

    @commands.hybrid_command(description="Show all information about a certain user.", aliases=["ui"], with_app_command=True, extras={"category": "General"},)
    async def whois(self, ctx, member: discord.User = None):
        member = member or ctx.author


        try:
            fetched_member: discord.Member = await ctx.guild.fetch_member(member.id)
        except discord.NotFound:
            fetched_member = member


        embed = await UserInformationEmbed(
            fetched_member, self.constants, self.rift
        ).create_embed()


        links = await self._get_social_links(fetched_member.id)
        view = None
        if links:
            view = discord.ui.View()
            view.add_item(SocialLinksButton(fetched_member.id, self._get_social_links))


        await ctx.send(embed=embed, view=view)


    @commands.hybrid_group(name="social", description="Manage your social media links", extras={"category": "General"},)
    async def social(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send_error("Please specify a subcommand: add, remove, list")


    @social.command(name="add", description="Add a social media link", extras={"category": "General"},)
    async def social_add(self, ctx: RiftContext, platform: SocialPlatformType, username: str):
        await self._set_social_link(ctx.author.id, platform, username)
        link = _platform_url(platform, username)
        await ctx.send_success(f"Added your [**{platform}**]({link}) link successfully!")


    @social.command(name="remove", description="Remove a social media link", extras={"category": "General"},)
    async def social_remove(self, ctx: RiftContext, platform: SocialPlatformType):
        changed = await self._remove_social_link(ctx.author.id, platform)
        if changed > 0:
            await ctx.send_success(f"Removed your {platform} link successfully!")
        else:
            await ctx.send_error(f"You don't have a {platform} link saved.")


    @social.command(name="list", description="List your social media links", extras={"category": "General"},)
    async def social_list(self, ctx: RiftContext):
        links = await self._get_social_links(ctx.author.id)
        if not links:
            await ctx.send_warning("You have no social links saved.")
            return


        embed = discord.Embed(
            title="Your Social Links",
            color=getattr(ctx.rift, "base_color", discord.Color.green()),
        )
        

        for platform, username in links.items():
            embed.add_field(
                name=platform.title(),
                value=_platform_url(platform, username),
                inline=False,
            )


        await ctx.send(embed=embed)


async def setup(rift):
    await rift.add_cog(ManagementCommandCog(rift))
