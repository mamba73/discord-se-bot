import discord
from discord.ext import commands, tasks
import sqlite3
import xml.etree.ElementTree as ET
import os
import sys
import configparser
from datetime import datetime
from dotenv import load_dotenv

# ============================================================
# ENV + CONFIG
# ============================================================

load_dotenv()

BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if not BOT_TOKEN:
    print("DISCORD_BOT_TOKEN is missing in .env")
    sys.exit(1)

config = configparser.ConfigParser()
config.read("config/config.ini")

GUILD_ID = int(config["DISCORD"]["GUILD_ID"])
CATEGORY_ID = int(config["DISCORD"]["CATEGORY_ID"])

SANDBOX_SBC = config["SPACE_ENGINEERS"]["SANDBOX_SBC"]
DB_FILE = config["database"]["DB_FILE"]

SYNC_INTERVAL = int(config["GENERAL"]["SYNC_INTERVAL"])
DEBUG = config["GENERAL"]["DEBUG"].lower() == "true"
DELETE_ALL = config["GENERAL"]["DELETE_ALL"].lower() == "true"
DISCORD_DELETE_UNUSED = config["GENERAL"]["DISCORD_DELETE_UNUSED"].lower() == "true"

# ============================================================
# LOGGING
# ============================================================

def log(msg):
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}")

# ============================================================
# DISCORD INIT
# ============================================================

intents = discord.Intents.default()
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ============================================================
# DATABASE
# ============================================================

db = sqlite3.connect(DB_FILE)
cur = db.cursor()

# ---- Factions table
cur.execute("""
CREATE TABLE IF NOT EXISTS factions (
    faction_id INTEGER PRIMARY KEY,
    tag TEXT,
    name TEXT,
    is_player_faction INTEGER
)
""")

# ---- Players table
cur.execute("""
CREATE TABLE IF NOT EXISTS players (
    player_id INTEGER PRIMARY KEY,
    name TEXT,
    steam_id TEXT
)
""")

# ---- Faction ↔ Player
cur.execute("""
CREATE TABLE IF NOT EXISTS faction_player (
    player_id INTEGER PRIMARY KEY,
    faction_id INTEGER NULL
)
""")

# ---- Discord roles created by bot
cur.execute("""
CREATE TABLE IF NOT EXISTS discord_roles (
    faction_id INTEGER PRIMARY KEY,
    role_id INTEGER
)
""")

# ---- Discord channels created by bot
cur.execute("""
CREATE TABLE IF NOT EXISTS discord_channels (
    faction_id INTEGER PRIMARY KEY,
    channel_id INTEGER,
    channel_name TEXT
)
""")

db.commit()

# ============================================================
# XML PARSING
# ============================================================

def parse_factions():
    """
    Parses Sandbox.sbc and returns factions.
    Player factions: tag length == 3
    NPC / mod factions: tag length != 3 (ignored on Discord)
    """
    if not os.path.exists(SANDBOX_SBC):
        log("[ERROR] Sandbox.sbc not found")
        return []

    tree = ET.parse(SANDBOX_SBC)
    root = tree.getroot()
    factions_node = root.find("Factions")
    if factions_node is None:
        return []

    result = []
    for f in factions_node.findall(".//MyObjectBuilder_Faction"):
        tag = f.findtext("Tag", "").strip()
        name = f.findtext("Name", "").strip()
        fid = int(f.findtext("FactionId", "0"))
        is_player_faction = len(tag) == 3

        members = []
        members_node = f.find("Members")
        if members_node is not None:
            for m in members_node.findall("MyObjectBuilder_FactionMember"):
                pid = m.findtext("PlayerId")
                if pid:
                    members.append(int(pid))

        result.append({
            "faction_id": fid,
            "tag": tag,
            "name": name,
            "is_player_faction": is_player_faction,
            "members": members
        })

    return result

# ============================================================
# DATABASE SYNC
# ============================================================

