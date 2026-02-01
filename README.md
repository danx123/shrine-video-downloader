# 🛸 Macan Video Downloader – Premium Edition

Macan Shrine Video Downloader is a lightweight and fast desktop application for downloading videos from various online platforms using a modern PySide6-based interface. Equipped with the yt-dlp engine, a multi-threaded UI, DNS Switching and the Shrine Log Panel, the SilentStream edition is designed to allow users to focus on downloading with a silent, efficient, and powerful flow.

---

## 🚀 Featured Features

- 🎞️ **Supports various video sites** (YouTube, TikTok, Instagram, etc.)
- 🧠 **Automatic metadata preview** (title, resolution, duration, thumbnail)
- 📥 **Batch downloader** for up to 10 URLs at once
- 📊 **Per-file progress bar** with real-time status log
- 🌏 Multi-Language
- Converter
- Video Player


---

## 📸 Interface Appearance
<img width="1099" height="697" alt="Screenshot 2026-02-02 022151" src="https://github.com/user-attachments/assets/324b395f-a994-4e50-8f3f-e3c698d5332b" />
<img width="1100" height="699" alt="Screenshot 2026-02-02 022203" src="https://github.com/user-attachments/assets/6504f6d7-c6ed-49c0-b278-b0492f540934" />
<img width="1099" height="700" alt="Screenshot 2026-02-02 022330" src="https://github.com/user-attachments/assets/f0c2b875-e5ef-48f0-b94a-ea879facc16f" />



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
