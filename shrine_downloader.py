import sys, os, subprocess, requests, json, re
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QTextEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QComboBox, QFileDialog, QProgressBar,
    QListWidget, QListWidgetItem, QMessageBox, QInputDialog
)
from PyQt6.QtGui import QPixmap, QColor, QIcon
from PyQt6.QtCore import Qt, QTimer, QThread, QObject, pyqtSignal
import yt_dlp, socket
import dns.resolver
from shrine_browser import ShrineBrowser # Pastikan shrine_browser.py juga dimigrasi

# 📜 Load video config
with open("video_config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

# 🌐 Load DNS config
with open("dns_config.json", "r", encoding="utf-8") as f:
    dns_config = json.load(f)

# --- WORKER UNTUK PROSES DOWNLOAD DI THREAD TERPISAH ---
class DownloadWorker(QObject):
    """Worker untuk menangani download yt-dlp di thread terpisah."""
    progress = pyqtSignal(int)
    finished = pyqtSignal(str, str) # status, message
    log = pyqtSignal(str, str) # message, status

    def run(self, cmd):
        try:
            self.log.emit("⬇️ Memulai unduhan...", "retry")
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith("win") else 0
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                creationflags=creationflags
            )

            for line in iter(process.stdout.readline, ''):
                # Cari persentase progress dari output yt-dlp
                match = re.search(r"\[download\]\s+([0-9\.]+)%", line)
                if match:
                    percent = float(match.group(1))
                    self.progress.emit(int(percent))
                
                # Kirim log real-time ke UI
                self.log.emit(line.strip(), "retry")

            process.wait()

            if process.returncode == 0:
                self.finished.emit("success", f"✅ Stream selesai ➤ {os.path.basename(cmd[-2])}")
            else:
                self.finished.emit("error", f"❌ Error unduh, cek log untuk detail.")

        except Exception as e:
            self.finished.emit("error", f"❌ Error kritis pada worker unduh: {str(e)}")


