import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import os
import json
import random
import psutil
import logging

# ---------------- HARDCODED CONFIG ----------------
TOKEN = "YOUR_BOT_TOKEN_HERE"
OWNER_ID = 1212951893651759225 
IMAGE = "jrei/systemd-ubuntu:22.04"
DATA_FILE = "vps_db.json"

logging.basicConfig(level=logging.INFO, handlers=[logging.FileHandler("dragoncloud.log"), logging.StreamHandler()])
logger = logging.getLogger("DragonCloud")

# ---------------- DATABASE ----------------
def load_db():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f: return json.load(f)
    return {}

def save_db(data):
    with open(DATA_FILE, 'w') as f: json.dump(data, f, indent=4)

vps_db = load_db()

# ---------------- BOT INIT ----------------
class DragonBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())
    async def setup_hook(self):
        await self.tree.sync()

bot = DragonBot()

# ---------------- TMATE HELPER ----------------
async def get_tmate_links(c_name):
    sock = f"/tmp/tmate-{c_name}.sock"
    # Command to initialize tmate and grab links
    cmd = (
        f"tmate -S {sock} new-session -d && sleep 7 && "
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

@bot.tree.command(name="deploy", description="Deploy a new 12GB DragonCloud VPS")
async def deploy(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    user_id = str(interaction.user.id)

    if any(v['owner'] == user_id for v in vps_db.values()):
        return await interaction.followup.send("❌ You already have an active VPS!", ephemeral=True)

    c_name = f"dragon-{random.randint(1000, 9999)}"
    display_port = random.randint(1000, 9999) # Random 4-digit port

    # Docker Run - Resource Caps: 12GB RAM, 2 CPUs
    cmd = ["docker", "run", "-d", "--privileged", "--name", c_name, "--memory", "12g", "--cpus", "2", IMAGE]
    proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE)
    stdout, _ = await proc.communicate()
    container_id = stdout.decode().strip()[:12]

    # Env Setup inside Container
    await asyncio.create_subprocess_exec("docker", "exec", c_name, "bash", "-c", "apt update && apt install -y tmate curl sudo")
    
    ssh_link, web_link = await get_tmate_links(c_name)

    vps_db[container_id] = {"owner": user_id, "name": c_name, "status": "Active"}
    save_db(vps_db)

    embed = discord.Embed(title="🚀 Your VPS is Ready!", color=0x00ff00)
    embed.description = (
        f"**Container ID**\n`{container_id}`\n\n"
        f"**Status**\n🟢 Active\n\n"
        f"**HTTP Access**\nhttp://127.0.0.1:{display_port}/\n\n"
        f"**Web Terminal**\n[Click Here to Open]({web_link})\n\n"
        f"**SSH Connection**\n`{ssh_link}`\n\n"
        f"**Points Deducted**\n0 points"
    )
    embed.set_footer(text="Official DragonCloud - Quality Wise, No Compromise.")
    
    try:
        await interaction.user.send(embed=embed)
        await interaction.followup.send(f"✅ Success! Check your DMs.", ephemeral=True)
    except:
        await interaction.followup.send(f"⚠️ VPS Created: `{container_id}`, but I couldn't DM you.", ephemeral=True)

@bot.tree.command(name="suspend", description="Admin: Suspend a VPS")
async def suspend(interaction: discord.Interaction, container_id: str):
    if interaction.user.id != OWNER_ID: return
    if container_id in vps_db:
        await asyncio.create_subprocess_exec("docker", "pause", vps_db[container_id]['name'])
        vps_db[container_id]['status'] = "Suspended"
        save_db(vps_db)
        await interaction.response.send_message(f"⏸️ `{container_id}` Suspended.")

@bot.tree.command(name="unsuspend", description="Admin: Unsuspend a VPS")
async def unsuspend(interaction: discord.Interaction, container_id: str):
    if interaction.user.id != OWNER_ID: return
    if container_id in vps_db:
        await asyncio.create_subprocess_exec("docker", "unpause", vps_db[container_id]['name'])
        vps_db[container_id]['status'] = "Active"
        save_db(vps_db)
        await interaction.response.send_message(f"▶️ `{container_id}` Activated.")

@bot.tree.command(name="delete", description="Admin: Delete a VPS")
async def delete(interaction: discord.Interaction, container_id: str):
    if interaction.user.id != OWNER_ID: return
    if container_id in vps_db:
        await asyncio.create_subprocess_exec("docker", "rm", "-f", vps_db[container_id]['name'])
        del vps_db[container_id]
        save_db(vps_db)
        await interaction.response.send_message(f"🗑️ `{container_id}` Deleted.")

@bot.tree.command(name="status", description="Host Status")
async def status(interaction: discord.Interaction):
    ram = psutil.virtual_memory()
    embed = discord.Embed(title="📊 DragonCloud Health", color=0x3498db)
    embed.add_field(name="RAM Usage", value=f"`{ram.percent}%` ({round(ram.used/1024**3, 1)}/64GB)")
    embed.add_field(name="Active VPS", value=f"`{len(vps_db)}`")
    await interaction.response.send_message(embed=embed)

bot.run(TOKEN)
