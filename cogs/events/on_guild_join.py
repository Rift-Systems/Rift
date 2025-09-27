import discord

from discord.ext import commands
from utils.constants import RiftConstants
from utils.utils import RiftContext
from utils.embeds import OnGuildEmbed

constants = RiftConstants()

class OnGuildJoin(commands.Cog):
    def __init__(self, rift):
        self.rift = rift

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        if constants.rift_environment_type() == "Development":
            return

        channel = self.rift.get_channel(1421554689509687347)

        embed = OnGuildEmbed.create_guild_join_embed(
            guild,
            current_guild_count=len(self.rift.guilds),
        )

        await channel.send(embed=embed)