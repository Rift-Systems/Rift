# ==========================================================================================================
# This file is for roblox related operation such as looking up roblox users, performing in-game roblox
# operation as well as verification operations with Roblox OAuth.
# ==========================================================================================================

import discord
import aiohttp
import asyncio
import datetime as dt
from discord import app_commands
from discord.ext import commands
from typing import Optional, Union
from utils.utils import RiftContext
from utils.embeds import RobloxUserEmbed

# Roblox API endpoints

ROBLOX_USER_BY_ID = "https://users.roblox.com/v1/users/{user_id}"
RESOLVE_USERNAMES = "https://users.roblox.com/v1/usernames/users"  # POST
FRIENDS_API = "https://friends.roblox.com/v1/users/{user_id}/friends/count"
FOLLOWERS_API = "https://friends.roblox.com/v1/users/{user_id}/followers/count"
FOLLOWING_API = "https://friends.roblox.com/v1/users/{user_id}/followings/count"
GROUPS_API = "https://groups.roblox.com/v1/users/{user_id}/groups/roles"
AVATAR_API = "https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=150x150&format=png"

class Roblox(commands.Cog):
    def __init__(self, rift: commands.Bot):
        self.rift = rift
        self.session: Optional[aiohttp.ClientSession] = None

    async def cog_load(self):
        timeout = aiohttp.ClientTimeout(total=15)
        self.session = aiohttp.ClientSession(timeout=timeout)

    async def cog_unload(self):
        if self.session and not self.session.closed:
            await self.session.close()

    async def _ensure_session(self):
        if self.session is None or self.session.closed:
            await self.cog_load()


    async def fetch_json(self, url: str, *, method: str = "GET", json: dict | None = None) -> dict:
        
        await self._ensure_session()
        
        try:
            async with self.session.request(method, url, json=json) as resp:
                if resp.status == 429:
                    ra = resp.headers.get("Retry-After", "unknown")
                    return {"error": "rate_limited", "retry_after": ra}
                if resp.status >= 400:
                    return {"error": f"http_{resp.status}"}
                return await resp.json(content_type=None)
        except aiohttp.ClientConnectorDNSError as e:
            return {"error": "dns_error", "detail": str(e)}
        except asyncio.TimeoutError:
            return {"error": "timeout"}
        except aiohttp.ClientError as e:
            return {"error": "network_error", "detail": str(e)}
        except Exception as e:
            return {"error": "unexpected_error", "detail": str(e)}


    async def resolve_user_id(self, identifier: Union[str, int]) -> Optional[int]:
        if isinstance(identifier, int) or str(identifier).isdigit():
            return int(identifier)

        username = str(identifier).strip()
        if not username:
            return None

        payload = {"usernames": [username], "excludeBannedUsers": True}
        data = await self.fetch_json(RESOLVE_USERNAMES, method="POST", json=payload)
        if data.get("error"):
            return None

        users = data.get("data") or []
        if users and "id" in users[0]:
            return int(users[0]["id"])
        return None


    async def build_embed(self, user_id: int) -> Optional[discord.Embed]:
       
        user_data = await self.fetch_json(ROBLOX_USER_BY_ID.format(user_id=user_id))
        
        if user_data.get("error") or "name" not in user_data:
            return None

        username = user_data["name"]
        
        created_iso = user_data.get("created")  # e.g. "2021-10-02T20:46:22.757Z"
        if created_iso:
            try:
                created_dt = dt.datetime.fromisoformat(created_iso.replace("Z", "+00:00"))
                created_unix = int(created_dt.timestamp())
                created = f"<t:{created_unix}:F>"     # full date/time
            except Exception:
                created = created_iso
        else:
            created = "Unknown"
        
        friends_data = await self.fetch_json(FRIENDS_API.format(user_id=user_id))
        followers_data = await self.fetch_json(FOLLOWERS_API.format(user_id=user_id))
        following_data = await self.fetch_json(FOLLOWING_API.format(user_id=user_id))
        friends = friends_data.get("count", 0) if not friends_data.get("error") else 0
        followers = followers_data.get("count", 0) if not followers_data.get("error") else 0
        following = following_data.get("count", 0) if not following_data.get("error") else 0
        groups_data = await self.fetch_json(GROUPS_API.format(user_id=user_id))
        groups_count = 0
        
        if not groups_data.get("error"):
            arr = groups_data.get("data") or []
            groups_count = len(arr) if isinstance(arr, list) else 0


        avatar_data = await self.fetch_json(AVATAR_API.format(user_id=user_id))
        avatar_url = ""
        
        if not avatar_data.get("error"):
            dl = avatar_data.get("data") or []
            avatar_url = (dl[0].get("imageUrl") if dl else "") or ""

        embed = RobloxUserEmbed.create(
            user_id=user_id,
            username=username,
            created=created,
            friends=friends,
            followers=followers,
            following=following,
            groups=groups_count,
            avatar_url=avatar_url or None,
        )

        view = discord.ui.View()
        profile_url = f"https://www.roblox.com/users/{user_id}/profile"
        view.add_item(
            discord.ui.Button(
                label="View Profile",
                url=profile_url,
                style=discord.ButtonStyle.link
            )
        )

        return embed, view


    @commands.hybrid_command(
        name="roblox",
        description="Get info about a Roblox user (username or ID)",
        with_app_command=True,
        extras={"category": "Other"},
    )
    async def roblox(self, ctx: RiftContext, identifier: str):
        
        user_id = await self.resolve_user_id(identifier)
        
        if not user_id:
            fail_embed = discord.Embed(
                description="<:RiftFail:1421378112339312742> Could not find that Roblox user.",
                color=0x89FFBC,
            )
            
            if ctx.interaction:
                return await ctx.interaction.response.send_message(embed=fail_embed, ephemeral=True)
            
            if hasattr(ctx, "send_error"):
                return await ctx.send_error("Could not find that Roblox user.")
            return await ctx.send(embed=fail_embed)

        embed, view = await self.build_embed(user_id)



        if embed:
            if ctx.interaction and not ctx.interaction.response.is_done():
                return await ctx.interaction.response.send_message(embed=embed, view=view)
            return await ctx.send(embed=embed, view=view)

        err_embed = discord.Embed(
            description="<:RiftFail:1421378112339312742> Failed to fetch Roblox profile.",
            color=0x89FFBC,
        )
        
        
        if ctx.interaction and not ctx.interaction.response.is_done():
            return await ctx.interaction.response.send_message(embed=err_embed, ephemeral=True)
        if hasattr(ctx, "send_error"):
            return await ctx.send_error("Failed to fetch Roblox profile.")
        
        
        return await ctx.send(embed=err_embed)


async def setup(rift: commands.Bot):
    await rift.add_cog(Roblox(rift))