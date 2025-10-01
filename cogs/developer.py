<<<<<<< HEAD
=======
<<<<<<< HEAD
=======
>>>>>>> f7e77aa (Squashed commit of the following:)
# ==========================================================================================================
# This file is for developer only commands such as dev_add and dev_remove as well as sync and some others.
# ==========================================================================================================

<<<<<<< HEAD
=======
>>>>>>> keep-current
>>>>>>> f7e77aa (Squashed commit of the following:)
import re
import discord
import time
import aiomysql
from discord import app_commands, Interaction
from discord.ui import View, Button
from discord.ext import commands
from discord.app_commands import Choice
from utils.constants import RiftConstants, blacklists
from utils.utils import RiftContext
from utils.modals import BlacklistModal
from utils.pagination import GuildPaginator

constants = RiftConstants()

CONTROL_GUILD_ID = 1420889056174411898
CONTROL_ROLE_IDS = [1421267029960167614, 1421279981220135024]

async def is_panel_admin(discord_id: int) -> bool:
    
    if not constants.pool:
        await constants.connect()
        
    async with constants.pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                "SELECT id FROM users WHERE oauth_id=%s AND access_level='Developer'",
                (discord_id,),
            )
            row = await cur.fetchone()
            return bool(row)
        
        
def has_any_control_role(member: discord.Member) -> bool:
    user_role_ids = {r.id for r in member.roles}
    return any(rid in user_role_ids for rid in CONTROL_ROLE_IDS)


