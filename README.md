# Arsitektur Microservice: Python (Flask + Gunicorn), MySQL, PostgreSQL, Nginx, & Docker

Sistem akademik sederhana berbasis arsitektur *microservice* yang terdiri dari dua layanan utama (Mahasiswa Service dan Mata Kuliah Service), Nginx API Gateway, serta menggunakan dua jenis database yang berbeda (*Database-per-Service*).

---

## 🛠️ Prasyarat Sistem
Sebelum menjalankan proyek ini, pastikan komputer Anda telah terinstal:
* [Git](https://git-scm.com/)
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Pastikan layanan/daemon Docker sudah aktif dan berjalan).

---

## 🚀 Cara Menjalankan Program

### 1. Clone Repository
Buka terminal/PowerShell, lalu clone repository ini ke komputer lokal Anda:
```powershell
git clone https://github.com/DaffaMaulan0/praktikum-microservice.git
cd praktikum-microservice
```

### 2. Jalankan dengan Docker Compose

#### 🔹 Solusi Utama (Jika perintah `docker` sudah dikenali sistem):
```powershell
docker compose up --build
```

#### ⚠️ Solusi Jika Muncul Error `"docker is not recognized..."`:
Jika terminal Anda memunculkan error bahwa perintah `docker` tidak dikenali, hal ini disebabkan oleh jalur instalasi (*PATH*) Docker yang belum terdaftar di komputer tersebut. Anda dapat mengatasinya dengan menggunakan **Path Absolut** berikut:

* **Jika Docker terinstal di Program Files:**
  ```powershell
  & "C:\Program Files\Docker\Docker\resources\bin\docker.exe" compose up --build
  ```

* **Jika Docker terinstal di folder AppData:**
  ```powershell
  & "$env:LOCALAPPDATA\Programs\DockerDesktop\resources\bin\docker.exe" compose up --build
  ```

> *Catatan: Docker Compose telah dikonfigurasi dengan `healthcheck` otomatis. Layanan backend hanya akan berjalan setelah database siap sepenuhnya menerima koneksi.*

---

## 🌐 Akses & Pengujian Sistem

Sistem menerapkan prinsip **Single Entry Point** di mana semua akses klien diarahkan melalui **Nginx API Gateway pada port 8080** (port internal backend terlindungi di dalam Docker network):

* **Dashboard Web Akademik:** `http://localhost:8080`
* **Health Check Gateway:** `http://localhost:8080/health`
* **Mahasiswa Service (API):**
  * `GET /mahasiswa` - Menampilkan seluruh data mahasiswa
  * `POST /mahasiswa` - Mendaftarkan mahasiswa baru
  * `GET /mahasiswa/<nim>` - Menampilkan data mahasiswa tertentu
  * `PUT /mahasiswa/<nim>` - Memperbarui data mahasiswa
  * `DELETE /mahasiswa/<nim>` - Menghapus data mahasiswa
  * `GET /mahasiswa/<nim>/matkul` - Menampilkan daftar KRS mahasiswa (*dioptimalkan via batch query*)
  * `POST /mahasiswa/<nim>/matkul` - Pengambilan mata kuliah (KRS)
  * `DELETE /mahasiswa/<nim>/matkul/<kode_mk>` - Pembatalan mata kuliah (KRS)
* **Mata Kuliah Service (API):**
  * `GET /matkul` - Menampilkan daftar mata kuliah
  * `POST /matkul` - Menambahkan mata kuliah baru
  * `POST /matkul/batch` - Query batch mata kuliah sekaligus (*mengeliminasi N+1 problem*)
  * `GET /matkul/<kode>` - Menampilkan detail mata kuliah
  * `PUT /matkul/<kode>` - Memperbarui mata kuliah
  * `DELETE /matkul/<kode>` - Menghapus mata kuliah (*otomatis membersihkan referensi KRS lintas service*)

---

## 🏗️ Peningkatan Arsitektur yang Diterapkan
1. **Keamanan Gateway (No Direct Port Exposure):** Port container `5001` dan `5002` tidak lagi dibuka ke host luar. Seluruh lalu lintas wajib melewati API Gateway.
2. **Production-Ready Web Server:** Menjalankan **Gunicorn WSGI** (multi-worker) menggantikan server pengembangan bawaan Flask.
3. **Healthcheck & Startup Synchronization:** Menerapkan `healthcheck` native pada MySQL, PostgreSQL, dan Flask services sehingga bebas dari race condition saat booting awal.
4. **Optimasi N+1 REST Problem:** Pengambilan daftar KRS pada `mahasiswa-service` menggunakan endpoint batch `POST /matkul/batch` dengan satu kali HTTP call.
5. **Integritas Data Lintas Layanan:** Penghapusan mata kuliah di `matkul-service` secara otomatis mengomunikasikan pembersihan data KRS terkait di `mahasiswa-service`.

---

## 📦 Struktur Direktori Proyek

```text
praktikum-microservice/
├── docker-compose.yml           # Konfigurasi multi-container, healthcheck & network
├── gateway/
│   ├── Dockerfile               # Image Nginx + Dashboard
│   ├── default.conf             # Reverse proxy routing & proxy headers
│   └── dashboard/
│       └── index.html           # Web UI Dashboard Akademik
├── mahasiswa-service/
│   ├── Dockerfile               # Python 3.12 + Gunicorn
│   ├── requirements.txt         # Flask, Flask-SQLAlchemy, PyMySQL, Gunicorn, Requests
│   └── app.py                   # CRUD Mahasiswa, KRS, & Healthcheck (MySQL)
└── matkul-service/
    ├── Dockerfile               # Python 3.12 + Gunicorn
    ├── requirements.txt         # Flask, Flask-SQLAlchemy, Psycopg2, Gunicorn, Requests
    └── app.py                   # CRUD Matkul, Batch Query, & Healthcheck (PostgreSQL)
```

---

## 🛑 Menghentikan Layanan
Untuk menghentikan seluruh kontainer yang sedang berjalan, tekan **`Ctrl + C`** di terminal, atau jalankan:
```powershell
docker compose down
```
> *Gunakan `docker compose down -v` jika Anda ingin menghapus volume database dan memulai dari data kosong.*
