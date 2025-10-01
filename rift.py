# ==========================================================================================================
# This software was created by Nexure Solutions LLP and Rift Systems.
# This software was created by Nick Derry, JustDizo, Dozen and Abby.
# ==========================================================================================================

import discord
import os
import requests
import asyncio
import aiomysql
import sentry_sdk
from datetime import datetime
from discord.ext import commands
from utils.constants import RiftConstants
from utils.utils import get_prefix, RiftContext
from cogwatch import watch

# We use constants.py to specify things like the mysql db connection, prefix
# and default embed color.

constants = RiftConstants()

class Rift(commands.AutoShardedBot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.token = None
        self.start_time = datetime.now()
        self.error = "<:RiftFail:1421378112339312742>"
        self.success = "<:RiftSuccess:1421378019167309888>"
        self.loading = "<:RiftLoading:1421377775549546599>"
        self.warning = "<:RiftWarning:1421378257378345041>"
        self.base_color = 0x89ffbc
        self.context = RiftContext
        self.prefixes = {}


    async def get_context(self, message, *, cls=RiftContext):
        return await super().get_context(message, cls=cls)


    @watch(path="cogs", preload=False)
    async def on_ready(self):
        self.prefixes = {}
        async with constants.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("SELECT serverid, prefix FROM server_config")
                rows = await cur.fetchall()
                for row in rows:
                    self.prefixes[int(row["serverid"])] = row["prefix"]


        if constants.rift_environment_type() == "Development":
            pass


        else:
            guild_count = len(rift.guilds)
            user_count = sum(
                guild.member_count or 0 for guild in rift.guilds
            )

            await rift.change_presence(
                activity=discord.Activity(
                    name=f"{guild_count} Guilds • {user_count:,} Users • /help",
                    type=discord.ActivityType.watching,
                )
            )


        print(f"{self.user.name} is ready!")


    async def is_owner(self, user: discord.User):
        await constants.fetch_bypassed_users()
        
        if user.id in constants.bypassed_users:
            return True
        
        try:
            async with constants.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    await cur.execute(
                        "SELECT access_level FROM users WHERE oauth_id=%s AND access_level='Developer'",
                        (user.id,)
                    )
                    row = await cur.fetchone()
                    if row:
                        return True
                    
        except Exception:
            pass

        return False


    async def setup_hook(self) -> None:
        await constants.connect()

        for root, _, files in os.walk("./cogs"):
            for file in files:
                if file.endswith(".py"):
                    cog_path = os.path.relpath(os.path.join(root, file), "./cogs")
                    cog_module = cog_path.replace(os.sep, ".")[:-3]
                    await self.load_extension(f"cogs.{cog_module}")

        print("All cogs loaded successfully!")


    async def refresh_blacklist_periodically(self):
        while True:
            await constants.refresh_blacklists()
            await asyncio.sleep(3600)


intents = discord.Intents.default()
intents.message_content = True
intents.members = True


rift = Rift(
    command_prefix=get_prefix,
    intents=intents,
    chunk_guilds_at_startup=False,
    help_command=None,
    allowed_mentions=discord.AllowedMentions(
        replied_user=True, everyone=True, roles=True
    ),
    cls=RiftContext,
)


@rift.before_invoke
async def before_invoke(ctx):
    if ctx.author.id in constants.bypassed_users:
        return
    await global_blacklist_check(ctx)


async def global_blacklist_check(ctx):
    await constants.fetch_blacklisted_users()
    await constants.fetch_blacklisted_guilds()

    if ctx.author.id in constants.blacklisted_user_ids and ctx.command.name != "unblacklist":
        
        em = discord.Embed(
            title="",
            description=f"{rift.warning} **Blacklisted User** \n\n> You are blacklisted from Rift, you can email us to check the reason for this blacklist or to request a removal at `support@riftsystems.xyz`.",
            color=constants.rift_embed_color_setup(),
        )

        await ctx.send(embed=em)
        raise commands.CheckFailure("You are blacklisted from using Rift.")


    # Check if the guild is blacklisted

    if ctx.guild and ctx.guild.id in constants.blacklisted_guild_ids and ctx.command.name != "unblacklist":
        
        em = discord.Embed(
            title="",
            description=f"{rift.warning} **Blacklisted Guild** \n\n> This server is blacklisted from Rift, you can email us to check the reason for this blacklist or to request a removal at `support@riftsystems.xyz`.",
            color=constants.rift_embed_color_setup(),
        )
        
        await ctx.send(embed=em)
        raise commands.CheckFailure("This guild is blacklisted from using Rift.")

    if ctx.guild is None:
        raise commands.NoPrivateMessage("This command cannot be used in private messages.")

    return True


def run():
    sentry_sdk.init(
        dsn=constants.sentry_dsn_setup(),
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )
    rift.run(constants.rift_token_setup())

if __name__ == "__main__":
    run()