class AdminCommandsCog(commands.Cog):
    def __init__(self, rift):
        self.rift = rift


    @commands.command()
    async def checkguild(self, ctx: RiftContext, guild_id: int):
        await ctx.send_success(f"Checkguild command received for ID: `{guild_id}`")


    @commands.command()
    async def guildlist(self, ctx: RiftContext):
        guilds = sorted(ctx.rift.guilds, key=lambda g: -g.member_count)
        view = GuildPaginator(ctx, guilds)
        await view.send()


    @commands.command()
    async def guildinvite(self, ctx: RiftContext, guild_id: int):
        guild = ctx.rift.get_guild(guild_id)
        if not guild:
            return await ctx.send_error("I am not in that guild.")
        invite = None
        for channel in guild.text_channels:
            try:
                invite = await channel.create_invite(max_age=300, max_uses=1, unique=True)
                break
            except Exception:
                continue
        if not invite:
            return await ctx.send_error("I could not create an invite for that guild.")
        await ctx.send_success(f"Here is a temporary invite to **{guild.name}**: {invite.url}")


    @app_commands.command(name="blacklist", description="Blacklist a user or a guild.")
    @app_commands.describe(entity_id="User ID (snowflake) or Guild ID (string of digits)", target_type="Choose whether you're blacklisting a user or a guild")
    @app_commands.choices(target_type=[Choice(name="User", value="user"), Choice(name="Guild", value="guild"),])
    async def blacklist(self, interaction: discord.Interaction, entity_id: str, target_type: Choice[str]):

        target = target_type.value
        display_name = None
        blacklist_type=target.capitalize()
        
        if target == "user":
            try:
                user = await interaction.client.fetch_user(int(entity_id))
                display_name = user.mention
            except Exception:
                display_name = f"User `{entity_id}`"

            try:
                uid = int(entity_id)
                if await self._is_developer(uid):
                    embed = discord.Embed(
                        description=f"{self.rift.error} You cannot blacklist another **Developer** or **Administrator**.",
                        color=self.rift.base_color,
                    )
                    return await interaction.response.send_message(embed=embed, ephemeral=True)
            except ValueError:
                embed = discord.Embed(
                    description=f"{self.rift.error} `{entity_id}` is not a valid user ID.",
                    color=self.rift.base_color,
                )
                return await interaction.response.send_message(embed=embed, ephemeral=True)

        else:
            try:
                g = interaction.client.get_guild(int(entity_id))
                display_name = f"**{g.name}** (`{g.id}`)" if g else f"Guild `{entity_id}`"
            except ValueError:
                embed = discord.Embed(
                    description=f"{self.rift.error} `{entity_id}` is not a valid guild ID.",
                    color=self.rift.base_color,
                )
                return await interaction.response.send_message(embed=embed, ephemeral=True)

        modal = BlacklistModal(
            self.rift,
            entity_id=entity_id,
            entity_display=display_name,
            btype=blacklist_type,
            entity_type=target
        )
        
        await interaction.response.send_modal(modal)
        
        
    @app_commands.command(name="unblacklist")
    async def unblacklist(self, interaction: Interaction, entity_id: str):
        
        await interaction.response.defer(ephemeral=False)

        if not constants.pool:
            await constants.connect()

        try:
            entity_user = await self.rift.fetch_user(int(entity_id))
            entity_type, entity_id_int, display = "user", entity_user.id, entity_user.mention
        except Exception:
            entity_type, entity_id_int, display = "guild", entity_id, f"Guild `{entity_id}`"

        async with constants.pool.acquire() as conn:
            
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    "SELECT * FROM blacklists WHERE (discord_id = %s OR guild_id = %s) AND blacklist_status='Active' LIMIT 1",
                    (entity_id_int, entity_id_int)
                )
                
                row = await cur.fetchone()

                if not row:
                    embed = discord.Embed(
                        description=f"{self.rift.error} {display} is not actively blacklisted.",
                        color=self.rift.base_color,
                    )
                    return await interaction.followup.send(embed=embed)

                if entity_type == "user":
                    await cur.execute("SELECT username FROM users WHERE oauth_id=%s", (entity_id_int,))
                    user_row = await cur.fetchone()
                    if user_row and user_row.get("username"):
                        email = user_row["username"]
                        await cur.execute(
                            """
                            UPDATE users
                            SET status='Active'
                            WHERE oauth_id=%s
                            """,
                            (entity_id_int,)
                        )

                await cur.execute(
                    """
                    UPDATE blacklists
                    SET blacklist_status='Cleared',
                        blacklist_updated_date=NOW()
                    WHERE (discord_id = %s OR guild_id = %s) AND blacklist_status='Active'
                    """,
                    (entity_id_int, entity_id_int)
                )

            await conn.commit()

        embed = discord.Embed(
            description=f"{self.rift.success} **{display}** has been **unblacklisted**.",
            color=self.rift.base_color,
        )
        
        await interaction.followup.send(embed=embed, ephemeral=False)
    
    
    @commands.command()
    async def sync(self, ctx: RiftContext, guild_id: int = None):
        if guild_id:
            guild = discord.Object(id=guild_id)
            synced = await self.rift.tree.sync(guild=guild)
        else:
            synced = await self.rift.tree.sync()
        await ctx.send_success(f"Synced **{len(synced)}** commands.")        
        
        
    @commands.command()
    @commands.guild_only()
    async def dev_add(self, ctx: RiftContext, target: discord.User):
        if not ctx.guild or ctx.guild.id != CONTROL_GUILD_ID:
            return await ctx.send_error("This command can only be used in the **Rift Systems** guild.")
        
        if not any(ctx.guild.get_role(rid) for rid in CONTROL_ROLE_IDS):
            roles_list = " ".join(f"<@&{rid}>" for rid in CONTROL_ROLE_IDS)
            return await ctx.send_error(
                f"None of the configured control roles exist in this guild. Expected one of: {roles_list}"
            )

        if not has_any_control_role(ctx.author):
            roles_list = " ".join(f"<@&{rid}>" for rid in CONTROL_ROLE_IDS)
            return await ctx.send_error(
                f"You don't have a required role to use this command. You need one of: {roles_list}"
            )
        
        if not await is_panel_admin(ctx.author.id):
            return await ctx.send_error("You don't have panel admin permissions.")

        target_id = target.id
        display = target.mention

        if not constants.pool:
            await constants.connect()

        async with constants.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                
                await cur.execute("SELECT id, access_level FROM users WHERE oauth_id=%s", (target_id,))
                row = await cur.fetchone()
                
                if not row:
                    return await ctx.send_error(f"{display} does not exist in the `users` table (oauth_id={target_id}).")

                if (row.get("access_level") or "").lower() == "developer":
                    return await ctx.send_success(f"{display} is already a **Developer**.")

                await cur.execute(
                    "UPDATE users SET access_level='Developer' WHERE oauth_id=%s",
                    (target_id,)
                )
                
            await conn.commit()

        await ctx.send_success(f"Granted **Developer** access to {display}.")


    @commands.command()
    @commands.guild_only()
    async def dev_remove(self, ctx: RiftContext, target: discord.User):
        
        if not ctx.guild or ctx.guild.id != CONTROL_GUILD_ID:
            return await ctx.send_error("This command can only be used in the control guild.")
        
        if not any(ctx.guild.get_role(rid) for rid in CONTROL_ROLE_IDS):
            roles_list = " ".join(f"<@&{rid}>" for rid in CONTROL_ROLE_IDS)
            return await ctx.send_error(
                f"None of the configured control roles exist in this guild. Expected one of: {roles_list}"
            )

        if not has_any_control_role(ctx.author):
            roles_list = " ".join(f"<@&{rid}>" for rid in CONTROL_ROLE_IDS)
            return await ctx.send_error(
                f"You don't have a required role to use this command. You need one of: {roles_list}"
            )
        
        if not await is_panel_admin(ctx.author.id):
            return await ctx.send_error("You don't have panel admin permissions.")

        target_id = target.id
        display = target.mention

        if not constants.pool:
            await constants.connect()

        async with constants.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("SELECT id, access_level FROM users WHERE oauth_id=%s", (target_id,))
                
                row = await cur.fetchone()
                
                if not row:
                    return await ctx.send_error(f"{display} does not exist in the `users` table (oauth_id={target_id}).")

                if (row.get("access_level") or "").lower() != "developer":
                    return await ctx.send_success(f"{display} is not a **Developer**.")

                await cur.execute(
                    "UPDATE users SET access_level='User' WHERE oauth_id=%s",
                    (target_id,)
                )
            await conn.commit()

        await ctx.send_success(f"Revoked **Developer** access from {display} (set to **User**).")
        
        
    @commands.hybrid_group(name="panel", with_app_command=True, description="This command group will allow you to add user to the panel and remove users from the panel.")
    async def panel(self, ctx: RiftContext):
        if ctx.invoked_subcommand is None:
            return await ctx.send_error("Use a subcommand: `/panel add` or `/panel remove`.")
        
    
    @panel.command(name="add", description="Creates a panel user for the target.")
    async def panel_add_user(self, ctx: RiftContext, target: discord.User):
        
        if not ctx.guild or ctx.guild.id != CONTROL_GUILD_ID:
            return await ctx.send_error("This command can only be used in the control guild.")
        
        if not any(ctx.guild.get_role(rid) for rid in CONTROL_ROLE_IDS):
            roles_list = " ".join(f"<@&{rid}>" for rid in CONTROL_ROLE_IDS)
            return await ctx.send_error(
                f"None of the configured control roles exist in this guild. Expected one of: {roles_list}"
            )

        if not has_any_control_role(ctx.author):
            roles_list = " ".join(f"<@&{rid}>" for rid in CONTROL_ROLE_IDS)
            return await ctx.send_error(
                f"You don't have a required role to use this command. You need one of: {roles_list}"
            )
        
        if not await is_panel_admin(ctx.author.id):
            return await ctx.send_error("You don't have panel admin permissions.")
        
        if ctx.interaction is None:
            return await ctx.send_error("Use the **slash** command `/panel add` to open the modal.")
        
        modal = AddUserModal(target_user_id=target.id)
        await ctx.interaction.response.send_modal(modal)


    @panel.command(name="remove", description="Removes a panel user for the target")
    async def panel_remove_user(self, ctx: RiftContext, target: discord.User):
        
        if not ctx.guild or ctx.guild.id != CONTROL_GUILD_ID:
            return await ctx.send_error("This command can only be used in the control guild.")
        
        if not any(ctx.guild.get_role(rid) for rid in CONTROL_ROLE_IDS):
            roles_list = " ".join(f"<@&{rid}>" for rid in CONTROL_ROLE_IDS)
            return await ctx.send_error(
                f"None of the configured control roles exist in this guild. Expected one of: {roles_list}"
            )

        if not has_any_control_role(ctx.author):
            roles_list = " ".join(f"<@&{rid}>" for rid in CONTROL_ROLE_IDS)
            return await ctx.send_error(
                f"You don't have a required role to use this command. You need one of: {roles_list}"
            )
        
        if not await is_panel_admin(ctx.author.id):
            return await ctx.send_error("You don't have panel admin permissions.")
        
        target_id = target.id
        display = target.mention

        if not constants.pool:
            await constants.connect()

        async with constants.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("SELECT id FROM users WHERE oauth_id=%s", (target_id,))
                row = await cur.fetchone()
                if not row:
                    return await ctx.send_error(f"{display} does not exist in the `users` table (oauth_id={target_id}).")

                await cur.execute(
                    """
                    UPDATE users
                    SET status='Terminated',
                        status_reason='Removed by admin',
                        status_date=CURDATE()
                    WHERE oauth_id=%s
                    """,
                    (target_id,)
                )
            await conn.commit()

        await ctx.send_success(f"Marked **{display}** as **Terminated**.")


async def setup(rift):
    await rift.add_cog(AdminCommandsCog(rift))
