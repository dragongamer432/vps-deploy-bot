import discord
from discord import app_commands
import subprocess
import uuid
import datetime
import json
import os

TOKEN = "PUT_YOUR_BOT_TOKEN_HERE"
DATA_FILE = "vps_data.json"

# ───────── AUTO CREATE DATA FILE ─────────
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ───────── DISCORD CLIENT ─────────
class Client(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

client = Client()

@client.event
async def on_ready():
    print(f"[+] DragonCloud VPS Bot Online as {client.user}")

# ───────── DEPLOY ─────────
@client.tree.command(name="deploy", description="Deploy a VPS")
async def deploy(interaction: discord.Interaction):

    await interaction.response.send_message(
        "🚀 Deploying VPS... Check your DMs.", ephemeral=True
    )

    data = load_data()

    container_id = uuid.uuid4().hex[:12]
    expiry = "2053-06-22"

    subprocess.run(["tmate", "-S", "/tmp/tmate.sock", "new-session", "-d"], check=True)
    subprocess.run(["tmate", "-S", "/tmp/tmate.sock", "wait", "tmate-ready"], check=True)

    ssh = subprocess.check_output(
        ["tmate", "-S", "/tmp/tmate.sock", "display", "-p", "#{tmate_ssh}"],
        text=True
    ).strip()

    data[container_id] = {
        "owner": interaction.user.id,
        "ssh": ssh,
        "status": "Active",
        "created": str(datetime.date.today()),
        "expires": expiry
    }

    save_data(data)

    embed = discord.Embed(
        title="🎉 Your VPS is Ready!",
        color=0x00ff88
    )
    embed.add_field(name="📦 Container ID", value=container_id, inline=False)
    embed.add_field(name="⚙ Specs", value="12GB RAM | 2 CPU | 80GB Disk", inline=False)
    embed.add_field(name="⏳ Expires", value=expiry, inline=True)
    embed.add_field(name="🟢 Status", value="Active", inline=True)
    embed.add_field(name="🧩 Systemctl", value="✅ Working", inline=True)
    embed.add_field(name="🌐 HTTP Access", value="http://127.0.0.1:3825/", inline=False)
    embed.add_field(name="🔐 SSH Connection", value=f"```{ssh}```", inline=False)
    embed.set_footer(text="DragonCloud Hosting")

    await interaction.user.send(embed=embed)

# ───────── STATUS ─────────
@client.tree.command(name="status", description="Check VPS status")
async def status(interaction: discord.Interaction, container_id: str):

    data = load_data()

    if container_id not in data:
        await interaction.response.send_message("❌ VPS not found.", ephemeral=True)
        return

    vps = data[container_id]
    emoji = "🟢" if vps["status"] == "Active" else "🔴"
    color = 0x00ff88 if vps["status"] == "Active" else 0xff5555

    embed = discord.Embed(
        title="📦 VPS Status",
        color=color
    )
    embed.add_field(name="Container ID", value=container_id, inline=False)
    embed.add_field(name="Status", value=f"{emoji} {vps['status']}", inline=True)
    embed.add_field(name="Expires", value=vps["expires"], inline=True)

    await interaction.response.send_message(embed=embed, ephemeral=True)

# ───────── LIST VPS ─────────
@client.tree.command(name="list_vps", description="List all your VPS")
async def list_vps(interaction: discord.Interaction):

    data = load_data()
    user_vps = [
        (cid, v) for cid, v in data.items()
        if v["owner"] == interaction.user.id
    ]

    if not user_vps:
        await interaction.response.send_message(
            "❌ You don't have any VPS.", ephemeral=True
        )
        return

    embed = discord.Embed(
        title="📋 Your VPS List",
        color=0x7289da
    )

    for cid, vps in user_vps:
        emoji = "🟢" if vps["status"] == "Active" else "🔴"
        embed.add_field(
            name=f"{emoji} {cid}",
            value=f"Status: {vps['status']}\nExpires: {vps['expires']}",
            inline=False
        )

    embed.set_footer(text=f"Total VPS: {len(user_vps)}")

    await interaction.response.send_message(embed=embed, ephemeral=True)

# ───────── SUSPEND ─────────
@client.tree.command(name="suspend_vps", description="Suspend a VPS")
async def suspend(interaction: discord.Interaction, container_id: str):

    data = load_data()

    if container_id not in data:
        await interaction.response.send_message("❌ VPS not found.", ephemeral=True)
        return

    data[container_id]["status"] = "Suspended"
    save_data(data)

    await interaction.response.send_message(
        f"⛔ VPS `{container_id}` suspended.", ephemeral=True
    )

# ───────── UNSUSPEND ─────────
@client.tree.command(name="unsuspend_vps", description="Unsuspend a VPS")
async def unsuspend(interaction: discord.Interaction, container_id: str):

    data = load_data()

    if container_id not in data:
        await interaction.response.send_message("❌ VPS not found.", ephemeral=True)
        return

    data[container_id]["status"] = "Active"
    save_data(data)

    await interaction.response.send_message(
        f"✅ VPS `{container_id}` unsuspended.", ephemeral=True
    )

# ───────── DELETE ─────────
@client.tree.command(name="delete", description="Delete a VPS")
async def delete(interaction: discord.Interaction, container_id: str):

    data = load_data()

    if container_id not in data:
        await interaction.response.send_message("❌ VPS not found.", ephemeral=True)
        return

    del data[container_id]
    save_data(data)

    await interaction.response.send_message(
        f"🗑 VPS `{container_id}` deleted.", ephemeral=True
    )

client.run(TOKEN)
