import discord
import aiomysql
from discord.ui import Modal, TextInput
from utils.constants import RiftConstants


constants = RiftConstants()


# Custom interation handler for the embed system that I made to allow a ctx.send_success system
# to exist for interactions as well.

class InteractionContextAdapter:
    
    
    def __init__(self, interaction: discord.Interaction, bot):
        self.interaction = interaction
        self.bot = bot


    async def send_success(self, message: str, ephemeral=True):
        
        embed = discord.Embed(
            description=f"{self.bot.success} {message}",
            color=self.bot.base_color,
        )
        
        try:
            await self.interaction.response.send_message(embed=embed, ephemeral=ephemeral)
            
        except discord.errors.InteractionAlreadyResponded:
            await self.interaction.followup.send(embed=embed, ephemeral=ephemeral)


    async def send_error(self, message: str, ephemeral=True):
        embed = discord.Embed(
            description=f"{self.bot.error} {message}",
            color=self.bot.base_color,
        )
        try:
            await self.interaction.response.send_message(embed=embed, ephemeral=ephemeral)
        except discord.errors.InteractionAlreadyResponded:
            await self.interaction.followup.send(embed=embed, ephemeral=ephemeral)



# This is the entire blacklsit submission logic to check information and send it to the MySQL database. 

async def process_blacklist_db(data: dict):
    
    
    if not constants.pool:
        await constants.connect()


    try:
        
        case_id = constants.generate_case_id()
        
        async with constants.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                
                await cur.execute(
                    """
                    INSERT INTO blacklists
                    (discord_id, blacklist_title, blacklist_description, blacklist_type, blacklist_date, blacklist_updated_date, blacklist_status)
                    VALUES (%s, %s, %s, %s, NOW(), NOW(), 'Active')
                    """,
                    (data["entity_id"], data["title"], data["description"], data["btype"])
                )

                await cur.execute("SELECT * FROM users WHERE oauth_id=%s", (data["entity_id"],))
                
                user_row = await cur.fetchone()

                if user_row:
                    email = user_row["username"]

                    await cur.execute(
                        """
                        UPDATE users
                        SET status='Terminated',
                            status_reason=%s,
                            status_date=NOW()
                        WHERE oauth_id=%s
                        """,
                        (f"This user has been blacklisted because they have been using the bot improperly.", data["entity_id"])
                    )

            await conn.commit()
            
        return case_id


    except Exception as e:
        print(f"[ERROR] Failed to process blacklist DB: {e}")
        raise



# This is the rendering of the blacklist submission modal. We handle DB operations sepetealy to prevent
# timing out and getting a response for discord within the 3 second time limit.

class BlacklistModal(discord.ui.Modal):
    def __init__(self, bot, entity_id: int, entity_display: str, btype: str):
        super().__init__(title=f"Submit new blacklist")
        self.bot = bot
        self.entity_id = entity_id
        self.entity_display = entity_display
        self.btype = btype

        self.title_input = discord.ui.TextInput(label="Title", max_length=255)
        self.description_input = discord.ui.TextInput(
            label="Description", style=discord.TextStyle.paragraph, max_length=2000
        )
        self.add_item(self.title_input)
        self.add_item(self.description_input)


    async def on_submit(self, interaction: discord.Interaction):
        data = {
            "entity_id": self.entity_id,
            "entity_display": self.entity_display,
            "btype": self.btype,
            "title": self.title_input.value,
            "description": self.description_input.value
        }


        ctx = InteractionContextAdapter(interaction, interaction.client)
        
        
        try:
            case_id = await process_blacklist_db(data)
            await ctx.send_success(f"The user {self.entity_display} has been **blacklisted** from Rift because {self.description_input.value}")
       
       
        except Exception as e:
            await ctx.send_error(f"Failed to process blacklist because of an error \n`{e}`")