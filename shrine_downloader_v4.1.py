import sys, os, subprocess, requests, json, re, platform
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QTextEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QComboBox, QFileDialog, QProgressBar,
    QListWidget, QListWidgetItem, QMessageBox, QInputDialog, QCheckBox
)
from PyQt6.QtGui import QPixmap, QColor, QIcon
from PyQt6.QtCore import Qt, QTimer, QThread, QObject, pyqtSignal
import yt_dlp
import dns.resolver
from shrine_browser import ShrineBrowser # Pastikan shrine_browser.py juga ada

# --- CONFIG & LANGUAGE FILES ---
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
    """Worker untuk menangani download yt-dlp di thread terpisah."""
    progress = pyqtSignal(int)
    finished = pyqtSignal(str, str) # status, message
    log = pyqtSignal(str, str) # message, status

    def run(self, cmd):
        try:
            self.log.emit("log_download_start", "retry")
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith("win") else 0
            
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding='utf-8', errors='replace', creationflags=creationflags
            )

            for line in iter(process.stdout.readline, ''):
                match = re.search(r"\[download\]\s+([0-9\.]+)%", line)
                if match:
                    percent = float(match.group(1))
                    self.progress.emit(int(percent))
                self.log.emit(line.strip(), "retry")

            process.wait()
            if process.returncode == 0:
                self.finished.emit("success", os.path.basename(cmd[-2]))
            else:
                self.finished.emit("error", "log_download_error")
        except Exception as e:
            self.finished.emit("error", f"log_worker_error\n{str(e)}")