class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        # Migrasi Enum Qt.SplashScreen dan Qt.FramelessWindowHint
        self.setWindowFlags(Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint)
        self.setFixedSize(500, 500)
        self.setStyleSheet("background-color: black;")
        splash_label = QLabel(self)
        # Migrasi Enum Qt.KeepAspectRatio dan Qt.SmoothTransformation
        splash_label.setPixmap(QPixmap("video_splash.png").scaled(500, 500, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        # Migrasi Enum Qt.AlignCenter
        splash_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        splash_label.setGeometry(0, 0, 500, 500)

class ShrineDownloader(QWidget):
    def __init__(self):
        super().__init__()       
        try:
            with open("dns_config.json", "r", encoding="utf-8") as f:
                self.dns_config = json.load(f)
        except Exception as e:
            self.dns_config = {"dns_active": False, "dns_server": "1.1.1.1", "dns_label": "Cloudflare"}
            print(f"❌ Gagal load dns_config.json ➤ pakai default ➤ {str(e)}")
  
        self.setWindowIcon(QIcon("video.ico"))
        self.setWindowTitle("Macan Shrine Video Downloader - SilentStream Edition V3")
        self.output_folder = os.path.abspath("downloads")
        os.makedirs(self.output_folder, exist_ok=True)
        self.setup_ui()
        self.setup_downloader_thread()

    def setup_ui(self):
        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        self.url_input = QLineEdit(); self.url_input.setPlaceholderText("Masukkan URL Video")
        self.url_input.textChanged.connect(self.update_tooltip)
        left_layout.addWidget(self.url_input)

        self.tooltip_label = QLabel("ℹ️ Info Situs"); left_layout.addWidget(self.tooltip_label)

        self.res_combo = QComboBox()
        for res in CONFIG["format_map"]: self.res_combo.addItem(res)
        left_layout.addWidget(QLabel("Resolusi:")); left_layout.addWidget(self.res_combo)        

        tombol_layout = QHBoxLayout()
        self.download_button = QPushButton("⬇️ Single Download")
        self.download_button.clicked.connect(self.single_download)
        self.batch_button = QPushButton("🔁 Batch Download")
        self.batch_button.clicked.connect(self.batch_download)
        tombol_layout.addWidget(self.download_button); tombol_layout.addWidget(self.batch_button)
        left_layout.addLayout(tombol_layout)

        self.batch_input = QTextEdit()
        left_layout.addWidget(QLabel("Batch URL (max 10):")); left_layout.addWidget(self.batch_input)

        self.folder_button = QPushButton("📂 Lihat File Hasil")
        self.folder_button.clicked.connect(self.open_result_folder)
        left_layout.addWidget(self.folder_button) 

        self.shrine_browser_button = QPushButton("🌐 Buka Shrine Browser")
        self.shrine_browser_button.clicked.connect(self.open_shrine_browser)
        left_layout.addWidget(self.shrine_browser_button)       

        self.thumb_label = QLabel("Thumbnail:")
        self.thumb_frame = QLabel(); self.thumb_frame.setFixedSize(320, 180)
        self.title_label = QLabel("🎬 Judul Video: -")
        right_layout.addWidget(self.title_label)
        self.url_input.textChanged.connect(self.show_thumbnail)
        right_layout.addWidget(self.thumb_label); right_layout.addWidget(self.thumb_frame)
        self.meta_preview = QLabel("📊 Preview Resolusi & Durasi: -")
        right_layout.addWidget(self.meta_preview)

        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #44ff88; }")
        self.log_panel = QListWidget()
        self.reset_log_button = QPushButton("🗑️ Reset Log Shrine")
        self.reset_log_button.clicked.connect(self.reset_log)
        right_layout.addWidget(QLabel("📜 Log Shrine"))
        right_layout.addWidget(self.log_panel)
        right_layout.addWidget(self.progress_bar)
        right_layout.addWidget(self.reset_log_button)

        self.dns_button = QPushButton("⚙️ Ganti DNS")
        self.dns_button.clicked.connect(self.show_dns_dialog)
        right_layout.addWidget(self.dns_button)

        self.activate_dns_button = QPushButton("🛡️ Aktifkan DNS")
        self.activate_dns_button.clicked.connect(self.activate_dns)
        right_layout.addWidget(self.activate_dns_button)
        self.dns_status_label = QLabel("🛡️ Status DNS: Nonaktif")
        right_layout.addWidget(self.dns_status_label)        

        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)
        self.setLayout(main_layout)

    def setup_downloader_thread(self):
        self.thread = QThread()
        self.worker = DownloadWorker()
        self.worker.moveToThread(self.thread)

        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.log.connect(self.log_writer)
        self.worker.finished.connect(self.on_download_finished)
        self.thread.started.connect(lambda: self.worker.run(self.current_cmd))

    def on_download_finished(self, status, message):
        self.log_writer(message, status)
        self.progress_bar.setValue(100 if status == "success" else 0)
        self.thread.quit()
        self.thread.wait()
        # Aktifkan kembali tombol setelah selesai
        self.download_button.setEnabled(True)
        self.batch_button.setEnabled(True)

    def update_tooltip(self):
        url = self.url_input.text().strip()
        domain = url.split('/')[2] if '/' in url else ''
        tips = {
            "youtube.com": "✔️ YouTube biasanya bisa diunduh.",
            "udemy.com": "🔐 Udemy butuh login aktif.",
            "netflix.com": "❌ Netflix pakai DRM ➤ tidak bisa diunduh langsung."
        }
        self.tooltip_label.setText(tips.get(domain, "⚠️ Situs tidak dikenal ➤ shrine akan coba default."))

    def open_result_folder(self):
        path = os.path.abspath(self.output_folder)
        try: 
            os.startfile(path)
            self.log_writer(f"📂 Membuka folder ➤ {path}", "success")
        except Exception as e: 
            self.log_writer(f"❌ Gagal buka folder ➤ {str(e)}", "error")

    def reset_log(self):
        if os.path.exists("shrine_log.txt"):
            open("shrine_log.txt", "w").close()
        self.log_panel.clear()

    def log_writer(self, text, status="success"):
        color = {"success":"green", "retry":"orange", "error":"red"}.get(status,"black")
        item = QListWidgetItem(text)
        item.setForeground(QColor(color))
        self.log_panel.addItem(item)
        self.log_panel.scrollToBottom() # Auto-scroll
        with open("shrine_log.txt", "a", encoding="utf-8") as f: 
            f.write(f"{text}\n")

    def show_thumbnail(self):
        url = self.url_input.text().strip()
        if not url: return
        try:
            with yt_dlp.YoutubeDL({}) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get("title", "-")
                self.title_label.setText(f"🎬 Judul Video: {title}")
                self.log_writer(f"🧠 Judul ditemukan ➤ {title}", "retry")

                duration = info.get("duration", 0)
                height = info.get("height", "-")
                width = info.get("width", "-")

                def format_dur(sec):
                    h = int(sec // 3600); m = int((sec % 3600) // 60); s = int(sec % 60)
                    return f"{h}j {m}m {s}d" if h else f"{m}m {s}d"
                
                duration_str = format_dur(duration)
                self.meta_preview.setText(f"📊 Resolusi: {width}x{height} ➤ Durasi: {duration_str}")
                self.log_writer(f"🔍 Preview ➤ {width}x{height}, durasi {duration_str}", "retry")     
               
                thumb_url = info.get("thumbnail", None)  
                if thumb_url:
                    img_data = requests.get(thumb_url).content
                    pixmap = QPixmap()
                    pixmap.loadFromData(img_data)
                    self.thumb_frame.setPixmap(pixmap.scaled(320,180))
                    self.log_writer("🖼️ Thumbnail berhasil ditampilkan", "success")
                else:
                    self.thumb_frame.setText("⚠️ Thumbnail tidak tersedia")
                    self.log_writer("⚠️ Thumbnail tidak tersedia", "error")
        except Exception as e:
            self.title_label.setText("🎬 Judul Video: (gagal ambil)")
            self.thumb_frame.setText("⚠️ Thumbnail gagal ditampilkan.")
            self.meta_preview.setText("📊 Preview gagal diambil")
            self.log_writer(f"❌ Gagal ambil metadata ➤ {str(e)}", "error")

    def show_dns_dialog(self):
        new_dns, ok = QInputDialog.getText(self, "Ganti DNS", "Masukkan DNS Server:")
        if ok and new_dns:
            self.dns_config["dns_server"] = new_dns
            self.dns_config["dns_label"] = "Custom"
            with open("dns_config.json", "w", encoding="utf-8") as f:
                json.dump(self.dns_config, f, indent=4)
            self.meta_preview.setText(f"🌐 DNS diubah ke ➤ {new_dns}")
            self.log_writer(f"⚙️ DNS diubah ➤ {new_dns}", "success")
            self.apply_dns_config()

    def activate_dns(self):
        try:
            self.apply_dns_config()
            self.dns_status_label.setText(f"🛡️ Status DNS: Aktif ➤ {self.dns_config['dns_label']}")
            self.meta_preview.setText(f"🛡️ DNS diaktifkan ➤ {self.dns_config['dns_label']}")
            self.log_writer(f"🛡️ DNS aktif ➤ {self.dns_config['dns_label']} ➤ {self.dns_config['dns_server']}", "success")
        except Exception as e:
            self.dns_status_label.setText("🛡️ Status DNS: Gagal aktifkan")
            self.log_writer(f"❌ Gagal aktifkan DNS ➤ {str(e)}", "error")

    def apply_dns_config(self):
        try:
            dns_server = self.dns_config.get("dns_server", "1.1.1.1")
            resolver = dns.resolver.Resolver()
            resolver.nameservers = [dns_server]
            resolver.resolve("youtube.com") # Tes resolusi domain
            self.log_writer(f"🌐 DNS aktif ➤ {self.dns_config['dns_label']} ➤ {dns_server}", "success")
        except Exception as e:
            self.log_writer(f"❌ Gagal aktifkan DNS ➤ {str(e)}", "error")   
            raise e

    def single_download(self):
        url = self.url_input.text().strip()
        if not url: return
        self.try_download(url)

    def batch_download(self):
        # Note: Batch download will run sequentially. Progress bar will reset for each video.
        urls = self.batch_input.toPlainText().strip().split("\n")[:10]
        for i, url in enumerate(urls):
            if url.strip() and not self.thread.isRunning():
                self.log_writer(f"--- Memulai Batch Item {i+1}/{len(urls)} ---", "success")
                self.try_download(url.strip())
            elif self.thread.isRunning():
                self.log_writer("Harap tunggu unduhan sebelumnya selesai.", "error")
                break

    def try_download(self, url):
        if self.thread.isRunning():
            self.log_writer("Harap tunggu unduhan saat ini selesai!", "error")
            return

        res = self.res_combo.currentText()
        format_str = CONFIG["format_map"].get(res, "best")
        
        try:
            with yt_dlp.YoutubeDL({}) as ydl:
                info = ydl.extract_info(url, download=False)                
                title = info.get("title", "shrine_output").replace(" ", "_").replace("/", "-")
        except Exception as e:
            self.log_writer(f"❌ Gagal ambil info judul ➤ {str(e)}", "error")
            title = "shrine_output"

        output = os.path.join(self.output_folder, f"{title}_{res}.mp4")
        
        self.current_cmd = [
            "yt-dlp", "--no-part", "--no-continue",
            "--fragment-retries", str(CONFIG["fragment_retries"]),
            "--concurrent-fragments", str(CONFIG["concurrent_fragments"]),
            "--merge-output-format", CONFIG["merge_format"],
            "--format", format_str,
            "-o", output, url
        ]
        
        # Nonaktifkan tombol selama download
        self.download_button.setEnabled(False)
        self.batch_button.setEnabled(False)
        
        self.progress_bar.setValue(0)
        self.thread.start()

    def open_shrine_browser(self):
        try:
            # Pastikan variabel window tidak hilang karena garbage collection
            if not hasattr(self, 'browser_window'):
                self.browser_window = ShrineBrowser()
            self.browser_window.show()
        except Exception as e:
            QMessageBox.warning(self, "Error Shrine", f"⚠️ Gagal invoke Shrine Browser: {e}")
    
    def closeEvent(self, event):
        # Pastikan thread berhenti saat window ditutup
        if self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    splash = SplashScreen()
    splash.show()

    def launch_main():
        splash.close()
        global window 
        window = ShrineDownloader()
        window.log_writer("✅ Shrine UI muncul ➤ siap orbit 🧿", "success")
        window.show()

    QTimer.singleShot(2500, launch_main)
    # Migrasi exec_() ke exec()
    sys.exit(app.exec())