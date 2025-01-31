import os
import discord
from discord.ext import commands, tasks
from discord import app_commands
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
import asyncio
import time
import shutil

# Load sensitive information from .env
load_dotenv()
TOKEN1 = os.getenv("DISCORD_TOKEN1")
YOUR_DISCORD_ID = int(os.getenv("YOUR_DISCORD_ID"))
GUILD_ID = int(os.getenv("GUILD_ID"))

# Load channel IDs from .env
TOP3_CHANNEL_ID = int(os.getenv("TOP3_CHANNEL_ID"))
TOP10_CHANNEL_ID = int(os.getenv("TOP10_CHANNEL_ID"))

DB_CONFIG = {
    "host": "191.96.229.15",
    "user": "u1_9TO8L1QmCN",
    "password": "K=+FRwP6CuoI+eh@PP4F5XTD",
    "database": "s1_s87_Itay",
    "connection_timeout": 30
}

# Helper function to connect to the database
def get_database_connection(retries=3, delay=5):
    for attempt in range(retries):
        try:
            print(f"Trying to connect to the database... (Attempt {attempt + 1})")
            connection = mysql.connector.connect(**DB_CONFIG)
            if connection.is_connected():
                print("Successfully connected to the database!")
                return connection
        except Error as e:
            print(f"Error connecting to database (Attempt {attempt + 1}): {e}")
            if attempt < retries - 1:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
    print(f"Failed to connect to database after {retries} attempts.")
    return None

# Fetch player data
def fetch_player_data(identifier):
    query = """SELECT steamid, exp, exp2, exp3, name FROM todayinfo WHERE steamid = %s OR name LIKE %s"""
    connection = get_database_connection()
    if connection is None:
        return None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, (identifier, f"%{identifier}%"))
        result = cursor.fetchone()
        cursor.close()
        return result
    except Error as e:
        print(f"Error executing query: {e}")
        return None
    finally:
        if connection.is_connected():
            connection.close()

# Fetch top players data
def fetch_top_players(limit):
    query = "SELECT name, kills, deaths, hs FROM csstatsx2 ORDER BY kills DESC LIMIT %s"
    connection = get_database_connection()
    if connection is None:
        return []
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, (limit,))
        result = cursor.fetchall()
        cursor.close()
        return result
    except Error as e:
        print(f"Error executing query: {e}")
        return []
    finally:
        if connection.is_connected():
            connection.close()

# Generate player embed for top 3 / top 10
def generate_top_embed(title, players, emoji, thumbnail_url):
    embed = discord.Embed(
        title=title,
        color=discord.Color.gold(),
        description="🏅 רשימת השחקנים המובילים"
    )
    embed.set_thumbnail(url=thumbnail_url)
    for index, player in enumerate(players, start=1):
        embed.add_field(
            name=f"{emoji} מקום {index}: {player['name']}",
            value=(f"**🔫 Kills:** {player['kills']} | "
                   f"**☠️ Deaths:** {player['deaths']} | "
                   f"**🎯 Headshots:** {player['hs']}"),
            inline=False
        )
    embed.set_footer(text="עודכן אוטומטית", icon_url="https://cdn-icons-png.flaticon.com/512/1828/1828884.png")
    return embed

# Bot 1 configuration
intents1 = discord.Intents.default()
bot1 = commands.Bot(command_prefix='!', intents=intents1)

top3_message = None
top10_message = None

@bot1.event
async def on_ready():
    print(f'Bot 1 Logged in as {bot1.user}')
    try:
        guild = discord.Object(id=GUILD_ID)
        await bot1.tree.sync(guild=guild)
        print(f"Slash commands synced for guild {GUILD_ID}.")
    except Exception as e:
        print(f"Error syncing slash commands: {e}")

    update_top_players.start()
    #check_owner_presence.start()  # Start the check for owner's presence every 5 hours

