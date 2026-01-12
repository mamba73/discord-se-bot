# Space Engineers → Discord Sync Bot

This bot synchronizes **Space Engineers player factions** with a Discord server.

It creates:

* **Discord roles** per player faction
* **Private text channels** per faction
* Keeps a **local SQLite database** to safely track what the bot created

NPC / mod factions are **ignored**.

---

## ✨ Key Rules & Logic

* Only **player factions** are synced

  * A player faction is defined as:

    ```text
    Tag length === 3
    ```
* NPC / default / mod factions (e.g. `NOMAD`, `IMBER`, `REAVER`, etc.) are ignored
* Discord **roles are created using the faction name**
* Discord **channels are created using the faction name**
* If a channel name already exists, a numeric suffix is added:

  ```text
  apollo
  apollo-2
  apollo-3
  ```
* All created Discord objects are stored in a **database** for safe reuse & deletion

---

## 📁 Project Directory Structure

```text
discord-SE-bot/
│
├── discord-se-bot.py        # Main bot script
├── requirements.txt        # Python dependencies
├── README.md
├── .gitignore
│
├── .env                    # NOT committed (Discord token)
├── .env.sample             # Example environment file
│
├── config/
│   └── config.ini          # Bot configuration
│
└── data/
    └── se.db               # SQLite database (auto-created)
```

---

## 🧩 Requirements

* **Python 3.10+ recommended**
* Discord Bot Token
* Access to `Sandbox.sbc` from a Space Engineers server

---

## 📦 Python Dependencies

All dependencies are installed via `requirements.txt`:

```txt
discord.py>=2.3.2
python-dotenv>=1.0.0
```

---

## 🔧 Installation

### 1️⃣ Clone the repository

```bash
git clone git@github.com:mamba73/discord-se-bot.git
cd discord-se-bot
```

---

### 2️⃣ Create virtual environment (recommended)

```bash
python -m venv venv
```

Activate it:

**Windows**

```bash
venv\Scripts\activate
```

**Linux / macOS**

```bash
source venv/bin/activate
```

---

### 3️⃣ Install dependencies

If you have **only one Python version**:

```bash
pip install -r requirements.txt
```

If you have **multiple Python versions installed** (recommended):

```bash
python -m pip install -r requirements.txt
```

---

### 4️⃣ Environment variables

Create `.env` in the project root:

```env
DISCORD_BOT_TOKEN=YOUR_DISCORD_BOT_TOKEN
```

⚠️ **Never commit `.env` to GitHub**

---

### 5️⃣ Configuration file

Edit:

```text
config/config.ini
```

Example:

```ini
[DISCORD]
GUILD_ID = 123456789012345678
CATEGORY_ID = 123456789012345678

[SPACE_ENGINEERS]
SANDBOX_SBC = D:\torch-server\Instance\Saves\world\Sandbox.sbc

[database]
DB_FILE = data/se.db

[GENERAL]
SYNC_INTERVAL = 60
DEBUG = true
DELETE_ALL = false
DISCORD_DELETE_UNUSED = false
```

---

## Configuration Flags (Booleans)

### DEBUG

DEBUG = true

- Enables verbose logging
- Recommended during development

---

### DELETE_ALL

DELETE_ALL = false

DANGEROUS – USE WITH CARE

- When true:
  - Deletes ONLY Discord roles and channels created by this bot
  - Uses database records for safety
  - Bot exits immediately after cleanup
- Managed roles (bot roles) are never deleted

Use only for full reset scenarios.

---

### DISCORD_DELETE_UNUSED

DISCORD_DELETE_UNUSED = false

- When false:
  - No automatic deletion of Discord objects
- When true:
  - Allows cleanup of unused Discord roles/channels
- Currently conservative by design

---

---

## ▶️ Running the Bot

```bash
python discord-se-bot.py
```

or (safe for multi-version setups):

```bash
python -m discord-se-bot.py
```

---

## 🗃️ Database Model (SQLite)

The database is created automatically.

### Tables

* `factions`
* `players`
* `faction_player`
* `discord_roles`
* `discord_channels`

The database guarantees:

* No duplicate Discord objects
* Safe restarts
* Safe cleanup

---

## 🧹 Safe Deletion Mode

To delete **only** objects created by the bot:

```ini
DELETE_ALL = true
```

What happens:

* Deletes only roles & channels recorded in the database
* Never touches manual Discord objects
* Bot exits automatically

---

## ⚠️ Discord Intent Warning

You may see:

```text
Privileged message content intent is missing
```

This is **not an error**.

The bot:

* Does NOT read messages
* Does NOT use commands

You can safely ignore this warning.

---

## ✅ Current Status

* ✔ Tag-based player faction detection
* ✔ NPC faction exclusion
* ✔ Duplicate-safe Discord channels
* ✔ Persistent database mapping
* ✔ Safe delete mode

---

## 🚀 Possible Future Extensions

* SteamID → Discord member role assignment
* Auto-cleanup of unused roles
* Torch / SE API integration
* Multi-server support

---

## 📜 License

MIT / Private use — adapt as needed.
