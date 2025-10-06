# 🛸 Macan Shrine Video Downloader – SilentStream Edition

Macan Shrine Video Downloader is a lightweight and fast desktop application for downloading videos from various online platforms using a modern PySide6-based interface. Equipped with the yt-dlp engine, a multi-threaded UI, DNS Switching and the Shrine Log Panel, the SilentStream edition is designed to allow users to focus on downloading with a silent, efficient, and powerful flow.

---

## 🚀 Featured Features

- 🎞️ **Supports various video sites** (YouTube, TikTok, Instagram, etc.)
- 🧠 **Automatic metadata preview** (title, resolution, duration, thumbnail)
- 📥 **Batch downloader** for up to 10 URLs at once
- 🧭 **Smart DNS Switcher** to bypass or stabilize connections
- 📊 **Per-file progress bar** with real-time status log
- 🧾 **Shrine Log Panel** — monitor activity and errors in one place
- 🧩 Integrated with **Shrine Ecosystem** (Shrine Browser, Shrine Core Tools)
- 🌏 Multi-Language
- 🔧 **Custom config via JSON**

---

## 📸 Interface Appearance
<img width="623" height="543" alt="image" src="https://github.com/user-attachments/assets/7138ecdc-fd6b-4bdd-bbfd-a9f9879a6eb6" />





---
## 📝 Changelog v5.0.0
- Update Framework
- Redesign UI
- Update Engine (yt-dlp)

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
