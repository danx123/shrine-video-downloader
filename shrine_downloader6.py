import sys, os, subprocess, requests, json, re, platform, tempfile
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QHBoxLayout, QComboBox, QFileDialog, QProgressBar, QMessageBox,
    QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
    QPlainTextEdit, QSizePolicy
)
from PySide6.QtGui import QPixmap, QColor, QIcon, QFont
from PySide6.QtCore import Qt, QTimer, QThread, QObject, Signal

# --- CONFIG & LANGUAGE FILES ---
# Memuat file konfigurasi dan bahasa, sama seperti sebelumnya.
# Pastikan file video_config.json, dns_config.json, dan languages.json ada di direktori yang sama.
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
# Worker untuk download, sudah dioptimalkan di kode Anda dan dipertahankan.
class DownloadWorker(QObject):
    progress = Signal(int, int)
    finished = Signal(int, str, str)
    log = Signal(str, str)
    update_status = Signal(int, str)

    def __init__(self, lang_pack):
        super().__init__()
        self.lang_pack = lang_pack

    def _t(self, key):
        return self.lang_pack.get(key, key)

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
                if progress_match := re.search(r"\[download\]\s+([0-9\.]+)%", line):
                    self.progress.emit(row_index, int(float(progress_match.group(1))))
                if "[Merger]" in line:
                    self.update_status.emit(row_index, self._t("status_merging"))
                if merge_match := re.search(r"\[Merger\] Merging formats into \"(.+?)\"", line):
                    final_filepath = merge_match.group(1)
                if mp3_match := re.search(r"\[ExtractAudio\] Destination: (.+?)\n", line):
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

# Worker untuk mengambil metadata (judul, thumbnail).
# Diubah untuk membawa 'row' agar tahu baris mana yang harus diperbarui.
class MetadataWorker(QObject):
    finished = Signal(dict, int) # Mengirimkan hasil dan nomor baris
    error = Signal(str, int)    # Mengirimkan error dan nomor baris

    def run(self, url, yt_dlp_path, row):
        try:
            cmd = [yt_dlp_path, '--dump-json', '--no-playlist', url]
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith("win") else 0
            process = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', check=True, creationflags=creationflags)
            info = json.loads(process.stdout)
            thumb_url = info.get("thumbnail")
            img_data = requests.get(thumb_url).content if thumb_url else None
            result = {"title": info.get("title", "N/A"), "thumbnail_data": img_data, "url": url}
            self.finished.emit(result, row)
        except Exception as e:
            self.error.emit(str(e), row)

