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
<img width="1003" height="633" alt="Screenshot 2025-11-17 093751" src="https://github.com/user-attachments/assets/8ff885c1-53fd-4e2f-b86c-d845e9aaaabe" />


---
## 📝 Changelog v7.3.0
✨ New Features
Implemented Queue Statistics Panel: Added a new display panel at the top of the application to provide users with at-a-glance information about the download queue.
Added Total Progress Monitor: The panel now displays the total number of items in the queue ("Total: X") and tracks overall completion ("Progress: Y/X"). This count updates automatically as items are added, removed, or completed.
Added Elapsed Time Counter: A new "Elapsed: HH:MM:SS" timer now actively tracks the duration of the download process. The timer starts when the queue is initiated and stops automatically upon completion or when manually stopped by the user.
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
