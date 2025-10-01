import os
import discord
import aiohttp
from discord.ext import commands
from utils.constants import RiftConstants

constants = RiftConstants()

ROBLOX_COOKIE = os.getenv("ROBLOX_COOKIE")
ROBLOX_USER_ID = os.getenv("ROBLOX_USER_ID")

class RobloxFilter(commands.Cog):
    def __init__(self, rift: commands.Bot):
        self.rift = rift

    async def roblox_filter(self, text: str, under13: bool = False) -> str | None:
        url = "https://textfilter.roblox.com/v1/filter-text"
        payload = {
            "text": text,
            "context": "Chat",
            "userId": ROBLOX_USER_ID,
            "chatMode": "Under13" if under13 else "Over13"
        }

        headers = {
            "Cookie": ROBLOX_COOKIE,
            "Content-Type": "application/json"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as resp:
                    if resp.status != 200:
                        return None
                    data = await resp.json()
            return data.get("filteredText")
        except Exception:
            return None

    @commands.command(name="filter")
    async def filter_word(self, ctx: commands.Context, word: str = None, age: str = None):
        try:
            if not word:
                embed = discord.Embed(
                    description="<:RiftFail:1421378112339312742> Please specify a word to check.",
                    color=0x89FFBC
                )
                return await ctx.send(embed=embed)

            # Delete invoking message if prefixed with ">"
            if ctx.message.content.startswith(">"):
                try:
                    await ctx.message.delete()
                except discord.Forbidden:
                    pass

            under13 = age and age.lower() in ["13", "under", "u13", "under13"]

            filtered = await self.roblox_filter(word, under13)

            if not filtered:
                embed = discord.Embed(
                    description="<:RiftFail:1421378112339312742> An error occurred while reaching Roblox filter API. Please try again later.",
                    color=0x89FFBC
                )
                return await ctx.send(embed=embed)

            allowed = (filtered.lower() == word.lower())

            if allowed:
                desc = f"<:RiftSuccess:1421378019167309888> **Allowed** in Roblox chat."
            else:
                desc = f"<:RiftFail:1421378112339312742> **Blocked** or filtered in Roblox chat."

            embed = discord.Embed(
                title="<:riftsystems:1421319259472003212> Roblox Chat Filter",
                description=desc,
                color=0x89FFBC
            )

            embed.add_field(name="Input", value=f"`{word}`", inline=False)
            embed.add_field(
                name=f"Filtered ({'Under 13' if under13 else '13+'})",
                value=f"`{filtered}`",
                inline=False
            )

            await ctx.send(embed=embed)

        except Exception as e:
            error_embed = discord.Embed(
                title="<:riftsystems:1421319259472003212> Roblox Chat Filter",
                description=(
                    f"<:RiftFail:1421378112339312742> An unexpected error occurred.\n\n"
                    f"```{type(e).__name__}: {e}```\n"
                    f"Please contact [Rift Systems](https://discord.gg/EPaU5aWqCU) for support."
                ),
                color=0x89FFBC
            )
            await ctx.send(embed=error_embed)


async def setup(rift: commands.Bot):
    await rift.add_cog(RobloxFilter(rift))