# --- Main Application Window ---
class ShrineDownloader(QWidget):
    def __init__(self):
        super().__init__()
        self.current_lang = "id"
        self.output_folder = os.path.abspath("downloads")
        os.makedirs(self.output_folder, exist_ok=True)
        
        self.download_queue_data = [] # Menyimpan data lengkap job
        self.is_downloading = False
        self.current_download_index = -1
        self.meta_threads = [] # Menyimpan referensi thread metadata agar tidak hilang

        self.init_ui()
        self.connect_signals()
        self.retranslate_ui()
        self.apply_stylesheet()

    def _t(self, key, **kwargs):
        return LANGUAGES.get(self.current_lang, {}).get(key, key).format(**kwargs)

    def get_yt_dlp_path(self):
        executable = "yt-dlp.exe" if platform.system() == "Windows" else "yt-dlp"
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, executable)
        return executable

    def init_ui(self):
        """Membangun semua elemen UI dengan layout yang baru."""
        main_layout = QVBoxLayout(self)
        top_layout = QHBoxLayout()

        # --- KOLOM KIRI: KONTROL & BATCH ---
        left_column = QVBoxLayout()
        
        # Grup Kontrol
        controls_group = QGroupBox()
        controls_layout = QVBoxLayout()
        
        self.url_input = QLineEdit()
        self.format_label = QLabel()
        self.format_combo = QComboBox()
        self.format_combo.addItems(["Video (MP4)", "Audio (MP3)"])
        self.res_label = QLabel()
        self.res_combo = QComboBox()
        self.res_combo.addItems(CONFIG["format_map"].keys())
        self.add_single_button = QPushButton()
        
        controls_layout.addWidget(self.url_input)
        controls_layout.addWidget(self.format_label)
        controls_layout.addWidget(self.format_combo)
        controls_layout.addWidget(self.res_label)
        controls_layout.addWidget(self.res_combo)
        controls_layout.addWidget(self.add_single_button)
        controls_group.setLayout(controls_layout)
        left_column.addWidget(controls_group)

        # Grup Batch
        batch_group = QGroupBox()
        batch_layout = QVBoxLayout()
        self.batch_urls_input = QPlainTextEdit()
        self.add_batch_button = QPushButton()
        batch_layout.addWidget(self.batch_urls_input)
        batch_layout.addWidget(self.add_batch_button)
        batch_group.setLayout(batch_layout)
        left_column.addWidget(batch_group)
        
        left_column.addStretch(1) # Pendorong agar grup tetap di atas

        # --- KOLOM KANAN: ANTRIAN & AKSI ---
        right_column = QVBoxLayout()
        queue_group = QGroupBox()
        queue_layout = QVBoxLayout()
        
        self.queue_table = QTableWidget()
        self.queue_table.setColumnCount(5)
        self.queue_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.queue_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.queue_table.verticalHeader().setVisible(False)
        self.queue_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.queue_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.queue_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        queue_layout.addWidget(self.queue_table)
        queue_group.setLayout(queue_layout)
        right_column.addWidget(queue_group)
        
        # Tombol Aksi di bawah antrean
        action_buttons_layout = QHBoxLayout()
        self.start_queue_button = QPushButton()
        self.open_folder_button = QPushButton()
        self.shutdown_checkbox = QCheckBox()
        action_buttons_layout.addWidget(self.start_queue_button)
        action_buttons_layout.addWidget(self.open_folder_button)
        action_buttons_layout.addStretch(1)
        action_buttons_layout.addWidget(self.shutdown_checkbox)
        right_column.addLayout(action_buttons_layout)

        top_layout.addLayout(left_column, 1)
        top_layout.addLayout(right_column, 3) # Kolom kanan 3x lebih besar
        main_layout.addLayout(top_layout)

        self.setWindowTitle(self._t("window_title"))
        self.setWindowIcon(QIcon("video.ico")) # Ganti dengan path ikon Anda
        self.setMinimumSize(1000, 600)

    def connect_signals(self):
        """Menghubungkan sinyal dari widget ke slot (fungsi)."""
        self.format_combo.currentIndexChanged.connect(self.toggle_resolution_box)
        self.add_single_button.clicked.connect(self.add_single_url)
        self.add_batch_button.clicked.connect(self.add_batch_urls)
        self.start_queue_button.clicked.connect(self.process_queue)
        self.open_folder_button.clicked.connect(self.open_result_folder)

    def retranslate_ui(self):
        """Memperbarui teks UI berdasarkan bahasa yang dipilih."""
        self.setWindowTitle(self._t("window_title"))
        # Grup Kontrol
        self.findChild(QGroupBox).setTitle(self._t("controls_group_title", default="Controls"))
        self.url_input.setPlaceholderText(self._t("url_placeholder"))
        self.format_label.setText(self._t("format_label"))
        self.res_label.setText(self._t("resolution"))
        self.add_single_button.setText(self._t("add_single_button", default="Add Single Video"))
        # Grup Batch
        self.findChildren(QGroupBox)[1].setTitle(self._t("batch_group_title", default="Batch Mode"))
        self.batch_urls_input.setPlaceholderText(self._t("batch_urls_placeholder", default="Paste multiple URLs here, one per line..."))
        self.add_batch_button.setText(self._t("add_batch_button", default="Add from Batch"))
        # Grup Antrean
        self.findChildren(QGroupBox)[2].setTitle(self._t("queue_group_title", default="Download Queue"))
        self.queue_table.setHorizontalHeaderLabels([
            self._t("queue_thumb", default=""),
            self._t("queue_title", default="Title"),
            self._t("queue_format", default="Details"),
            self._t("queue_progress", default="Progress"),
            self._t("queue_status", default="Status")
        ])
        # Tombol Aksi
        self.start_queue_button.setText(self._t("start_download", default="Start Download"))
        self.open_folder_button.setText(self._t("open_folder"))
        self.shutdown_checkbox.setText(self._t("shutdown_checkbox"))
        
        # Set Ikon
        # Ganti path ini jika ikon Anda berada di folder lain.
        icon_path = "icons/"
        self.add_single_button.setIcon(QIcon(icon_path + "add.png"))
        self.add_batch_button.setIcon(QIcon(icon_path + "batch-add.png"))
        self.start_queue_button.setIcon(QIcon(icon_path + "download.png"))
        self.open_folder_button.setIcon(QIcon(icon_path + "folder.png"))


    def add_single_url(self):
        """Menambahkan satu URL dari input."""
        url = self.url_input.text().strip()
        if url:
            self.add_to_queue([url])
            self.url_input.clear()
            
    def add_batch_urls(self):
        """Menambahkan banyak URL dari area teks batch."""
        urls = self.batch_urls_input.toPlainText().strip().split('\n')
        urls = [u.strip() for u in urls if u.strip()]
        if urls:
            self.add_to_queue(urls)
            self.batch_urls_input.clear()

    def add_to_queue(self, urls):
        """Fungsi inti untuk menambahkan URL ke antrean dan memulai pengambilan metadata."""
        for url in urls:
            row_position = self.queue_table.rowCount()
            self.queue_table.insertRow(row_position)
            self.queue_table.setRowHeight(row_position, 95) # Tinggi baris untuk thumbnail

            # Tambahkan placeholder saat metadata diambil
            self.queue_table.setItem(row_position, 1, QTableWidgetItem(url))
            self.queue_table.setItem(row_position, 4, QTableWidgetItem(self._t("status_fetching", default="Fetching...")))
            
            # Data sementara untuk job
            job_data = {
                "url": url,
                "format": self.format_combo.currentText(),
                "resolution": self.res_combo.currentText() if self.format_combo.currentIndex() == 0 else "N/A",
                "status": "Queued",
                "row": row_position
            }
            self.download_queue_data.append(job_data)
            
            self.fetch_metadata_for_row(url, row_position)

    def fetch_metadata_for_row(self, url, row):
        """Membuat worker terpisah untuk mengambil metadata satu URL."""
        thread = QThread()
        worker = MetadataWorker()
        worker.moveToThread(thread)

        thread.started.connect(lambda: worker.run(url, self.get_yt_dlp_path(), row))
        worker.finished.connect(self.update_row_with_metadata)
        worker.error.connect(self.on_metadata_error)
        
        # Membersihkan setelah selesai
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        
        thread.start()
        self.meta_threads.append((thread, worker)) # Simpan referensi

    def update_row_with_metadata(self, info, row):
        """Memperbarui baris tabel dengan metadata yang sudah didapat."""
        # Update data di list utama
        job = next((item for item in self.download_queue_data if item['row'] == row), None)
        if not job: return
        job['title'] = info['title']
        
        # Tampilkan thumbnail
        thumb_label = QLabel()
        thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if info["thumbnail_data"]:
            pixmap = QPixmap()
            pixmap.loadFromData(info["thumbnail_data"])
            thumb_label.setPixmap(pixmap.scaled(160, 90, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            thumb_label.setText("No Thumb")
        self.queue_table.setCellWidget(row, 0, thumb_label)
        
        # Tampilkan Judul dan Detail
        self.queue_table.setItem(row, 1, QTableWidgetItem(info["title"]))
        details = f"{job['format']} | {job['resolution']}"
        self.queue_table.setItem(row, 2, QTableWidgetItem(details))
        
        # Tambahkan Progress Bar
        progress_bar = QProgressBar()
        progress_bar.setValue(0)
        progress_bar.setTextVisible(True)
        self.queue_table.setCellWidget(row, 3, progress_bar)
        
        # Update status
        self.queue_table.setItem(row, 4, QTableWidgetItem(self._t("status_queued", default="Queued")))

    def on_metadata_error(self, error_msg, row):
        """Menangani jika gagal mengambil metadata."""
        self.queue_table.setItem(row, 1, QTableWidgetItem(f"Failed: {error_msg}"))
        self.queue_table.setItem(row, 4, QTableWidgetItem(self._t("status_error", default="Error")))
        job = next((item for item in self.download_queue_data if item['row'] == row), None)
        if job: job['status'] = "Error"
        
    def process_queue(self):
        """Memulai atau menghentikan proses unduhan."""
        if self.is_downloading:
            # Logika untuk menghentikan unduhan (implementasi lebih lanjut)
            pass
        else:
            self.is_downloading = True
            self.start_queue_button.setText(self._t("stop_download", default="Stop Download"))
            self.start_queue_button.setIcon(QIcon("icons/stop.png"))
            self.start_next_in_queue()

    def start_next_in_queue(self):
        """Mencari item berikutnya dalam antrean dan memulai unduhan."""
        next_job_index = -1
        for i, job in enumerate(self.download_queue_data):
            if job["status"] == "Queued":
                next_job_index = i
                break

        if next_job_index == -1:
            self.is_downloading = False
            self.start_queue_button.setText(self._t("start_download", default="Start Download"))
            self.start_queue_button.setIcon(QIcon("icons/download.png"))
            if self.shutdown_checkbox.isChecked():
                self.initiate_shutdown()
            return

        self.current_download_index = next_job_index
        job = self.download_queue_data[self.current_download_index]
        job["status"] = "Downloading"
        
        # Bangun perintah yt-dlp
        yt_dlp_path = self.get_yt_dlp_path()
        base_cmd = [yt_dlp_path, "--no-part", "--no-continue", "--fragment-retries", str(CONFIG["fragment_retries"]), "--concurrent-fragments", str(CONFIG["concurrent_fragments"])]
        
        if job["format"] == "Audio (MP3)":
            output_template = os.path.join(self.output_folder, "%(title)s.%(ext)s")
            cmd = base_cmd + ["-f", "bestaudio/best", "--extract-audio", "--audio-format", "mp3", "--audio-quality", "0", "-o", output_template, job["url"]]
        else: # Video
            res = job["resolution"]
            format_str = CONFIG["format_map"].get(res, "best")
            output_template = os.path.join(self.output_folder, f"%(title)s_{res}.%(ext)s")
            cmd = base_cmd + ["--merge-output-format", CONFIG["merge_format"], "--format", format_str, "-o", output_template, job["url"]]

        # Siapkan dan mulai thread unduhan
        self.download_thread = QThread()
        self.download_worker = DownloadWorker(LANGUAGES.get(self.current_lang, {}))
        self.download_worker.moveToThread(self.download_thread)
        
        self.download_worker.progress.connect(self.update_progress_in_table)
        self.download_worker.update_status.connect(self.update_status_in_table)
        self.download_worker.finished.connect(self.on_download_finished)

        self.download_thread.started.connect(lambda: self.download_worker.run(cmd, job['row']))
        self.download_thread.start()

    def on_download_finished(self, row, status, message):
        job = next((item for item in self.download_queue_data if item['row'] == row), None)
        if not job: return

        if status == "success":
            job["status"] = "Completed"
            self.update_status_in_table(row, self._t("status_completed", default="Completed"))
        else:
            job["status"] = "Error"
            self.update_status_in_table(row, self._t("status_error", default="Error"))

        self.download_thread.quit()
        self.download_thread.wait()
        self.start_next_in_queue()

    def update_progress_in_table(self, row, percentage):
        progress_bar = self.queue_table.cellWidget(row, 3)
        if isinstance(progress_bar, QProgressBar):
            progress_bar.setValue(percentage)

    def update_status_in_table(self, row, status_text):
        status_item = self.queue_table.item(row, 4)
        if status_item:
            status_item.setText(status_text)
        else:
            self.queue_table.setItem(row, 4, QTableWidgetItem(status_text))

    def toggle_resolution_box(self):
        is_audio = self.format_combo.currentText() == "Audio (MP3)"
        self.res_combo.setEnabled(not is_audio)
        self.res_label.setEnabled(not is_audio)
        
    def open_result_folder(self):
        path = os.path.abspath(self.output_folder)
        try:
            if platform.system() == "Windows": os.startfile(path)
            elif platform.system() == "Darwin": subprocess.Popen(["open", path])
            else: subprocess.Popen(["xdg-open", path])
        except Exception:
            pass
            
    def initiate_shutdown(self):
        system = platform.system()
        try:
            if system == "Windows": os.system("shutdown /s /t 1")
            else: os.system("sudo shutdown -h now")
        except Exception: pass

    def apply_stylesheet(self):
        """Menerapkan tema gelap pada aplikasi."""
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #f0f0f0;
                font-family: Segoe UI;
                font-size: 10pt;
            }
            QGroupBox {
                border: 1px solid #4a4a4a;
                border-radius: 5px;
                margin-top: 1ex;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 3px;
            }
            QLineEdit, QPlainTextEdit, QComboBox {
                background-color: #3c3f41;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton {
                background-color: #0078d7;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:pressed {
                background-color: #003c6a;
            }
            QTableWidget {
                gridline-color: #4a4a4a;
                background-color: #3c3f41;
            }
            QHeaderView::section {
                background-color: #2b2b2b;
                padding: 4px;
                border: 1px solid #4a4a4a;
                font-weight: bold;
            }
            QProgressBar {
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                text-align: center;
                color: #f0f0f0;
            }
            QProgressBar::chunk {
                background-color: #0078d7;
                width: 10px;
                margin: 0.5px;
            }
        """)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ShrineDownloader()
    window.show()
    sys.exit(app.exec())