# Savegame Backup Tool

A simple PyQt5 application to backup and restore game save files easily.

---

## Features

- Manage multiple games and their savegame directories.
- Backup selected save files or folders with timestamps.
- Restore backups to the original savegame location.
- Add, edit, or delete games, including custom icons.
- Store notes for each backup.
- **Automatic version check** on startup against a GitHub-hosted version file.
- Prompt to update if a newer version is available.
- Launches an external `updater.exe` to handle updates.

---

## Requirements

- Python 3.6 or higher
- PyQt5 (`pip install PyQt5`)
- Requests (`pip install requests`)

---

## Installation

1. Clone or download this repository.
2. Make sure `updater.exe` is in the same folder as the main script (or adjust the path in the script).
3. Install the required Python packages:
   ```bash
   pip install PyQt5 requests
