# 🛸 Macan Video Downloader – Premium Edition

Macan Shrine Video Downloader is a lightweight and fast desktop application for downloading videos from various online platforms using a modern PySide6-based interface. Equipped with the yt-dlp engine, a multi-threaded UI, DNS Switching and the Shrine Log Panel, the SilentStream edition is designed to allow users to focus on downloading with a silent, efficient, and powerful flow.

---

## 🚀 Featured Features

- 🎞️ **Supports various video sites** (YouTube, TikTok, Instagram, etc.)
- 🧠 **Automatic metadata preview** (title, resolution, duration, thumbnail)
- 📥 **Batch downloader** for up to 10 URLs at once
- 📊 **Per-file progress bar** with real-time status log
- 🌏 Multi-Language


---

## 📸 Interface Appearance
<img width="1002" height="630" alt="Screenshot 2025-11-14 092537" src="https://github.com/user-attachments/assets/41b84553-9b0c-44be-9798-1c10858701b0" />
<img width="1000" height="630" alt="Screenshot 2025-11-14 092805" src="https://github.com/user-attachments/assets/e2fbcae6-d0a5-4a4d-830f-a1308e1cb193" />

---
## 📝 Changelog v7.0.0
✨ Added
CLI (Command-Line Interface) Mode:
A new "CLI Mode" checkbox has been added to the main interface.
When enabled, this mode switches the queue to a raw text log, displaying all output directly from the macan-engine.
Adding URLs in this mode bypasses thumbnail and metadata fetching, allowing for rapid-fire queuing and immediate download.
Queue Context Menu & Multi-Select:
The download table now supports multi-selection of items.
A new right-click context menu has been implemented, providing the following actions:
Play: Opens the completed video or audio file.
Remove from List: Removes selected items from the queue (does not delete the file).
Delete from Disk: Permanently deletes the downloaded file from your computer (a confirmation prompt is shown).
🐞 Fixed
"Stop Download" Button Logic:
Resolved a major bug where the "Stop Download" button would not correctly terminate the download queue.
The button now immediately kills the active download process, marks the stopped item as "Error," and reliably prevents the next item in the queue from starting automatically.
File Path Parsing:
Fixed a critical error where file paths containing quotes or trailing spaces were not parsed correctly. This ensures that files are found and can be played after a successful download.
Asset Path Portability:
Corrected the pathing logic for icons and assets. The application will now correctly load all icons regardless of the directory it is run from, improving portability.
🛠️ Changed / Improved
Translation Engine:
The internal internationalization (i18n) function has been upgraded to be more robust, improving support for default text and formatted strings.
UI Refactoring:
Refactored the logic for updating and rebuilding the queue table, resulting in more stable performance, especially when removing items from the list.
Styling:
Updated the application's stylesheet to support the new CLI view, table selection colors, and the context menu for a consistent dark-mode experience.


---
## 📦 How to Use

1. Make sure you have Python 3.10+ and have installed the dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python main.py
```

3. Enter the video URL or use **batch mode**
4. Click the `Orbit Shrine` button to start the download
5. Check the Shrine Log Panel to monitor the process
6. (Optional) Enable DNS resolver for a more optimal connection

---

## ⚙️ Configuration

Configurations can be set in the `downloader_config.json` file.
```json
{ 
"max_batch": 10, 
"output_format": "mp4", 
"download_folder": "ShrineDownloads/"
}
