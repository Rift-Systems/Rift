import discord
import time
import aiomysql
from discord import app_commands, Interaction
from discord.ui import View, Button
from discord.ext import commands
from utils.constants import RiftConstants, blacklists
from utils.utils import RiftContext
from utils.modals import BlacklistModal
from utils.pagination import GuildPaginator


constants = RiftConstants()


async def is_panel_admin(discord_id: int) -> bool:
    
    
    if not constants.pool:
        await constants.connect()
        
        
    async with constants.pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                "SELECT id FROM users WHERE oauth_id=%s AND accessLevel='Developer'",
                (discord_id,),
            )
            row = await cur.fetchone()
            return bool(row)


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



    @app_commands.command(name="blacklist")
    async def blacklist(self, interaction: discord.Interaction, entity_id: str, blacklist_type: str):
        if not constants.pool:
            await constants.connect()


        user = await interaction.client.fetch_user(int(entity_id))
        display_name = f"{user.mention}"


        async with constants.pool.acquire() as conn:
            
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    "SELECT access_level FROM users WHERE oauth_id=%s",
                    (user.id,)
                )
                
                row = await cur.fetchone()

                if row and row.get("accessLevel") == "Developer":
                    embed = discord.Embed(
                        description=f"{self.rift.error} You cannot blacklist another **Developer** or **Administrator**.",
                        color=self.rift.base_color,
                    )
                    return await interaction.response.send_message(embed=embed, ephemeral=True)


        modal = BlacklistModal(self.rift, int(entity_id), display_name, blacklist_type)
        await interaction.response.send_modal(modal)
        
        
        
    @app_commands.command(name="unblacklist")
    async def unblacklist(self, interaction: Interaction, entity_id: str):
        
        
        await interaction.response.defer(ephemeral=True)


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
                    "SELECT * FROM blacklists WHERE discord_id=%s",
                    (entity_id_int)
                )
                
                
                row = await cur.fetchone()


                if not row:
                    embed = discord.Embed(
                        description=f"{self.rift.error} {display} is not actively blacklisted.",
                        color=self.rift.base_color,
                    )
                    return await interaction.followup.send(embed=embed, ephemeral=True)


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
                    WHERE discord_id=%s AND blacklist_status='Active'
                    """,
                    (entity_id_int)
                )

            await conn.commit()


        embed = discord.Embed(
            description=f"{self.rift.success} **{display}** has been **unblacklisted**.",
            color=self.rift.base_color,
        )
        
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    
    
    @commands.command()
    async def sync(self, ctx: RiftContext, guild_id: int = None):
        if guild_id:
            guild = discord.Object(id=guild_id)
            synced = await self.rift.tree.sync(guild=guild)
        else:
            synced = await self.rift.tree.sync()
        await ctx.send_success(f"Synced **{len(synced)}** commands.")



async def setup(rift):
    await rift.add_cog(AdminCommandsCog(rift))
