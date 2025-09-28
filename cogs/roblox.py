import discord
from discord import app_commands
from discord.ext import commands
import aiohttp

# Roblox API endpoints
ROBLOX_API = "https://users.roblox.com/v1/users/{user_id}"
USERNAME_TO_ID = "https://api.roblox.com/users/get-by-username?username={username}"
FRIENDS_API = "https://friends.roblox.com/v1/users/{user_id}/friends/count"
FOLLOWERS_API = "https://friends.roblox.com/v1/users/{user_id}/followers/count"
FOLLOWING_API = "https://friends.roblox.com/v1/users/{user_id}/followings/count"
GROUPS_API = "https://groups.roblox.com/v1/users/{user_id}/groups/roles"
AVATAR_API = "https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=150x150&format=png"


class Roblox(commands.Cog):
    def __init__(self, rift: commands.Bot):
        self.rift = rift

    async def fetch_json(self, url: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                return await resp.json()

    async def resolve_user_id(self, identifier: str | int):
        """Resolve a username or ID into a Roblox user ID"""
        if str(identifier).isdigit():
            return int(identifier)

        data = await self.fetch_json(USERNAME_TO_ID.format(username=identifier))
        if data and "Id" in data and data["Id"] != 0:
            return int(data["Id"])
        return None

    async def build_embed(self, user_id: int):
        user_data = await self.fetch_json(ROBLOX_API.format(user_id=user_id))
        if "name" not in user_data:
            return None

        username = user_data["name"]
        created = user_data.get("created", "Unknown")

        # Counts
        friends = (await self.fetch_json(FRIENDS_API.format(user_id=user_id))).get("count", 0)
        followers = (await self.fetch_json(FOLLOWERS_API.format(user_id=user_id))).get("count", 0)
        following = (await self.fetch_json(FOLLOWING_API.format(user_id=user_id))).get("count", 0)

        # Groups
        groups_data = await self.fetch_json(GROUPS_API.format(user_id=user_id))
        groups_count = len(groups_data.get("data", []))

        # Avatar
        avatar_data = await self.fetch_json(AVATAR_API.format(user_id=user_id))
        avatar_url = avatar_data.get("data", [{}])[0].get("imageUrl", "")

        # Embed
        embed = discord.Embed(
            title=username,
            description=f"Roblox profile for **{username}**",
            color=0x89FFBC
        )
        embed.set_thumbnail(url=avatar_url)
        embed.add_field(name="Created on", value=created, inline=False)
        embed.add_field(name="Friends", value=friends, inline=True)
        embed.add_field(name="Followers", value=followers, inline=True)
        embed.add_field(name="Following", value=following, inline=True)
        embed.add_field(name="Groups", value=groups_count, inline=True)
        embed.set_footer(text=f"User ID: {user_id}")

        return embed

    # Slash command
    @app_commands.command(name="roblox", description="Get info about a Roblox user (username or ID)")
    async def roblox_slash(self, interaction: discord.Interaction, identifier: str):
        user_id = await self.resolve_user_id(identifier)
        if not user_id:
            embed = discord.Embed(
                description="❌ Could not find that Roblox user.",
                color=0x89FFBC,
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        embed = await self.build_embed(user_id)
        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                description="❌ Failed to fetch Roblox profile.",
                color=0x89FFBC,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    # Prefix command
    @commands.command(name="roblox")
    async def roblox_prefix(self, ctx: commands.Context, identifier: str):
        user_id = await self.resolve_user_id(identifier)
        if not user_id:
            return await ctx.send_error("Could not find that Roblox user.")

        embed = await self.build_embed(user_id)
        if embed:
            await ctx.send(embed=embed)
        else:
            await ctx.send_error("Failed to fetch Roblox profile.")


async def setup(rift: commands.Bot):
    await rift.add_cog(Roblox(rift))

