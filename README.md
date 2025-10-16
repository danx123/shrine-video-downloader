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
<img width="1000" height="631" alt="Screenshot 2025-10-16 185813" src="https://github.com/user-attachments/assets/8cf57727-4b1f-443f-8a2a-22be7af91231" />






---
## 📝 Changelog v6.0.0
- These changes focus on improving the user experience, adding advanced queue features (including batch), and improving the accuracy of downloaded file naming.

- New Features
New Queue and UI Layout:
Adopted a more structured two-column layout with group boxes for single controls, batch mode, and the download queue.
Added a Thumbnail column to the queue table for a visual preview of videos to be downloaded.
The row height is adjusted to accommodate thumbnail displays.

- Batch Mode:
Added a separate group box with a QPlainTextEdit widget (self.batch_urls_input) to accommodate multiple URLs to be added to the queue at once.
Added a self.add_batch_button button for processing URLs in bulk.

- Video Playback Feature:
Added a self.play_finished_video function connected to the itemDoubleClicked signal in the queue table. Users can double-click an item with the "Completed" status to play the downloaded file.

- Clear Queue Button:
Added the self.clear_queue_button and self.clear_queue functions to clear the queue table and job data.

- Improved Language Settings:
Added lang_map to display more descriptive language names in combo boxes.
The change_language function now updates the translation status for items already in the queue.

- Custom Dark Theme:
Added the self.apply_stylesheet function with comprehensive CSS styles for a modern, dark interface.

- Improvements and Fixes
Improved Final File Naming Logic:
In DownloadWorker.run, the logic has been improved to always capture the final file path from the [download] Destination: ... output in yt-dlp, ensuring the correct file name is captured even if no merge or audio extraction is performed.
Removed inaccurate -o path fallback logic.

- Job Data Structure Improvements:
The job data structure (self.download_queue_data) now uses rows as indexes to refer to table rows.

- Added a filepath field to job data to store the final file path after the download is complete.

- Metadata Retrieval Improvements:
The MetadataWorker now returns results along with the corresponding row number (Signal(dict, int)), simplifying job data updates.
UI metadata updates (title, details, "Queued" status) are now performed by update_row_with_metadata after data is received.

- Default Output Location Changes:
Changed the default output folder for downloads (in the application directory) to $HOME/Downloads/Macan Video Download for easier user access.

- Widget and Layout Changes:
Replaced the QListWidget widget for queues with a QTableWidget widget that is more suitable for displaying structured data (Title, Format, Progress, Status).

Removed the separate metadata preview widgets (self.title_label, self.thumb_frame, self.meta_preview) as their functionality is now integrated directly into the queue line.
Removed the Log widget (formerly QListWidget) and the reset_log button from the main UI.


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
