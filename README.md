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
<img width="1101" height="700" alt="Screenshot 2025-12-26 025846" src="https://github.com/user-attachments/assets/e9368cd9-5795-4af7-8ddd-a06b9141b109" />
<img width="1098" height="698" alt="Screenshot 2025-12-26 030950" src="https://github.com/user-attachments/assets/0ef0446f-be7b-49e8-8d89-512508c7642c" />





---
## 📝 Changelog v8.0.0
- Change Layout Video Downloader
- Change Layout Video Converter
- Frameless Windows
- Custom Titlebar
- Windows Controls
- Drag & Resize
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
