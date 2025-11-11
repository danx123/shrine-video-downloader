import sys, os, subprocess, requests, json, re, platform, tempfile
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QComboBox, QFileDialog, QProgressBar,
    QListWidget, QListWidgetItem, QMessageBox, QInputDialog, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtGui import QPixmap, QColor, QIcon
from PySide6.QtCore import Qt, QTimer, QThread, QObject, Signal

# --- CONFIG & LANGUAGE FILES (TETAP SAMA) ---
try:
    with open("video_config.json", "r", encoding="utf-8") as f:
        CONFIG = json.load(f)
except FileNotFoundError:
    QMessageBox.critical(None, "Config Error", "video_config.json not found!")
    sys.exit(1)

try:
    with open("dns_config.json", "r", encoding="utf-8") as f:
        dns_config = json.load(f)
except FileNotFoundError:
    dns_config = {"dns_active": False, "dns_server": "1.1.1.1", "dns_label": "Cloudflare"}

try:
    with open("languages.json", "r", encoding="utf-8") as f:
        LANGUAGES = json.load(f)
except FileNotFoundError:
    QMessageBox.critical(None, "Language File Error", "languages.json not found!")
    sys.exit(1)

# --- WORKERS FOR THREADING ---
class DownloadWorker(QObject):
    """Worker untuk menangani download yt-dlp di thread terpisah. (DIOPTIMALKAN)"""
    progress = Signal(int, int) # row, percentage
    finished = Signal(int, str, str) # row, status, message
    log = Signal(str, str) # message, status
    update_status = Signal(int, str) # row, status_text

    def run(self, cmd, row_index):
        try:
            self.log.emit("log_download_start", "retry")
            self.update_status.emit(row_index, self._t("status_downloading"))
            
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith("win") else 0
            
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding='utf-8', errors='replace', creationflags=creationflags
            )

            final_filepath = ""
            for line in iter(process.stdout.readline, ''):
                progress_match = re.search(r"\[download\]\s+([0-9\.]+)%", line)
                if progress_match:
                    percent = float(progress_match.group(1))
                    self.progress.emit(row_index, int(percent))
                
                if "[Merger]" in line:
                    self.update_status.emit(row_index, self._t("status_merging"))
                
                merge_match = re.search(r"\[Merger\] Merging formats into \"(.+?)\"", line)
                if merge_match:
                    final_filepath = merge_match.group(1)
                    
                mp3_match = re.search(r"\[ExtractAudio\] Destination: (.+?)\n", line)
                if mp3_match:
                    final_filepath = mp3_match.group(1)

                self.log.emit(line.strip(), "retry")

            process.wait()
            if not final_filepath and "-o" in cmd:
                 final_filepath = cmd[cmd.index("-o") + 1]

            if process.returncode == 0:
                self.finished.emit(row_index, "success", os.path.basename(final_filepath))
            else:
                self.finished.emit(row_index, "error", "log_download_error")
        except Exception as e:
            self.finished.emit(row_index, "error", f"log_worker_error\n{str(e)}")
    
    def _t(self, key): # Helper kecil untuk worker
        return LANGUAGES.get("id", {}).get(key, key)


# --- MetadataWorker & DnsWorker (TETAP SAMA) ---
class MetadataWorker(QObject):
    finished = Signal(dict)
    error = Signal(str)
    def run(self, url, yt_dlp_path):
        try:
            cmd = [yt_dlp_path, '--dump-json', '--no-playlist', url]
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith("win") else 0
            process = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', check=True, creationflags=creationflags)
            info = json.loads(process.stdout)
            thumb_url = info.get("thumbnail")
            img_data = requests.get(thumb_url).content if thumb_url else None
            result = {"title": info.get("title", "N/A"), "duration": info.get("duration", 0), "height": info.get("height", "N/A"), "width": info.get("width", "N/A"), "thumbnail_data": img_data}
            self.finished.emit(result)
        except Exception as e: self.error.emit(str(e))

class DnsWorker(QObject):
    finished = Signal(bool, str, str)
    def run(self, dns_server):
        try:
            resolver = dns.resolver.Resolver()
            resolver.nameservers = [dns_server]
            resolver.resolve("google.com", "A")
            self.finished.emit(True, dns_server, "")
        except Exception as e: self.finished.emit(False, dns_server, str(e))

