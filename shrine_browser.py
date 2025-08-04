import sys, os, subprocess
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QToolBar,
    QCheckBox, QMessageBox, QProgressDialog
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
# Import spesifik untuk QWebEngineDownloadRequest
from PyQt6.QtWebEngineCore import QWebEngineDownloadRequest
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QIcon, QAction

class ShrineBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Danx Shrine Browser (PyQt6)")
        self.setWindowIcon(QIcon("browser.ico"))
        self.setGeometry(200, 100, 1024, 768)

        self.browser = QWebEngineView()
        self.setCentralWidget(self.browser)

        # 🔮 Download ritual handler
        self.profile = self.browser.page().profile()
        self.profile.downloadRequested.connect(self.handle_download)

        # 🚀 Chrome silent evoke
        self.invoke_chrome_silent()

        # ✨ SnapVid gate
        self.browser.setUrl(QUrl("https://snapvid.net/id/facebook-downloader"))

        # 🛠️ Toolbar nav
        bar = QToolBar("🔧 Navigasi")
        self.addToolBar(bar)
        bar.addAction(self.make_action("⬅️", self.browser.back))
        bar.addAction(self.make_action("➡️", self.browser.forward))
        bar.addAction(self.make_action("🔃", self.browser.reload))
        bar.addAction(self.make_action("🏠", lambda: self.browser.setUrl(QUrl("https://snapvid.net/id/facebook-downloader"))))

        proxy_toggle = QCheckBox("🛡️ Proxy")
        bar.addWidget(proxy_toggle)

    def make_action(self, text, slot):
        act = QAction(text, self)
        act.triggered.connect(slot)
        return act

    def invoke_chrome_silent(self):
        # Mencari path Chrome di Program Files
        chrome_path = os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe")
        if not os.path.exists(chrome_path):
            chrome_path = os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe")

        if os.path.exists(chrome_path):
            try:
                subprocess.Popen([
                    chrome_path,
                    "--new-window",
                    "--window-position=9999,9999", # Buka di luar layar
                    "https://facebook.com"
                ])
                print("🧿 Chrome dibuka (minimize), shrine siap evoke SnapVid.")
            except Exception as e:
                print("❌ Gagal panggil Chrome:", e)

    def handle_download(self, item: QWebEngineDownloadRequest):
        # 📂 Direktori shrine glyphs
        shrine_path = os.path.join(os.path.expanduser("~"), "shrine_video_downloader", "downloads")
        os.makedirs(shrine_path, exist_ok=True)
        # Di PyQt6, nama file disarankan diambil dari suggestedFileName()
        full_path = os.path.join(shrine_path, item.suggestedFileName())

        item.setDownloadDirectory(os.path.dirname(full_path))
        item.setDownloadFileName(os.path.basename(full_path))
        item.accept()

        # ⏳ Progress ritual
        progress = QProgressDialog("📥 Menarik artefact...", "❌ Batalkan", 0, 100, self)
        progress.setWindowTitle("⛩️ Shrine Progress")
        progress.setAutoClose(True)
        progress.setAutoReset(True)
        progress.show()

        def on_progress(received, total):
            if total > 0:
                percent = int((received / total) * 100)
                progress.setValue(percent)
                if percent >= 100:
                    # Menutup dialog dan membuka folder hanya sekali
                    if progress.isVisible():
                        progress.close()
                        os.startfile(shrine_path)  # 🎉 Open folder
                        QMessageBox.information(
                            self, "✅ Download Selesai",
                            f"Glyph artefact disimpan di:\n{full_path}"
                        )

        item.downloadProgress.connect(on_progress)

        print(f"⛩️ Download invoked ➤ {item.suggestedFileName()} → {full_path}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ShrineBrowser()
    window.show()
    # Migrasi exec_() ke exec()
    sys.exit(app.exec())