import discord
from discord.ext import commands
from utils.constants import RiftConstants
import os
from dotenv import load_dotenv


constants = RiftConstants()


async def get_prefix(rift, message):
    if not message.guild:
        return constants.default_prefix

    prefix = await constants.get_prefix(message.guild.id)

    if not prefix:
        load_dotenv()
        prefix = os.getenv("PREFIX", "!")

    return commands.when_mentioned_or(prefix)(rift, message)



class RiftContext(commands.Context):
    @property
    def rift(self):
        return self.bot


    async def send_success(self, message: str):
        embed = discord.Embed(
            description=f"{self.rift.success} {message}",
            color=self.rift.base_color,
        )
        return await super().send(embed=embed, reference=self.message)


    async def send_error(self, message: str):
        embed = discord.Embed(
            description=f"{self.rift.error} {message}",
            color=self.rift.base_color,
        )
        return await super().send(embed=embed, reference=self.message)


    async def send_loading(self, message: str):
        embed = discord.Embed(
            description=f"{self.rift.loading} {message}",
            color=0x2A2C31,
        )
        return await super().send(embed=embed, reference=self.message)


    async def send_warning(self, message: str):
        embed = discord.Embed(
            description=f"{self.rift.warning} {message}",
            color=self.rift.base_color,
        )
        return await super().send(embed=embed, reference=self.message)


    async def send_normal(self, message: str):
        embed = discord.Embed(
            description=message,
            color=self.rift.base_color,
        )
        return await super().send(embed=embed, reference=self.message)