def sync_database(factions):
    seen_players = set()

    for f in factions:
        cur.execute("""
        INSERT OR REPLACE INTO factions
        (faction_id, tag, name, is_player_faction)
        VALUES (?, ?, ?, ?)
        """, (
            f["faction_id"],
            f["tag"],
            f["name"],
            int(f["is_player_faction"])
        ))

        for pid in f["members"]:
            seen_players.add(pid)
            cur.execute("INSERT OR IGNORE INTO players VALUES (?, NULL, NULL)", (pid,))
            cur.execute("INSERT OR REPLACE INTO faction_player VALUES (?, ?)", (pid, f["faction_id"]))

    for (pid,) in cur.execute("SELECT player_id FROM players"):
        if pid not in seen_players:
            cur.execute("INSERT OR REPLACE INTO faction_player VALUES (?, NULL)", (pid,))

    db.commit()

# ============================================================
# SAFE DELETE
# ============================================================

async def delete_all_discord_objects():
    """
    Deletes only Discord roles/channels created by the bot.
    """
    log("[DELETE_ALL] SAFE DELETE START")

    guild = bot.get_guild(GUILD_ID)

    for faction_id, channel_id, _ in cur.execute("SELECT faction_id, channel_id, channel_name FROM discord_channels"):
        ch = guild.get_channel(channel_id)
        if ch:
            await ch.delete()
            log(f"[DELETE] Channel ID {channel_id}")

    for faction_id, role_id in cur.execute("SELECT faction_id, role_id FROM discord_roles"):
        role = guild.get_role(role_id)
        if role and not role.managed:
            await role.delete()
            log(f"[DELETE] Role ID {role_id}")

    cur.execute("DELETE FROM discord_channels")
    cur.execute("DELETE FROM discord_roles")
    db.commit()

    log("[DELETE_ALL] DONE — EXITING")
    await bot.close()
    sys.exit(0)

# ============================================================
# DISCORD SYNC
# ============================================================

async def sync_discord(factions):
    guild = bot.get_guild(GUILD_ID)
    category = bot.get_channel(CATEGORY_ID)

    for f in factions:
        if not f["is_player_faction"]:
            continue  # Skip NPC / mod factions

        fid = f["faction_id"]
        tag = f["tag"]
        name = f["name"]

        # ---- ROLE: use tag as name
        cur.execute("SELECT role_id FROM discord_roles WHERE faction_id = ?", (fid,))
        row = cur.fetchone()
        if row:
            role = guild.get_role(row[0])
        else:
            role = await guild.create_role(name=tag)
            cur.execute("INSERT INTO discord_roles VALUES (?, ?)", (fid, role.id))
            db.commit()
            log(f"[CREATE] Role: {tag}")

        # ---- CHANNEL: use faction name
        cur.execute("SELECT channel_id FROM discord_channels WHERE faction_id = ?", (fid,))
        row = cur.fetchone()
        if not row:
            base_name = name.lower()
            name_unique = base_name
            i = 1
            existing = {c.name for c in category.channels}
            while name_unique in existing:
                i += 1
                name_unique = f"{base_name}-{i}"

            ch = await guild.create_text_channel(
                name_unique,
                category=category,
                overwrites={
                    guild.default_role: discord.PermissionOverwrite(view_channel=False),
                    role: discord.PermissionOverwrite(view_channel=True)
                }
            )
            cur.execute("INSERT INTO discord_channels VALUES (?, ?, ?)", (fid, ch.id, name_unique))
            db.commit()
            log(f"[CREATE] Channel: {name_unique}")

# ============================================================
# SYNC LOOP
# ============================================================

@tasks.loop(seconds=SYNC_INTERVAL)
async def sync_loop():
    log("===== SYNC START =====")
    factions = parse_factions()
    sync_database(factions)
    await sync_discord(factions)
    log("===== SYNC END =====")

@bot.event
async def on_ready():
    log(f"[READY] Logged in as {bot.user}")
    if DELETE_ALL:
        await delete_all_discord_objects()
        return
    sync_loop.start()

bot.run(BOT_TOKEN)
