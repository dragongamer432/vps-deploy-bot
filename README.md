🐉 DragonCloud VPS Management Bot

DragonCloud Bot is a high-performance infrastructure automation tool built to deploy and manage Ubuntu VPS containers on a 64GB host. This version is specifically optimized for IPv6-only or NAT-based environments, utilizing tmate tunnels to provide external access without needing a public IPv4 address.
🚀 Key Features

    IPv4-Independent: No public IPv4? No problem. Tmate tunnels allow users to connect to their VPS from anywhere in the world.

    Web & SSH Access: Provides both a clickable Web Terminal (for browser-based coding) and a standard SSH string.

    Systemd Enabled: Uses jrei/systemd-ubuntu to allow users to run services via systemctl.

    Resource Capping: Automatically restricts containers to 12GB RAM and 2 CPU Cores to protect the 64GB host.

    Administrative Control: Dedicated commands for Suspending, Unsuspending, and Deleting instances by ID.

    Persistent Storage: All container mappings are saved to a local JSON database.

🛠️ Tech Stack

    Language: Python 3.10+

    Orchestration: Docker Engine

    Tunneling: tmate (SSH & Web)

    Monitoring: psutil

    API: Discord.py (Slash Commands)

📋 Requirements

    Host OS: Ubuntu 22.04+ (or any Linux with Docker support).

    Docker: Installed and running (sudo apt install docker.io).

    Image: docker pull jrei/systemd-ubuntu:22.04.

    Python Libraries: discord.py, psutil, python-dotenv.

⚙️ Installation & Usage

    Install Dependencies:
    Bash

    pip install discord.py psutil python-dotenv

    Configure bot.py:

        Insert your Bot Token.

        Insert your Discord User ID into OWNER_ID.

    Launch the Bot:
    Bash

    python3 bot.py

🎮 Commands
Command	Description	Permission
/deploy	Deploys 12GB VPS & DMs Tmate Web/SSH links.	Everyone
/status	Shows 64GB host RAM/CPU usage.	Everyone
/suspend	Pauses container execution (saves files).	Admin
/unsuspend	Resumes a paused container.	Admin
/delete	Permanently removes the container and data.	Admin
🛡️ Resource Governance

To maintain the health of the DragonCloud node:

    RAM: Hard cap at 12GB per instance.

    CPU: Limited to 2.0 fractional cores.

    Connectivity: Bypasses local firewall restrictions via tmate.io.

Developed by DragonGamer | Official DragonCloud Infrastructure.
