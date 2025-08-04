# 🛸 Macan Shrine Video Downloader – SilentStream Edition

Macan Shrine Video Downloader adalah aplikasi desktop ringan dan cepat untuk mengunduh video dari berbagai platform online menggunakan antarmuka modern berbasis **PyQt6**. Dibekali **engine `yt-dlp`**, multi-threaded UI, serta DNS Switching dan Shrine Log Panel, edisi **SilentStream** dirancang agar pengguna bisa fokus mendownload dengan alur yang senyap, efisien, dan powerful.

---

## 🚀 Fitur Unggulan

- 🎞️ **Support berbagai situs video** (YouTube, TikTok, Instagram, dsb)
- 🧠 **Preview metadata otomatis** (judul, resolusi, durasi, thumbnail)
- 📥 **Batch downloader** hingga 10 URL sekaligus
- 🧭 **Smart DNS Switcher** untuk bypass atau stabilisasi koneksi
- 📊 **Progress bar per file** dengan log status real-time
- 🧾 **Shrine Log Panel** — pantau aktivitas dan error dalam satu tempat
- 🧩 Terintegrasi dengan **Shrine Ecosystem** (Shrine Browser, Shrine Core Tools)
- 🌙 **Dark modern UI** dengan PyQt6 dan ikon SVG
- 🔧 **Custom config via JSON**

---

## 📸 Tampilan Antarmuka

<img width="605" height="543" alt="image" src="https://github.com/user-attachments/assets/f4e527f8-7ae9-442f-b38e-bf43d5eab3d2" />


---

## 📦 Cara Menggunakan

1. Pastikan Anda memiliki Python 3.10+ dan telah menginstal dependensi:
    ```bash
    pip install -r requirements.txt
    ```

2. Jalankan aplikasi:
    ```bash
    python main.py
    ```

3. Masukkan URL video atau gunakan **batch mode**
4. Klik tombol `Orbitkan Shrine` untuk memulai pengunduhan
5. Cek Shrine Log Panel untuk memantau proses
6. (Opsional) Aktifkan DNS resolver untuk koneksi yang lebih optimal

---

## ⚙️ Konfigurasi

Konfigurasi dapat diatur di file `downloader_config.json`.
```json
{
  "max_batch": 10,
  "output_format": "mp4",
  "download_folder": "ShrineDownloads/"
}

