import discord
import logging

from discord.ext import commands
from utils.embeds import OnCommandEmbed
from utils.constants import statistics

class OnCommand(commands.Cog):
    def __init__(self, rift):
        self.rift = rift

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context):        
        log_channel_id = 1421575045813370890
        channel = ctx.guild.get_channel(log_channel_id)
    
        embed = OnCommandEmbed.create_on_command_embed(
            command_name = ctx.command.qualified_name,
            user = ctx.author,
            guild = ctx.guild,
            channel = ctx.channel,
            timestamp = ctx.message.created_at,
            args = ctx.args,
        )

        await channel.send(embed=embed)
            
async def setup(rift):
    await rift.add_cog(OnCommand(rift))