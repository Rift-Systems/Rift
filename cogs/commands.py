# ==========================================================================================================
# This file contains basic commands for the bot that every bot should have such as about, ping, say, etc.
# ==========================================================================================================

import discord
import time
import datetime
import asyncio
import pytz
import aiomysql
from datetime import datetime
from discord.ext import commands
from utils.constants import RiftConstants
from utils.embeds import (
    AboutEmbed,
    AboutWithButtons,
    PingCommandEmbed,
    PrefixEmbed,
    PrefixSuccessEmbed,
    PrefixSuccessEmbedNoneChanged,
)
from utils.pagination import PingPaginationView
from utils.utils import RiftContext
from utils.modals import AddUserModal

constants = RiftConstants()

class CommandsCog(commands.Cog):
    def __init__(self, rift):
        self.rift = rift


    @commands.hybrid_command(
        description="Provides important information about Rift.",
        with_app_command=True,
        extras={"category": "Other"},
    )
    async def about(self, ctx: RiftContext):
        
        await ctx.defer(ephemeral=True)

        uptime_formatted = f"<t:{int((self.rift.start_time.timestamp()))}:R>"
        guilds = len(self.rift.guilds)
        users = sum(g.member_count for g in self.rift.guilds)
        shards = self.rift.shard_count or 1
        cluster = 0
        environment = constants.rift_environment_type() or "Unknown"
        version = await constants.get_mysql_version()
        command_run_time = datetime.now()

        embed = AboutEmbed.create_info_embed(
            uptime=self.rift.start_time,
            guilds=guilds,
            users=users,
            latency=self.rift.latency,
            version=version,
            bot_name=ctx.guild.name,
            bot_icon=ctx.guild.icon,
            shards=shards,
            cluster=cluster,
            environment=environment,
            command_run_time=command_run_time,
            thumbnail_url="https://media.discordapp.net/attachments/1421354662967115928/1421382112833048606/RiftSquareLogo.png?ex=68d8d4bf&is=68d7833f&hm=0bf8d3177eb55c9cd883c1032da6a8d861afbac1157eb735aa15fc20a5b5eb5e&=&format=webp&quality=lossless",
        )

        view = AboutWithButtons.create_view()
        await ctx.send(embed=embed, view=view)


    async def get_db_latency(self):
        
        try:
            start_time = time.time()
            await constants.ping_db()
            db_latency = round((time.time() - start_time) * 1000)
            return db_latency
        
        except Exception as e:
            print(f"Error measuring DB latency: {e}")
            return -1


    @commands.hybrid_command(name="ping", description="Check the bot's latency, uptime, and shard info.", with_app_command=True, extras={"category": "Other"},)
    async def ping(self, ctx: RiftContext):
        
        latency = self.rift.latency
        db_connected = await constants.is_db_connected()
        uptime = self.rift.start_time
        shard_info = []
        
        for shard_id, shard in self.rift.shards.items():
            shard_info.append(
                {
                    "id": shard_id,
                    "latency": round(shard.latency * 1000),
                    "guilds": len([g for g in self.rift.guilds if g.shard_id == shard_id]),
                }
            )

        embed = PingCommandEmbed.create_ping_embed(
            latency, db_connected, uptime, shard_info, page=0
        )
        
        view = PingPaginationView(self.rift, latency, db_connected, uptime, shard_info)
        await ctx.send(embed=embed, view=view)


    @commands.hybrid_command(description="Use this command to say things to people using the bot.", with_app_command=True, extras={"category": "General"},)
    @commands.has_permissions(administrator=True)
    async def say(self, ctx, *, message: str):
        
        if ctx.interaction:
            await ctx.send("sent", allowed_mentions=discord.AllowedMentions.none(), ephemeral=True)
            await ctx.channel.send(message, allowed_mentions=discord.AllowedMentions.none())
            
        else:
            await ctx.channel.send(message, allowed_mentions=discord.AllowedMentions.none())
            await ctx.message.delete()


async def setup(rift):
    await rift.add_cog(CommandsCog(rift))

# hi