@tasks.loop(minutes=5)
async def update_top_players():
    global top3_message, top10_message
    try:
        print("Fetching top 3 players...")
        top3_channel = bot1.get_channel(TOP3_CHANNEL_ID)
        top3_players = fetch_top_players(3)
        top3_embed = generate_top_embed(
            "שלושת השחקנים הטובים ביותר",
            top3_players,
            "🥇",
            "https://cdn-icons-png.flaticon.com/512/2278/2278992.png"
        )

        if top3_message is None:
            print("Sending top 3 message...")
            top3_message = await top3_channel.send(embed=top3_embed)
        else:
            print("Editing top 3 message...")
            await top3_message.edit(embed=top3_embed)

        print("Fetching top 10 players...")
        top10_channel = bot1.get_channel(TOP10_CHANNEL_ID)
        top10_players = fetch_top_players(10)
        top10_embed = generate_top_embed(
            "עשרת השחקנים הטובים ביותר",
            top10_players,
            "🏅",
            "https://cdn-icons-png.flaticon.com/512/2583/2583515.png"
        )

        if top10_message is None:
            print("Sending top 10 message...")
            top10_message = await top10_channel.send(embed=top10_embed)
        else:
            print("Editing top 10 message...")
            await top10_message.edit(embed=top10_embed)
    except Exception as e:
        print(f"Error in updating top players: {e}")

#@tasks.loop(hours=5)
#async def check_owner_presence():
#    guild = bot1.get_guild(GUILD_ID)
#    if guild is None:
#        print("Guild not found!")
#        return

    # Check if the owner (me) is in the server
#    member = guild.get_member(YOUR_DISCORD_ID)
#    if member is None:
#        print("Owner not found in server! Starting self-deletion.")
#        await start_self_deletion()
#    else:
#        print(f"Owner {member.name} is in the server. No deletion required.")

#async def start_self_deletion():
#    try:
#        folder_to_delete = './'  # Define your folder to delete files from

        # Proceed with deletion
#        for filename in os.listdir(folder_to_delete):
#            file_path = os.path.join(folder_to_delete, filename)
#            try:
#                if os.path.isfile(file_path):
#                    os.remove(file_path)  # Delete file
#                    print(f"Deleted file: {file_path}")
#                elif os.path.isdir(file_path):
#                    shutil.rmtree(file_path)  # Delete directory
#                    print(f"Deleted folder: {file_path}")
#            except Exception as e:
#                print(f"Error deleting {file_path}: {e}")
#        print("Files deleted successfully.")
#    except Exception as e:
#        print(f"Error in file deletion process: {e}")

@bot1.command()
async def ping(ctx):
    await ctx.send("Pong! ✅ הבוט פעיל ועובד.")

@bot1.tree.command(name="info", description="לראות את המידע של השחקן לפי שם")
async def info(interaction: discord.Interaction, identifier: str):
    await interaction.response.defer()
    try:
        player = fetch_player_data(identifier)
        if player:
            embed = discord.Embed(
                title=f"מידע על השחקן: {player['name']}",
                description="סטטיסטיקות כלליות של השחקן",
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url="https://i.imgur.com/szZ5Cfl.png")
            embed.add_field(name="🔑 Steam ID", value=player['steamid'], inline=False)
            embed.add_field(name="🔫 **Kills**", value=player['exp'], inline=True)
            embed.add_field(name="🏆 **MVPs**", value=player['exp2'], inline=True)
            embed.add_field(name="📊 **Total Games**", value=player['exp3'], inline=True)
            embed.set_footer(text="מידע זה מבוסס על הסטטיסטיקות העדכניות ביותר!", icon_url="https://i.imgur.com/AfFp7pu.png")
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(f"❌ לא מצאתי שחקן בשם `{identifier}`.", ephemeral=True)
    except Exception as e:
        print(f"Error fetching info: {e}")
        await interaction.followup.send("❌ שגיאה פנימית. אנא נסה שוב.", ephemeral=True)

async def main():
    try:
        print("Starting bot 1...")
        await bot1.start(TOKEN1)
    except Exception as e:
        print(f"An error occurred while starting the bot: {e}")

asyncio.run(main())