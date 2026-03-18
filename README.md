# Macan Video Downloader — Premium Edition

> **v9.8.0** · PySide6 · yt-dlp · Python 3.10+

A professional-grade desktop media suite for downloading, converting, and playing video content from hundreds of online platforms. Built on a fully multi-threaded architecture with a sleek frameless dark UI, Macan Suite is engineered for speed, reliability, and an uncompromising user experience.

---

## ✦ Screenshots

<img width="1147" height="727" alt="Macan Suite v9.8.0 Interface" src="https://github.com/user-attachments/assets/fb3d1d04-370d-4c87-b602-bd4719cb67ef" />

---

## ✦ Feature Highlights

### Core Downloader
| Feature | Details |
|---|---|
| **Platform Support** | YouTube, TikTok, Instagram, Twitter/X, Facebook, Vimeo, and 1,000+ sites via yt-dlp |
| **Metadata Preview** | Auto-fetches title, thumbnail, resolution, and duration before download |
| **Batch Mode** | Queue multiple URLs simultaneously with a numbered line editor |
| **Format Selection** | Video (MP4) or Audio (MP3) with resolution presets — Original, 480p, 720p, 1080p |
| **CLI Mode** | Terminal-style output view for power users and debugging |
| **Auto Shutdown** | Automatically powers off the system when the download queue completes |
| **Download History** | Persistent log of all completed downloads, searchable and clearable |

### Performance & Reliability
| Feature | Details |
|---|---|
| **Multi-threaded Engine** | Downloads, metadata fetches, and UI rendering run on independent threads — zero UI blocking |
| **Live Network Monitor** | Real-time download/upload speed display (B/s → KB/s → MB/s) powered by `psutil` |
| **Smart Path Resolution** | Automatically resolves sanitized filenames when yt-dlp normalizes special characters or emoji |
| **Crash-safe Shutdown** | All background workers are gracefully terminated before the window is destroyed |

### Media Suite
| Module | Details |
|---|---|
| **Video Converter** | FFmpeg-powered batch converter with format, resolution, and quality controls |
| **Media Player** | Built-in PySide6 player with seek bar, volume memory, and fullscreen support |

### UI & Experience
| Feature | Details |
|---|---|
| **Frameless Window** | Custom title bar with minimize, maximize/restore, and close — resizable from all edges |
| **System Tray** | Minimizes to tray on close; desktop notifications on queue completion |
| **Multi-Language** | Full UI localization for English and Bahasa Indonesia, switchable at runtime |
| **Busy Cursor Feedback** | Spinner cursor activates automatically during background metadata fetches |

---

## ✦ Requirements

- **Python** 3.10 or higher
- **Operating System** Windows 10/11 · macOS 12+ · Linux (tested on Ubuntu 22.04)
- **yt-dlp** engine binary (`macan-engine` / `macan-engine.exe`) in the application directory or on `PATH`
- **FFmpeg** (required for Video Converter and audio extraction)

---

## ✦ Installation

**1. Clone the repository**
```bash
git clone https://github.com/danx123/shrine-video-downloader.git
cd shrine-video-downloader
```

**2. Install Python dependencies**
```bash
pip install -r requirements.txt
```

The core optional dependency for network monitoring:
```bash
pip install psutil
```

**3. Place the engine binary**

Download the latest `macan-engine` binary from the [Releases](https://github.com/danx123/shrine-video-downloader/releases) page and place it in the project root directory.

---

## ✦ Configuration

Application behavior can be customized via `video_config.json`:

```json
{
  "cookiesfrombrowser": "chrome",
  "max_retries": 3,
  "concurrent_fragments": 1,
  "fragment_retries": 10,
  "merge_format": "mp4",
  "format_map": {
    "Original Size": "bv*+ba/b",
    "480p":  "bv*[height<=480]+ba/b[height<=480]",
    "720p":  "bv*[height<=720]+ba/b[height<=720]",
    "1080p": "bv*[height<=1080]+ba/b[height<=1080]"
  }
}
```

Additional preferences — output folder, notification settings, and tray behavior — are configurable from within the application via **Settings**.

---

## ✦ License

© 2026 **Macan Angkasa** All rights reserved.
Licensed under the **Commercial Premium License**. Unauthorized distribution or resale is strictly prohibited.

---

<p align="center">
  Built with PySide6 · Powered by yt-dlp · © 2026 Macan Angkasa Dev
</p>
