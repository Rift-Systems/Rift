import discord
from discord.ext import tasks, commands
from utils.utils import RiftContext


class Tasks(commands.Cog):
    def __init__(self, rift):
        self.rift = rift
        self.change_status.start()


    @tasks.loop(seconds=30)
    async def change_status(self):
        guild_count = len(self.rift.guilds)
        user_count = sum(guild.member_count for guild in self.rift.guilds)

        await self.rift.change_presence(
            activity=discord.Activity(
                name=f"{guild_count} Guilds • {user_count:,} Users • /help",
                type=discord.ActivityType.watching,
            )
        )


async def setup(rift):
    await rift.add_cog(Tasks(rift))