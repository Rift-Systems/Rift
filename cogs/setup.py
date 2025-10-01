# ==========================================================================================================
# This file is for the setup and configuation of Rift and will allow you to set all the settings for your
# guild to your liking, this also can be done via the dashboard at dashboard.riftsystems.xyz
# ==========================================================================================================

import discord
from discord.ext import commands
from discord import app_commands
from utils.utils import RiftContext


class Setup(commands.Cog):
    def __init__(self, rift: commands.Bot):
        self.rift = rift
        self.logo_path = "assets/riftlogo.png" 

    # Dropdown class
    class SetupDropdown(discord.ui.Select):
        def __init__(self):
            options = [
                discord.SelectOption(
                    label="General Setup",
                    description="Begin the setup process"
                )
            ]
            super().__init__(
                placeholder="Select a setup option...",
                min_values=1,
                max_values=1,
                options=options,
            )

        async def callback(self, interaction: discord.Interaction):
            embed = discord.Embed(
                title="<:riftsystems:1421319259472003212> Setup Information",
                description=(
                    "The setup system is currently under development and not yet available.\n\n"
                    "**Need help or want updates?**\n"
                    "Join our community Discord:\n"
                    "https://discord.gg/riftsystems"
                ),
                color=0x89FFBC,
            )
            embed.set_thumbnail(url="attachment://riftlogo.png")

            file = discord.File(interaction.client.get_cog("Setup").logo_path, filename="riftlogo.png")
            await interaction.response.send_message(embed=embed, file=file, ephemeral=True)

    # View for dropdown
    class SetupView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)
            self.add_item(Setup.SetupDropdown())

    # Slash command
    @app_commands.command(name="setup", description="Run the initial setup for Rift (in progress)")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_slash(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="<:riftsystems:1421319259472003212> Rift Setup",
            description=(
                "Welcome to the Rift setup menu.\n\n"
                "Please select an option from the dropdown below to begin configuration.\n\n"
                "For detailed guides and support, visit our Discord:\n"
                "https://discord.gg/riftsystems"
            ),
            color=0x89FFBC,
        )
        embed.set_thumbnail(url="attachment://riftlogo.png")

        file = discord.File(self.logo_path, filename="riftlogo.png")
        view = self.SetupView()
        await interaction.response.send_message(embed=embed, view=view, file=file, ephemeral=False)

    @setup_slash.error
    async def setup_slash_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                f"{self.rift.error} You must be an **administrator** to use this command.",
                ephemeral=True
            )

    # Prefix command
    @commands.command(name="setup")
    @commands.has_permissions(administrator=True)
    async def setup_prefix(self, ctx: RiftContext):
        embed = discord.Embed(
            title="<:riftsystems:1421319259472003212> Rift Setup",
            description=(
                "Welcome to the Rift setup menu.\n\n"
                "Please select an option from the dropdown below to begin configuration.\n\n"
                "For detailed guides and support, visit our Discord:\n"
                "https://discord.gg/riftsystems"
            ),
            color=0x89FFBC,
        )
        embed.set_thumbnail(url="attachment://riftlogo.png")

        file = discord.File(self.logo_path, filename="riftlogo.png")
        view = self.SetupView()
        await ctx.send(embed=embed, view=view, file=file)

    @setup_prefix.error
    async def setup_prefix_error(self, ctx: RiftContext, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send_error(
                f"{self.rift.error} You must be an **administrator** to use this command."
            )


async def setup(rift: commands.Bot):
    await rift.add_cog(Setup(rift))
