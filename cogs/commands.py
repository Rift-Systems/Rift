import discord
import time
import datetime
import asyncio
import pytz
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
        formatted_time = command_run_time.strftime("Today at %I:%M %p UTC")


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
            command_run_time=formatted_time,
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
        database_latency = await self.get_db_latency()
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
            latency, database_latency, uptime, shard_info, page=0
        )
        
        
        view = PingPaginationView(self.rift, latency, database_latency, uptime, shard_info)
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

# ---------------------------------------------------------------
# USERINFO COMMAND FOR DISCORD
# ---------------------------------------------------------------
@commands.hybrid_command(
    name="userinfo",
    description="Get information about a user.",
    with_app_command=True,
    extras={"category": "General"},
)
async def userinfo(self, ctx: RiftContext, member: discord.User = None):
    member = member or ctx.author

    # Account Creation
    created_at = member.created_at.replace(tzinfo=datetime.timezone.utc)
    created_fmt = created_at.strftime("%B %d, %Y %I:%M %p")
    created_ago = self._time_ago(created_at)

    # Server Join (if applicable)
    joined_fmt = None
    joined_ago = None
    if isinstance(member, discord.Member):
        if member.joined_at:
            joined_at = member.joined_at.replace(tzinfo=datetime.timezone.utc)
            joined_fmt = joined_at.strftime("%B %d, %Y %I:%M %p")
            joined_ago = self._time_ago(joined_at)

    # Build Embed
    embed = discord.Embed(
        title=f"{member.name}#{member.discriminator}",
        description=f"User information for **{member.display_name}**",
        color=0x89ffbc,
    )
    embed.set_thumbnail(url=member.display_avatar.url)

    embed.add_field(name="ID", value=str(member.id), inline=False)
    embed.add_field(
        name="Created On", 
        value=f"{created_fmt} ({created_ago})", 
        inline=False
    )

    if joined_fmt and joined_ago:
        embed.add_field(
            name="Joined Server On", 
            value=f"{joined_fmt} ({joined_ago})", 
            inline=False
        )

    if isinstance(member, discord.Member):
        roles = [role.mention for role in member.roles if role.name != "@everyone"]
        embed.add_field(
            name="Roles", 
            value=", ".join(roles) if roles else "None", 
            inline=False
        )

    embed.set_footer(
        text=f"Requested at {datetime.now().strftime('%B %d, %Y %I:%M %p')}"
    )

    await ctx.send(embed=embed)


def _time_ago(self, dt: datetime):
    """Return human-readable time difference."""
    now = datetime.now(datetime.timezone.utc)
    delta = now - dt

    days, seconds = delta.days, delta.seconds
    years, days = divmod(days, 365)
    months, days = divmod(days, 30)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    parts = []
    if years > 0:
        parts.append(f"{years} year{'s' if years != 1 else ''}")
    if months > 0:
        parts.append(f"{months} month{'s' if months != 1 else ''}")
    if days > 0:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if seconds > 0 and not parts:
        parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")

    return ", ".join(parts) + " ago"


async def setup(rift):
    await rift.add_cog(CommandsCog(rift))