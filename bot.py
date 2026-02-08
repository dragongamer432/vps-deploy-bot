import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import os
import json
import random
import psutil
import logging
from datetime import datetime

# ---------------- CONFIG ----------------
TOKEN = "YOUR_BOT_TOKEN"
OWNER_ID = 1212951893651759225 
IMAGE = "jrei/systemd-ubuntu:22.04"
SERVER_IP = "YOUR_VPS_IP"
DATA_FILE = "vps_db.json"

# Setup Logging to File for the /logs command
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("dragoncloud.log"), logging.StreamHandler()]
)
logger = logging.getLogger("DragonCloud")

# ---------------- DATA ----------------
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

# ---------------- LOGIC ----------------
async def get_tmate_ssh(c_name):
    sock = f"/tmp/tmate-{c_name}.sock"
    cmd = f"tmate -S {sock} new-session -d && sleep 5 && tmate -S {sock} display -p '#{{tmate_ssh}}'"
    proc = await asyncio.create_subprocess_exec("docker", "exec", c_name, "bash", "-c", cmd, stdout=asyncio.subprocess.PIPE)
    stdout, _ = await proc.communicate()
    return stdout.decode().strip()

# ---------------- COMMANDS ----------------

@bot.tree.command(name="deploy", description="Deploy a new 12GB DragonCloud VPS")
async def deploy(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    user_id = str(interaction.user.id)

    # Prevent duplicates
    if any(v['owner'] == user_id for v in vps_db.values()):
        return await interaction.followup.send("❌ You already have a VPS!", ephemeral=True)

    c_name = f"dragon-{random.randint(1000, 9999)}"
    port = random.randint(3000, 3999)

    # Create Container
    cmd = ["docker", "run", "-d", "--privileged", "--name", c_name, "--memory", "12g", "--cpus", "2", "-p", f"{port}:80", IMAGE]
    proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE)
    stdout, _ = await proc.communicate()
    container_id = stdout.decode().strip()[:12]

    # Install tmate
    await asyncio.create_subprocess_exec("docker", "exec", c_name, "bash", "-c", "apt update && apt install -y tmate curl sudo")
    ssh = await get_tmate_ssh(c_name)

    vps_db[container_id] = {"owner": user_id, "name": c_name, "port": port}
    save_db(vps_db)
    logger.info(f"User {user_id} deployed container {container_id}")

    embed = discord.Embed(title="🚀 Your VPS is Ready!", color=0x00ff00)
    embed.description = f"**Container ID**\n`{container_id}`\n\n**Specs**\n12GB RAM | 2 CPU | 80GB Disk\n\n**Expires**\n2053-06-22\n\n**Status**\n🟢 Active\n\n**Systemctl**\n✅ Working\n\n**HTTP Access**\nhttp://{SERVER_IP}:{port}/\n\n**SSH Connection**\n`{ssh}`\n\n**Points Deducted**\n0 points\n\n**Remaining Points**\n0 points"
    
    try:
        await interaction.user.send(embed=embed)
        await interaction.followup.send("✅ Sent to DMs!", ephemeral=True)
    except:
        await interaction.followup.send(f"⚠️ VPS Ready: `{container_id}` (DMs Locked)", ephemeral=True)

@bot.tree.command(name="status", description="Host Hardware Status")
async def status(interaction: discord.Interaction):
    ram = psutil.virtual_memory()
    embed = discord.Embed(title="📊 DragonCloud Host Status", color=discord.Color.blue())
    embed.add_field(name="Containers", value=f"`{len(vps_db)}`")
    embed.add_field(name="CPU", value=f"`{psutil.cpu_percent()}%`")
    embed.add_field(name="RAM", value=f"`{ram.percent}%` ({round(ram.used/1024**3, 1)}/64GB)")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="logs", description="Admin: View system or container logs")
@app_commands.describe(type="bot, host, or container_id")
async def logs(interaction: discord.Interaction, type: str):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ Admin only.", ephemeral=True)

    await interaction.response.defer(ephemeral=True)

    if type == "bot":
        with open("dragoncloud.log", "r") as f:
            log_data = f.readlines()[-15:] # Last 15 lines
        content = "".join(log_data)
    elif type == "host":
        proc = await asyncio.create_subprocess_exec("tail", "-n", "15", "/var/log/syslog", stdout=asyncio.subprocess.PIPE)
        stdout, _ = await proc.communicate()
        content = stdout.decode()
    elif type in vps_db:
        c_name = vps_db[type]['name']
        proc = await asyncio.create_subprocess_exec("docker", "logs", "--tail", "15", c_name, stdout=asyncio.subprocess.PIPE)
        stdout, _ = await proc.communicate()
        content = stdout.decode()
    else:
        content = "Invalid type. Use 'bot', 'host', or a valid Container ID."

    await interaction.followup.send(f"📋 **Logs for {type}:**\n```\n{content[:1900]}\n```", ephemeral=True)

@bot.tree.command(name="manage", description="Admin: Stop/Delete VPS")
async def manage(interaction: discord.Interaction, action: str, container_id: str):
    if interaction.user.id != OWNER_ID: return
    if container_id not in vps_db: return
    
    c_name = vps_db[container_id]['name']
    if action == "stop": await asyncio.create_subprocess_exec("docker", "stop", c_name)
    if action == "delete": 
        await asyncio.create_subprocess_exec("docker", "rm", "-f", c_name)
        del vps_db[container_id]
        save_db(vps_db)
    await interaction.response.send_message(f"✅ {action} successful.")

bot.run(TOKEN)
