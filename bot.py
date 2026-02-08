import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import os
import json
import random
import psutil

# ---------------- CONFIG (HARDCODED) ----------------
TOKEN = "YOUR_BOT_TOKEN_HERE"
OWNER_ID = 1346664897005621308 
IMAGE = "jrei/systemd-ubuntu:22.04"
DATA_FILE = "vps_db.json"

# Database Helpers
def load_db():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f: return json.load(f)
    return {}

def save_db(data):
    with open(DATA_FILE, 'w') as f: json.dump(data, f, indent=4)

vps_db = load_db()

class DragonBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())
    async def setup_hook(self):
        await self.tree.sync()

bot = DragonBot()

# ---------------- TMATE LOGIC ----------------
async def get_tmate_links(c_name):
    """Starts tmate inside container and captures the unique tunnel strings"""
    sock = f"/tmp/tmate-{c_name}.sock"
    cmd = (
        f"tmate -S {sock} new-session -d && sleep 8 && "
        f"tmate -S {sock} display -p '#{{tmate_ssh}}' && "
        f"tmate -S {sock} display -p '#{{tmate_web}}'"
    )
    proc = await asyncio.create_subprocess_exec("docker", "exec", c_name, "bash", "-c", cmd, stdout=asyncio.subprocess.PIPE)
    stdout, _ = await proc.communicate()
    output = stdout.decode().strip().split('\n')
    
    ssh = output[0] if len(output) > 0 else "Generating..."
    web = output[1] if len(output) > 1 else "Generating..."
    return ssh, web

# ---------------- COMMANDS ----------------

@bot.tree.command(name="deploy", description="Deploy a 12GB DragonCloud VPS")
async def deploy(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    c_name = f"dragon-{random.randint(1000, 9999)}"
    display_port = random.randint(1000, 9999) # Random number for the 127.0.0.1 string

    # 1. Start Container
    await asyncio.create_subprocess_exec("docker", "run", "-d", "--privileged", "--name", c_name, "--memory", "12g", "--cpus", "2", IMAGE)

    # 2. Setup Tmate
    await asyncio.create_subprocess_exec("docker", "exec", c_name, "bash", "-c", "apt update && apt install -y tmate curl sudo")
    
    # 3. Fetch Tunnel Links
    ssh_link, web_link = await get_tmate_links(c_name)

    vps_db[c_name] = {"owner": str(interaction.user.id), "status": "Active"}
    save_db(vps_db)

    embed = discord.Embed(title="🚀 DragonCloud VPS Ready", color=0x00ff00)
    embed.description = (
        f"**Container ID**\n`{c_name}`\n\n"
        f"**Specs**\n12GB RAM | 2 CPU\n\n"
        f"**HTTP Access**\nhttp://127.0.0.1:{display_port}/\n\n"
        f"**SSH Connection**\n`{ssh_link}`\n\n"
        f"**Web Terminal**\n[Open in Browser]({web_link})"
    )
    
    await interaction.user.send(embed=embed)
    await interaction.followup.send("✅ Details sent to your DM!", ephemeral=True)

@bot.tree.command(name="delete", description="Admin: Delete a VPS")
async def delete(interaction: discord.Interaction, name: str):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ Admin only.", ephemeral=True)
    
    await asyncio.create_subprocess_exec("docker", "rm", "-f", name)
    if name in vps_db:
        del vps_db[name]
        save_db(vps_db)
    await interaction.response.send_message(f"🗑️ Deleted `{name}`")

bot.run(TOKEN)
