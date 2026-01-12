# Changelog

## [1.0.0] – Initial stable release
### Added
- Discord bot syncing Space Engineers player factions
- Safe Discord role & channel creation
- SQLite persistence
- Tag-length rule (TAG length == 3 → player faction)
- NPC / mod factions excluded
- Safe delete logic
- Config.ini + .env support

### Fixed
- Prevent deletion of non-bot roles
- Prevent duplicate channels
- Database schema stability

### Notes
- SteamID is NOT available via Sandbox.sbc
- Discord user linking requires external mechanism
