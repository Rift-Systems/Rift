import discord
import aiomysql
import secrets
import hashlib
from discord.ui import Modal, TextInput
from utils.constants import RiftConstants

constants = RiftConstants()

class InteractionContextAdapter:
    def __init__(self, interaction: discord.Interaction, bot):
        self.interaction = interaction
        self.bot = bot

    async def send_success(self, message: str, ephemeral: bool = False):
        
        embed = discord.Embed(
            description=f"{self.bot.success} {message}",
            color=self.bot.base_color,
        )
        
        try:
            await self.interaction.response.send_message(embed=embed, ephemeral=ephemeral)
        except discord.errors.InteractionAlreadyResponded:
            await self.interaction.followup.send(embed=embed, ephemeral=ephemeral)


    async def send_error(self, message: str, ephemeral: bool = False):
        
        embed = discord.Embed(
            description=f"{self.bot.error} {message}",
            color=self.bot.base_color,
        )
        
        try:
            await self.interaction.response.send_message(embed=embed, ephemeral=ephemeral)
        except discord.errors.InteractionAlreadyResponded:
            await self.interaction.followup.send(embed=embed, ephemeral=ephemeral)


async def process_blacklist_db(data: dict):
    if not constants.pool:
        await constants.connect()

    try:
        case_id = getattr(constants, "generate_case_id", lambda: None)()
        is_guild = (data.get("entity_type") == "guild")
        discord_id = None if is_guild else int(data["entity_id"])
        guild_id = str(data["entity_id"]) if is_guild else None

        async with constants.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    """
                    INSERT INTO blacklists
                    (discord_id, guild_id, blacklist_title, blacklist_description,
                     blacklist_type, blacklist_date, blacklist_updated_date, blacklist_status)
                    VALUES (%s, %s, %s, %s, %s, NOW(), NOW(), 'Active')
                    """,
                    (discord_id, guild_id, data["title"], data["description"], data["btype"])
                )

                if not is_guild and discord_id is not None:
                    await cur.execute("SELECT id FROM users WHERE oauth_id=%s", (discord_id,))
                    user_row = await cur.fetchone()
                    if user_row:
                        await cur.execute(
                            """
                            UPDATE users
                            SET status='Terminated',
                                status_reason=%s,
                                status_date=NOW()
                            WHERE oauth_id=%s
                            """,
                            ("This user has been blacklisted because they have been using the bot improperly.", discord_id)
                        )

            await conn.commit()

        return case_id

    except Exception as e:
        print(f"[ERROR] Failed to process blacklist DB: {e}")
        raise


class BlacklistModal(discord.ui.Modal):
    def __init__(self, bot, entity_id: int | str, entity_display: str, btype: str, entity_type: str):
        super().__init__(title="Submit new blacklist")
        self.bot = bot
        self.entity_id = entity_id
        self.entity_display = entity_display
        self.btype = btype
        self.entity_type = entity_type
        self.title_input = discord.ui.TextInput(label="Title", max_length=255)
        self.description_input = discord.ui.TextInput(
            label="Description", style=discord.TextStyle.paragraph, max_length=2000
        )
        self.add_item(self.title_input)
        self.add_item(self.description_input)


    async def on_submit(self, interaction: discord.Interaction):
        data = {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "title": self.title_input.value,
            "description": self.description_input.value,
            "btype": self.btype,
        }

        ctx = InteractionContextAdapter(interaction, interaction.client)
        
        try:
            _ = await process_blacklist_db(data)
            await ctx.send_success(f"{self.entity_display} has been **blacklisted** from Rift Systems.")
        
        except Exception as e:
            await ctx.send_error(f"Failed to process blacklist because of an error \n`{e}`")
            
            
class AddUserModal(discord.ui.Modal, title="Add Panel User"):
    def __init__(self, target_user_id: int):
        super().__init__()
        self.target_user_id = target_user_id

        self.username_input = discord.ui.TextInput(
            label="Username",
            max_length=255,
            placeholder="example@company.com or username",
            required=True,
        )
        self.display_name_input = discord.ui.TextInput(
            label="Display name",
            max_length=255,
            placeholder="Jane Doe",
            required=True,
        )

        self.add_item(self.username_input)
        self.add_item(self.display_name_input)


    async def on_submit(self, interaction: discord.Interaction):
        password_hex = hashlib.sha512(secrets.token_bytes(32)).hexdigest()

        if not constants.pool:
            await constants.connect()

        try:
            async with constants.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    await cur.execute("SELECT id FROM users WHERE oauth_id=%s", (str(self.target_user_id),))
                    if await cur.fetchone():
                        embed = discord.Embed(
                            description=f"{interaction.client.error} A user with oauth_id `{self.target_user_id}` already exists.",
                            color=interaction.client.base_color,
                        )
                        return await interaction.response.send_message(embed=embed, ephemeral=True)

                    await cur.execute(
                        """
                        INSERT INTO users
                        (username, password, display_name, status, status_reason, status_date, oauth_id, access_level)
                        VALUES (%s, %s, %s, 'Active', '', CURDATE(), %s, 'User')
                        """,
                        (
                            self.username_input.value.strip(),
                            password_hex,
                            self.display_name_input.value.strip(),
                            str(self.target_user_id),
                        )
                    )
                await conn.commit()

            embed = discord.Embed(
                description=f"{interaction.client.success} Created panel user **{self.display_name_input.value.strip()}** (`{self.username_input.value.strip()}`) for <@{self.target_user_id}>.",
                color=interaction.client.base_color,
            )
            await interaction.response.send_message(embed=embed, ephemeral=False)


        except Exception as e:
            embed = discord.Embed(
                description=f"{interaction.client.error} Failed to create user.\n`{e}`",
                color=interaction.client.base_color,
            )
            try:
                await interaction.response.send_message(embed=embed, ephemeral=True)
            except discord.errors.InteractionAlreadyResponded:
                await interaction.followup.send(embed=embed, ephemeral=True)