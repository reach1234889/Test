import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
stock = []
balances = {}

OWNER_ID = 123456789012345678  # Replace this with your actual Discord user ID

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"❌ Sync failed: {e}")

@bot.tree.command(name="addstock", description="Add MCFA accounts to stock (multi-format)")
@app_commands.describe(accounts="email:pass per line, comma, or space separated")
async def addstock(interaction: discord.Interaction, accounts: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Only admins can add stock.", ephemeral=True)
        return
    raw = accounts.replace(",", "\n").replace(" ", "\n")
    lines = [line.strip() for line in raw.split("\n") if line.strip()]
    stock.extend(lines)
    await interaction.response.send_message(f"✅ Added {len(lines)} account(s).", ephemeral=True)

@bot.tree.command(name="stock", description="View number of accounts in stock")
async def stock_cmd(interaction: discord.Interaction):
    await interaction.response.send_message(f"📦 {len(stock)} account(s) in stock.")

@bot.tree.command(name="payuser", description="Send account(s) to user via DM (restricted)")
@app_commands.describe(user="User to pay", amount="Number of accounts to send")
async def payuser(interaction: discord.Interaction, user: discord.User, amount: int):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("❌ Only the bot owner can use this command.", ephemeral=True)
        return
    if amount > len(stock):
        await interaction.response.send_message(f"❌ Not enough stock. Only {len(stock)} available.")
        return

    balances[user.id] = balances.get(user.id, 0) + amount
    accounts = [stock.pop(0) for _ in range(amount)]
    try:
        await user.send("📨 **Your MCFA Account(s):**\n" + "\n".join(accounts))
        await interaction.response.send_message(f"✅ Sent {amount} account(s) to {user.mention}'s DM.")
    except discord.Forbidden:
        await interaction.response.send_message("⚠️ Sent but couldn't DM the user.")

@bot.tree.command(name="balance", description="Check your coin balance")
async def balance(interaction: discord.Interaction):
    bal = balances.get(interaction.user.id, 0)
    await interaction.response.send_message(f"💰 Your balance: `{bal}` coins")

@bot.tree.command(name="deliver", description="Manually deliver 1 account to user")
@app_commands.describe(user="User to deliver to")
async def deliver(interaction: discord.Interaction, user: discord.User):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Admins only.", ephemeral=True)
        return
    if not stock:
        await interaction.response.send_message("❌ No stock left.")
        return
    acc = stock.pop(0)
    try:
        await user.send(f"📨 **Your account:**\n{acc}")
        await interaction.response.send_message(f"✅ Delivered 1 account to {user.mention}.")
    except discord.Forbidden:
        await interaction.response.send_message("⚠️ Could not DM the user.")

@bot.tree.command(name="clearstock", description="Clear all stock (admin)")
async def clearstock(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Admins only.", ephemeral=True)
        return
    stock.clear()
    await interaction.response.send_message("🧹 Stock cleared successfully.")

@bot.tree.command(name="help", description="Show command help")
async def help_cmd(interaction: discord.Interaction):
    text = """
📘 **Bot Commands**
🔹 `/addstock` — Add stock (admin only)
🔹 `/stock` — View current stock
🔹 `/payuser` — Pay a user (bot owner only)
🔹 `/balance` — View your balance
🔹 `/deliver` — Deliver 1 account (admin)
🔹 `/clearstock` — Wipe all stock (admin)
"""
    await interaction.response.send_message(text, ephemeral=True)

bot.run(os.getenv("TOKEN"))