class SplashScreen(QWidget):
    # ... (TETAP SAMA) ...
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint)
        self.setFixedSize(500, 500)
        self.setStyleSheet("background-color: black;")
        splash_label = QLabel(self)
        splash_label.setPixmap(QPixmap("video_splash.png").scaled(500, 500, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        splash_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        splash_label.setGeometry(0, 0, 500, 500)

class ShrineDownloader(QWidget):
    def __init__(self):
        super().__init__()
        self.current_lang = "id"
        self.dns_config = dns_config
        self.output_folder = os.path.abspath("downloads")
        os.makedirs(self.output_folder, exist_ok=True)
        
        # --- LOGGING YANG DIOPTIMALKAN ---
        log_handle, self.log_file_path = tempfile.mkstemp(suffix=".log", prefix="shrine_log_")
        os.close(log_handle)
        self.log_file = open(self.log_file_path, "a", encoding="utf-8")
        
        self.download_queue = [] # List untuk menyimpan data job
        self.current_download_index = -1
        self.is_downloading = False

        self.setWindowIcon(QIcon("video.ico"))
        self.setup_ui()
        self.setup_threads()
        self.retranslate_ui()

    def _t(self, key, **kwargs):
        default_val = kwargs.pop('default', key)
        return LANGUAGES.get(self.current_lang, {}).get(key, default_val).format(**kwargs)

    def get_yt_dlp_path(self):
        executable = "yt-dlp.exe" if platform.system() == "Windows" else "yt-dlp"
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, executable)
        else:
            return executable

    def setup_ui(self):
        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()
        
        # --- Sisi Kiri ---
        # Language, URL, Tooltip, Format (Sama seperti sebelumnya)
        lang_layout = QHBoxLayout(); self.lang_label = QLabel(); lang_layout.addWidget(self.lang_label); self.lang_combo = QComboBox(); self.lang_combo.addItem("Indonesia", "id"); self.lang_combo.addItem("English", "en"); self.lang_combo.currentIndexChanged.connect(self.switch_language); lang_layout.addWidget(self.lang_combo); left_layout.addLayout(lang_layout)
        self.url_input = QLineEdit(); self.meta_timer = QTimer(); self.meta_timer.setSingleShot(True); self.meta_timer.timeout.connect(self.fetch_metadata); self.url_input.textChanged.connect(lambda: self.meta_timer.start(800)); left_layout.addWidget(self.url_input)
        self.tooltip_label = QLabel(); left_layout.addWidget(self.tooltip_label)
        format_layout = QHBoxLayout(); self.format_label = QLabel("Format:"); self.format_combo = QComboBox(); self.format_combo.addItems(["Video (MP4)", "Audio (MP3)"]); self.format_combo.currentIndexChanged.connect(self.toggle_resolution_box); format_layout.addWidget(self.format_label); format_layout.addWidget(self.format_combo); left_layout.addLayout(format_layout)
        self.res_label = QLabel(); self.res_combo = QComboBox(); [self.res_combo.addItem(res) for res in CONFIG["format_map"]]; left_layout.addWidget(self.res_label); left_layout.addWidget(self.res_combo)

        # Tombol Add to Queue
        self.add_to_queue_button = QPushButton()
        self.add_to_queue_button.clicked.connect(self.add_to_queue)
        left_layout.addWidget(self.add_to_queue_button)

        # Tombol Start/Stop Download
        self.start_queue_button = QPushButton()
        self.start_queue_button.clicked.connect(self.process_queue)
        left_layout.addWidget(self.start_queue_button)

        # Checkbox Shutdown
        self.shutdown_checkbox = QCheckBox()
        left_layout.addWidget(self.shutdown_checkbox)
        
        # Tombol Folder
        self.folder_button = QPushButton()
        self.folder_button.clicked.connect(self.open_result_folder)
        left_layout.addWidget(self.folder_button)
        
        # --- Sisi Kanan ---
        # Metadata Preview (Sama)
        self.title_label = QLabel(); self.title_label.setWordWrap(True); right_layout.addWidget(self.title_label)
        self.thumb_label = QLabel(); self.thumb_frame = QLabel(); self.thumb_frame.setFixedSize(320, 180); self.thumb_frame.setStyleSheet("border: 1px solid gray;"); right_layout.addWidget(self.thumb_label); right_layout.addWidget(self.thumb_frame); self.meta_preview = QLabel(); right_layout.addWidget(self.meta_preview)

        # --- Bagian Bawah (Antrean & Log) ---
        bottom_layout = QVBoxLayout()
        self.queue_label = QLabel()
        bottom_layout.addWidget(self.queue_label)

        # --- WIDGET ANTRIAN BARU ---
        self.queue_table = QTableWidget()
        self.queue_table.setColumnCount(5)
        self.queue_table.setHorizontalHeaderLabels(["Title", "Format", "Resolution", "Progress", "Status"])
        self.queue_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.queue_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        bottom_layout.addWidget(self.queue_table)
        
        self.log_label = QLabel(); bottom_layout.addWidget(self.log_label)
        self.log_panel = QListWidget(); bottom_layout.addWidget(self.log_panel)
        self.reset_log_button = QPushButton(); self.reset_log_button.clicked.connect(self.reset_log); bottom_layout.addWidget(self.reset_log_button)

        # Gabungkan semua layout
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 1)
        
        full_layout = QVBoxLayout()
        full_layout.addLayout(main_layout)
        full_layout.addLayout(bottom_layout)
        self.setLayout(full_layout)

    def retranslate_ui(self):
        self.setWindowTitle(self._t("window_title"))
        self.url_input.setPlaceholderText(self._t("url_placeholder"))
        self.tooltip_label.setText(self._t("site_info"))
        self.res_label.setText(self._t("resolution"))
        self.add_to_queue_button.setText(self._t("add_to_queue", default="Add to Queue"))
        self.start_queue_button.setText(self._t("start_download", default="Start Download"))
        self.folder_button.setText(self._t("open_folder"))
        self.title_label.setText(self._t("video_title"))
        self.thumb_label.setText(self._t("thumbnail"))
        self.meta_preview.setText(self._t("meta_preview"))
        self.log_label.setText(self._t("log_title"))
        self.reset_log_button.setText(self._t("reset_log"))
        self.shutdown_checkbox.setText(self._t("shutdown_checkbox"))
        self.lang_label.setText(self._t("lang_select"))
        self.format_label.setText(self._t("format_label", default="Format:"))
        self.queue_label.setText(self._t("queue_label", default="Download Queue"))
        self.queue_table.setHorizontalHeaderLabels([
            self._t("queue_title", default="Title"),
            self._t("queue_format", default="Format"),
            self._t("queue_res", default="Resolution"),
            self._t("queue_progress", default="Progress"),
            self._t("queue_status", default="Status")
        ])

    def setup_threads(self):
        self.download_thread = QThread()
        self.download_worker = DownloadWorker()
        self.download_worker.moveToThread(self.download_thread)
        self.download_worker.progress.connect(self.update_progress_in_table)
        self.download_worker.update_status.connect(self.update_status_in_table)
        self.download_worker.log.connect(self.log_writer)
        self.download_worker.finished.connect(self.on_download_finished)
        
        self.meta_thread = QThread(); self.meta_worker = MetadataWorker(); self.meta_worker.moveToThread(self.meta_thread); self.meta_worker.finished.connect(self.update_ui_with_metadata); self.meta_worker.error.connect(lambda e: self.log_writer(self._t("log_meta_fail", error=e), "error"))
        # DNS thread tetap sama

    def add_to_queue(self):
        url = self.url_input.text().strip()
        if not url: return

        job = {
            "url": url,
            "title": self.title_label.text().replace(self._t("video_title"), "").strip() or "Fetching title...",
            "format": self.format_combo.currentText(),
            "resolution": self.res_combo.currentText() if self.format_combo.currentIndex() == 0 else "N/A",
            "status": "Queued"
        }
        self.download_queue.append(job)
        self.add_job_to_table(job)
        self.url_input.clear()
        self.title_label.setText(self._t("video_title"))
        self.thumb_frame.clear()

    def add_job_to_table(self, job):
        row_position = self.queue_table.rowCount()
        self.queue_table.insertRow(row_position)
        
        self.queue_table.setItem(row_position, 0, QTableWidgetItem(job["title"]))
        self.queue_table.setItem(row_position, 1, QTableWidgetItem(job["format"]))
        self.queue_table.setItem(row_position, 2, QTableWidgetItem(job["resolution"]))
        
        progress_bar = QProgressBar()
        progress_bar.setValue(0)
        progress_bar.setStyleSheet("QProgressBar { text-align: center; } QProgressBar::chunk { background-color: #44ff88; }")
        self.queue_table.setCellWidget(row_position, 3, progress_bar)
        
        self.queue_table.setItem(row_position, 4, QTableWidgetItem(self._t("status_queued", default="Queued")))

    def process_queue(self):
        if self.is_downloading: # Nanti jadi tombol "Stop"
            # Logika untuk stop/cancel
            pass
        else:
            self.is_downloading = True
            self.start_queue_button.setText(self._t("stop_download", default="Stop Download"))
            self.start_next_in_queue()

    def start_next_in_queue(self):
        if self.current_download_index >= 0: # Cek jika ada download sebelumnya
             self.update_status_in_table(self.current_download_index, self._t("status_completed", default="Completed"))

        # Cari job berikutnya yang masih "Queued"
        next_job_index = -1
        for i, job in enumerate(self.download_queue):
            if job["status"] == "Queued":
                next_job_index = i
                break
        
        if next_job_index == -1:
            self.log_writer("All downloads finished!", "success")
            self.is_downloading = False
            self.start_queue_button.setText(self._t("start_download", default="Start Download"))
            if self.shutdown_checkbox.isChecked():
                self.initiate_shutdown()
            return

        self.current_download_index = next_job_index
        job = self.download_queue[self.current_download_index]
        job["status"] = "Downloading"

        # ... (Kode untuk membangun `cmd` dari `job` sama seperti `start_next_in_batch` sebelumnya) ...
        yt_dlp_path = self.get_yt_dlp_path(); base_cmd = [yt_dlp_path, "--no-part", "--no-continue", "--fragment-retries", str(CONFIG["fragment_retries"]), "--concurrent-fragments", str(CONFIG["concurrent_fragments"])]
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            ffmpeg_path = os.path.join(sys._MEIPASS, "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg")
            if os.path.exists(ffmpeg_path): base_cmd.extend(["--ffmpeg-location", ffmpeg_path])
        
        if job["format"] == "Audio (MP3)":
            output_template = os.path.join(self.output_folder, "%(title)s.%(ext)s")
            cmd = base_cmd + ["-f", "bestaudio/best", "--extract-audio", "--audio-format", "mp3", "--audio-quality", "0", "-o", output_template, job["url"]]
        else: # Video
            res = job["resolution"]; format_str = CONFIG["format_map"].get(res, "best"); output_template = os.path.join(self.output_folder, f"%(title)s_{res}.%(ext)s")
            cmd = base_cmd + ["--merge-output-format", CONFIG["merge_format"], "--format", format_str, "-o", output_template, job["url"]]

        self.download_thread.started.connect(lambda: self.download_worker.run(cmd, self.current_download_index))
        self.download_thread.start()

    def on_download_finished(self, row, status, message):
        self.download_thread.quit()
        self.download_thread.wait()

        if status == "success":
            final_message = self._t("log_download_success") + f" ➤ {message}"
            self.download_queue[row]["status"] = "Completed"
            self.update_status_in_table(row, self._t("status_completed", default="Completed"))
        else:
            final_message = self._t(message, default=message)
            self.download_queue[row]["status"] = "Error"
            self.update_status_in_table(row, self._t("status_error", default="Error"))

        self.log_writer(final_message, status)
        self.start_next_in_queue() # Lanjut ke item berikutnya

    def update_progress_in_table(self, row, percentage):
        progress_bar = self.queue_table.cellWidget(row, 3)
        if progress_bar:
            progress_bar.setValue(percentage)

    def update_status_in_table(self, row, status_text):
        status_item = self.queue_table.item(row, 4)
        if status_item:
            status_item.setText(status_text)
        else:
            self.queue_table.setItem(row, 4, QTableWidgetItem(status_text))

    def log_writer(self, text, status="success"):
        # --- LOG WRITER YANG SUDAH DIOPTIMALKAN ---
        color = {"success": "green", "retry": "orange", "error": "red"}.get(status, "black")
        
        # 1. Update UI (Cepat)
        item_text = self._t(text) if text in LANGUAGES.get(self.current_lang, {}) else text
        item = QListWidgetItem(f"[{datetime.now().strftime('%H:%M:%S')}] {item_text}")
        item.setForeground(QColor(color))
        self.log_panel.addItem(item)
        self.log_panel.scrollToBottom()

        # 2. Tulis ke file log (Operasi Append, Sangat Ringan)
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "message": text.strip() # Hapus whitespace aneh dari log yt-dlp
        }
        self.log_file.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        self.log_file.flush() # Pastikan data langsung tertulis ke disk

    def reset_log(self):
        self.log_panel.clear()
        # Reset file log
        self.log_file.close()
        self.log_file = open(self.log_file_path, "w", encoding="utf-8") # Buka dengan mode 'w' untuk mengosongkan

    def closeEvent(self, event):
        # --- PASTIKAN SEMUA DITUTUP DENGAN BENAR ---
        if self.log_file:
            self.log_file.close()
        if os.path.exists(self.log_file_path):
            try: os.remove(self.log_file_path)
            except OSError: pass

        for thread in [self.download_thread, self.meta_thread]: # Tambahkan dns_thread jika ada
            if thread.isRunning():
                thread.quit()
                thread.wait(2000) # Tunggu maks 2 detik
        event.accept()
        
    # --- Fungsi lainnya (fetch_metadata, update_ui_with_metadata, initiate_shutdown, open_result_folder, dll) sebagian besar tetap sama ---
    # ... (salin sisa fungsi dari script aslimu, pastikan penyesuaian kecil jika ada) ...
    def switch_language(self, index): self.current_lang = self.lang_combo.itemData(index); self.retranslate_ui()
    def toggle_resolution_box(self): is_audio = self.format_combo.currentText() == "Audio (MP3)"; self.res_combo.setEnabled(not is_audio); self.res_label.setEnabled(not is_audio)
    def fetch_metadata(self):
        if self.meta_thread.isRunning(): return
        url = self.url_input.text().strip()
        if not url: return
        yt_dlp_path = self.get_yt_dlp_path()
        # Disconnect dulu untuk mencegah koneksi ganda
        try: self.meta_thread.started.disconnect()
        except RuntimeError: pass
        self.meta_thread.started.connect(lambda: self.meta_worker.run(url, yt_dlp_path))
        self.meta_thread.start()
    def update_ui_with_metadata(self, info):
        self.title_label.setText(self._t("video_title") + " " + info["title"])
        def format_dur(sec): h = int(sec // 3600); m = int((sec % 3600) // 60); s = int(sec % 60); return f"{h}h {m}m {s}s" if h else f"{m}m {s}s"
        duration_str = format_dur(info["duration"]); res_str = f"{info['width']}x{info['height']}"
        self.meta_preview.setText(self._t("meta_preview") + f" {res_str} | {duration_str}")
        if info["thumbnail_data"]: pixmap = QPixmap(); pixmap.loadFromData(info["thumbnail_data"]); self.thumb_frame.setPixmap(pixmap.scaled(320, 180, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else: self.thumb_frame.setText(self._t("log_thumb_fail"))
        self.meta_thread.quit(); self.meta_thread.wait()
    def open_result_folder(self):
        path = os.path.abspath(self.output_folder)
        try:
            if platform.system() == "Windows": os.startfile(path)
            elif platform.system() == "Darwin": subprocess.Popen(["open", path])
            else: subprocess.Popen(["xdg-open", path])
        except Exception as e: self.log_writer(self._t("log_folder_fail", error=str(e)), "error")
    def initiate_shutdown(self):
        system = platform.system()
        try:
            if system == "Windows": os.system("shutdown /s /t 1")
            else: os.system("sudo shutdown -h now")
        except Exception: pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    splash = SplashScreen()
    splash.show()

    def launch_main():
        splash.close()
        global window
        window = ShrineDownloader()
        window.log_writer("✅ Shrine UI v5.1 loaded ➤ ready to conquer 🧿", "success")
        window.show()

    QTimer.singleShot(2500, launch_main)
    sys.exit(app.exec())