class MetadataWorker(QObject):
    """Worker untuk mengambil metadata video di thread terpisah agar UI tidak hang."""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def run(self, url):
        try:
            with yt_dlp.YoutubeDL({'noplaylist': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                
                thumb_url = info.get("thumbnail")
                img_data = requests.get(thumb_url).content if thumb_url else None

                result = {
                    "title": info.get("title", "N/A"),
                    "duration": info.get("duration", 0),
                    "height": info.get("height", "N/A"),
                    "width": info.get("width", "N/A"),
                    "thumbnail_data": img_data
                }
                self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class SplashScreen(QWidget):
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

        self.batch_queue = []
        self.current_batch_total = 0

        self.setWindowIcon(QIcon("video.ico"))
        self.setup_ui()
        self.setup_threads()
        self.retranslate_ui() # Set initial language

    def _t(self, key, **kwargs):
        """Helper untuk translasi teks."""
        return LANGUAGES[self.current_lang].get(key, key).format(**kwargs)

    def setup_ui(self):
        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()
        
        # Language Selector
        lang_layout = QHBoxLayout()
        self.lang_label = QLabel()
        lang_layout.addWidget(self.lang_label)
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("Indonesia", "id")
        self.lang_combo.addItem("English", "en")
        self.lang_combo.currentIndexChanged.connect(self.switch_language)
        lang_layout.addWidget(self.lang_combo)
        left_layout.addLayout(lang_layout)

        self.url_input = QLineEdit()
        self.meta_timer = QTimer()
        self.meta_timer.setSingleShot(True)
        self.meta_timer.timeout.connect(self.fetch_metadata)
        self.url_input.textChanged.connect(lambda: self.meta_timer.start(600)) # Debounce
        left_layout.addWidget(self.url_input)

        self.tooltip_label = QLabel()
        left_layout.addWidget(self.tooltip_label)

        self.res_label = QLabel()
        self.res_combo = QComboBox()
        for res in CONFIG["format_map"]: self.res_combo.addItem(res)
        left_layout.addWidget(self.res_label)
        left_layout.addWidget(self.res_combo)

        tombol_layout = QHBoxLayout()
        self.download_button = QPushButton()
        self.download_button.clicked.connect(self.single_download)
        self.batch_button = QPushButton()
        self.batch_button.clicked.connect(self.batch_download)
        tombol_layout.addWidget(self.download_button)
        tombol_layout.addWidget(self.batch_button)
        left_layout.addLayout(tombol_layout)

        self.batch_label = QLabel()
        self.batch_input = QTextEdit()
        left_layout.addWidget(self.batch_label)
        left_layout.addWidget(self.batch_input)
        
        self.shutdown_checkbox = QCheckBox()
        left_layout.addWidget(self.shutdown_checkbox)

        self.folder_button = QPushButton()
        self.folder_button.clicked.connect(self.open_result_folder)
        left_layout.addWidget(self.folder_button)

        self.shrine_browser_button = QPushButton()
        self.shrine_browser_button.clicked.connect(self.open_shrine_browser)
        left_layout.addWidget(self.shrine_browser_button)

        # Right Layout
        self.title_label = QLabel()
        self.title_label.setWordWrap(True)
        right_layout.addWidget(self.title_label)
        
        self.thumb_label = QLabel()
        self.thumb_frame = QLabel()
        self.thumb_frame.setFixedSize(320, 180)
        self.thumb_frame.setStyleSheet("border: 1px solid gray;")
        right_layout.addWidget(self.thumb_label)
        right_layout.addWidget(self.thumb_frame)
        self.meta_preview = QLabel()
        right_layout.addWidget(self.meta_preview)

        self.log_label = QLabel()
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #44ff88; }")
        self.log_panel = QListWidget()
        self.reset_log_button = QPushButton()
        self.reset_log_button.clicked.connect(self.reset_log)
        right_layout.addWidget(self.log_label)
        right_layout.addWidget(self.log_panel)
        right_layout.addWidget(self.progress_bar)
        right_layout.addWidget(self.reset_log_button)

        self.dns_button = QPushButton()
        self.dns_button.clicked.connect(self.show_dns_dialog)
        self.activate_dns_button = QPushButton()
        self.activate_dns_button.clicked.connect(self.activate_dns)
        self.dns_status_label = QLabel()
        right_layout.addWidget(self.dns_button)
        right_layout.addWidget(self.activate_dns_button)
        right_layout.addWidget(self.dns_status_label)

        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 1)
        self.setLayout(main_layout)

    def retranslate_ui(self):
        """Update all UI texts based on the current language."""
        self.setWindowTitle(self._t("window_title"))
        self.url_input.setPlaceholderText(self._t("url_placeholder"))
        self.tooltip_label.setText(self._t("site_info"))
        self.res_label.setText(self._t("resolution"))
        self.download_button.setText(self._t("single_download"))
        self.batch_button.setText(self._t("batch_download"))
        self.batch_label.setText(self._t("batch_urls"))
        self.folder_button.setText(self._t("open_folder"))
        self.shrine_browser_button.setText(self._t("shrine_browser"))
        self.title_label.setText(self._t("video_title"))
        self.thumb_label.setText(self._t("thumbnail"))
        self.meta_preview.setText(self._t("meta_preview"))
        self.log_label.setText(self._t("log_title"))
        self.reset_log_button.setText(self._t("reset_log"))
        self.dns_button.setText(self._t("dns_change"))
        self.activate_dns_button.setText(self._t("dns_activate"))
        self.dns_status_label.setText(self._t("dns_status_inactive"))
        self.shutdown_checkbox.setText(self._t("shutdown_checkbox"))
        self.lang_label.setText(self._t("lang_select"))

    def switch_language(self, index):
        self.current_lang = self.lang_combo.itemData(index)
        self.retranslate_ui()

    def setup_threads(self):
        self.download_thread = QThread()
        self.download_worker = DownloadWorker()
        self.download_worker.moveToThread(self.download_thread)
        self.download_worker.progress.connect(self.progress_bar.setValue)
        self.download_worker.log.connect(self.log_writer)
        self.download_worker.finished.connect(self.on_download_finished)
        self.download_thread.started.connect(lambda: self.download_worker.run(self.current_cmd))
        
        self.meta_thread = QThread()
        self.meta_worker = MetadataWorker()
        self.meta_worker.moveToThread(self.meta_thread)
        self.meta_worker.finished.connect(self.update_ui_with_metadata)
        self.meta_worker.error.connect(lambda e: self.log_writer(self._t("log_meta_fail", error=e), "error"))
        self.meta_thread.started.connect(lambda: self.meta_worker.run(self.url_input.text().strip()))

    def fetch_metadata(self):
        if self.meta_thread.isRunning(): return
        url = self.url_input.text().strip()
        if not url: return
        self.meta_thread.start()

    def update_ui_with_metadata(self, info):
        self.title_label.setText(self._t("video_title") + " " + info["title"])
        self.log_writer(self._t("log_title_found", title=info["title"]), "retry")

        def format_dur(sec):
            h = int(sec // 3600); m = int((sec % 3600) // 60); s = int(sec % 60)
            return f"{h}h {m}m {s}s" if h else f"{m}m {s}s"
        
        duration_str = format_dur(info["duration"])
        res_str = f"{info['width']}x{info['height']}"
        self.meta_preview.setText(self._t("meta_preview") + f" {res_str} | {duration_str}")
        self.log_writer(self._t("log_preview_found", res=res_str, dur=duration_str), "retry")

        if info["thumbnail_data"]:
            pixmap = QPixmap()
            pixmap.loadFromData(info["thumbnail_data"])
            self.thumb_frame.setPixmap(pixmap.scaled(320, 180, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            self.log_writer(self._t("log_thumb_success"), "success")
        else:
            self.thumb_frame.setText(self._t("log_thumb_fail"))
            self.log_writer(self._t("log_thumb_fail"), "error")
            
        self.meta_thread.quit()
        self.meta_thread.wait()

    def on_download_finished(self, status, message):
        self.progress_bar.setValue(100 if status == "success" else 0)
        final_message = self._t("log_download_success") + f" ➤ {message}" if status == "success" else self._t(message)
        self.log_writer(final_message, status)
        
        self.download_thread.quit()
        self.download_thread.wait()
        
        if self.batch_queue: # If there are more items in batch
            self.start_next_in_batch()
        else: # Last download finished
            self.set_buttons_enabled(True)
            if self.shutdown_checkbox.isChecked():
                self.initiate_shutdown()

    def set_buttons_enabled(self, enabled):
        self.download_button.setEnabled(enabled)
        self.batch_button.setEnabled(enabled)

    def single_download(self):
        url = self.url_input.text().strip()
        if not url: return
        self.batch_queue = [url]
        self.current_batch_total = 1
        self.start_next_in_batch()

    def batch_download(self):
        urls = [url.strip() for url in self.batch_input.toPlainText().strip().split("\n") if url.strip()]
        if not urls: return
        self.batch_queue = urls
        self.current_batch_total = len(urls)
        self.start_next_in_batch()

    def start_next_in_batch(self):
        if self.download_thread.isRunning():
            self.log_writer(self._t("msg_wait"), "error")
            return
        
        if not self.batch_queue: # Should not happen, but as a safeguard
            self.set_buttons_enabled(True)
            return

        url = self.batch_queue.pop(0)
        current_item_num = self.current_batch_total - len(self.batch_queue)
        self.log_writer(self._t("msg_batch_start", current=current_item_num, total=self.current_batch_total), "success")

        res = self.res_combo.currentText()
        format_str = CONFIG["format_map"].get(res, "best")
        
        # Simple title fetching without blocking
        try:
            with yt_dlp.YoutubeDL({'noplaylist': True, 'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get("title", "shrine_output").replace(" ", "_").replace("/", "-").replace("\\", "-")[:100]
        except:
            title = f"shrine_output_{datetime.now():%Y%m%d%H%M%S}"
        
        output = os.path.join(self.output_folder, f"{title}_{res}.mp4")
        
        self.current_cmd = [
            "yt-dlp", "--no-part", "--no-continue",
            "--fragment-retries", str(CONFIG["fragment_retries"]),
            "--concurrent-fragments", str(CONFIG["concurrent_fragments"]),
            "--merge-output-format", CONFIG["merge_format"],
            "--format", format_str, "-o", output, url
        ]
        
        self.set_buttons_enabled(False)
        self.progress_bar.setValue(0)
        self.download_thread.start()

    def initiate_shutdown(self):
        """
        [FIXED] Mematikan PC secara langsung tanpa dialog konfirmasi atau notifikasi log.
        Hanya menjalankan perintah shutdown sesuai sistem operasi.
        """
        system = platform.system()
        try:
            if system == "Windows":
                os.system("shutdown /s /t 1")
            elif system == "Linux" or system == "Darwin": # Darwin is macOS
                os.system("sudo shutdown -h now")
        except Exception:
            # Gagal mematikan PC, tidak ada notifikasi yang ditampilkan
            pass

    def log_writer(self, text, status="success"):
        """Writes log to UI panel and shrine_log.json."""
        log_file = "shrine_log.json"
        
        # UI Log
        color = {"success": "green", "retry": "orange", "error": "red"}.get(status, "black")
        item = QListWidgetItem(self._t(text) if text in LANGUAGES[self.current_lang] else text)
        item.setForeground(QColor(color))
        self.log_panel.addItem(item)
        self.log_panel.scrollToBottom()

        # JSON File Log
        logs = []
        if os.path.exists(log_file):
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    logs = json.load(f)
            except json.JSONDecodeError:
                logs = [] # Reset if file is corrupted

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "message": text
        }
        logs.append(log_entry)

        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=4, ensure_ascii=False)

    def reset_log(self):
        log_file = "shrine_log.json"
        if os.path.exists(log_file):
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump([], f) # Write an empty list
        self.log_panel.clear()

    # --- Other functions (unchanged logic but might use _t) ---
    def open_result_folder(self):
        path = os.path.abspath(self.output_folder)
        try:
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
            self.log_writer(self._t("log_folder_open", path=path), "success")
        except Exception as e:
            self.log_writer(self._t("log_folder_fail", error=str(e)), "error")

    def open_shrine_browser(self):
        try:
            if not hasattr(self, 'browser_window') or not self.browser_window.isVisible():
                self.browser_window = ShrineBrowser()
            self.browser_window.show()
            self.browser_window.activateWindow()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to invoke Shrine Browser: {e}")

    def show_dns_dialog(self): # Logic remains mostly the same
        new_dns, ok = QInputDialog.getText(self, "Change DNS", "Enter DNS Server:")
        if ok and new_dns:
            self.dns_config["dns_server"] = new_dns
            self.dns_config["dns_label"] = "Custom"
            with open("dns_config.json", "w", encoding="utf-8") as f:
                json.dump(self.dns_config, f, indent=4)
            self.log_writer(f"DNS changed to ➤ {new_dns}", "success")

    def activate_dns(self): # Logic remains mostly the same
        try:
            dns_server = self.dns_config.get("dns_server", "1.1.1.1")
            resolver = dns.resolver.Resolver()
            resolver.nameservers = [dns_server]
            resolver.resolve("youtube.com", "A") # Test resolution
            label = self.dns_config['dns_label']
            self.dns_status_label.setText(self._t("dns_status_active") + f" ➤ {label}")
            self.log_writer(f"DNS active ➤ {label} ➤ {dns_server}", "success")
        except Exception as e:
            self.dns_status_label.setText(self._t("dns_status_failed"))
            self.log_writer(f"Failed to activate DNS ➤ {str(e)}", "error")
            
    def closeEvent(self, event):
        if self.download_thread.isRunning():
            self.download_thread.quit()
            self.download_thread.wait()
        if self.meta_thread.isRunning():
            self.meta_thread.quit()
            self.meta_thread.wait()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    splash = SplashScreen()
    splash.show()

    def launch_main():
        splash.close()
        global window
        window = ShrineDownloader()
        window.log_writer("✅ Shrine UI loaded ➤ ready to orbit 🧿", "success")
        window.show()

    QTimer.singleShot(2500, launch_main)
    sys.exit(app.exec())