# 🛸 Macan Shrine Video Downloader – SilentStream Edition

Macan Shrine Video Downloader is a lightweight and fast desktop application for downloading videos from various online platforms using a modern PyQt6-based interface. Equipped with the yt-dlp engine, a multi-threaded UI, DNS Switching and the Shrine Log Panel, the SilentStream edition is designed to allow users to focus on downloading with a silent, efficient, and powerful flow.

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
<img width="611" height="550" alt="Screenshot 2025-09-17 202958" src="https://github.com/user-attachments/assets/f108ab43-357d-4a18-91aa-1e632379cd22" />




---
## 📝 Changelog v4.5.0
1. Log File Location in Temp Folder
What I changed: I imported the tempfile module. When the application first starts (__init__), it will create a single log file with a random name (e.g., shrine_log_a8b2c.json) in your operating system's temporary folder (such as C:\Users\YOUR_NAME\AppData\Local\Temp on Windows).

How it works: All functions that previously wrote to shrine_log.json (log_writer and reset_log) now automatically use the path to this temporary file.

2. Delete Log Files When the Application Closes
What I changed: I added a few lines of code to the closeEvent function. This function will be automatically executed by PyQt6 every time the application window is closed.

How it works: Before the application actually closes, the code will look for the temporary log file created in the first step and delete it from the system. This ensures that no log files are left behind.

3. MP3 Download Function
What's Changed:

I added a new QComboBox in the UI to select the download format: "Video (MP4)" or "Audio (MP3)".

If you select "Audio (MP3)", the video resolution option is automatically disabled to avoid confusion.

How it works: In the start_next_in_batch function, there's now a check for the selected format.

If it's Video, the yt-dlp command is the same as before.

If it's Audio, the yt-dlp command has been changed to --extract-audio --audio-format mp3 to download the audio in the best quality and save it as an .mp3 file.

4. FFmpeg & FFprobe Path Using _MEIPASS
What's Changed: In the start_next_in_batch function, I added a code block that checks whether the application is running as an .exe file created by PyInstaller.

How it works: If the application is running as an .exe, then the sys._MEIPASS variable will be present. This code will use that path to tell yt-dlp where ffmpeg is located (e.g., C:\Users\...\Temp\_MEI12345\ffmpeg.exe) using the --ffmpeg-location argument. This ensures that the video and audio merging (or converting to MP3) process runs smoothly without the need for a separate FFmpeg installation on the system.

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
