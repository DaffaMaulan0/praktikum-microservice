# Arsitektur Microservice: Python (Flask), MySQL, PostgreSQL, Nginx, & Docker

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
Jika terminal memunculkan error bahwa perintah `docker` tidak dikenali, artinya letak instalasi Docker belum terdaftar di *PATH*. Lokasi instalasi Docker **berbeda-beda di setiap komputer** (ada yang di `C:\Program Files`, ada yang di `AppData`).

**✅ Cara paling aman: auto-deteksi (berfungsi di semua komputer)**
```powershell
$docker = Get-ChildItem "C:\Program Files\Docker","$env:LOCALAPPDATA\Programs\DockerDesktop" -Recurse -Filter docker.exe -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName
if ($docker) { & $docker compose up --build } else { Write-Host "Docker belum terinstal di komputer ini" }
```

**Cara alternatif: gunakan path yang sesuai dengan komputer Anda**

* Jika Docker terinstal di Program Files:
  ```powershell
  & "C:\Program Files\Docker\Docker\resources\bin\docker.exe" compose up --build
  ```

* Jika Docker terinstal di folder AppData:
  ```powershell
  & "$env:LOCALAPPDATA\Programs\DockerDesktop\resources\bin\docker.exe" compose up --build
  ```

> *Catatan: Tunggu sekitar 10–30 detik pada percobaan pertama hingga database MySQL dan PostgreSQL selesai melakukan inisialisasi awal.*

---

## 🌐 Akses & Pengujian Sistem

Setelah semua layanan aktif, pintu masuk utama sistem diatur melalui **Nginx API Gateway pada port 8080**:

* **Dashboard Web Akademik:**
  Buka browser dan akses: `http://localhost:8080`
* **Mahasiswa Service (API):** `http://localhost:8080/mahasiswa`
* **Mata Kuliah Service (API):** `http://localhost:8080/matkul`

---

## 📦 Struktur Direktori Proyek

```text
praktikum-microservice/
├── docker-compose.yml           # Konfigurasi multi-container & network
├── gateway/
│   ├── Dockerfile               # Konfigurasi image Nginx + Dashboard
│   ├── default.conf             # Aturan routing path API Gateway
│   └── dashboard/
│       └── index.html           # Antarmuka web (Dashboard Akademik)
├── mahasiswa-service/
│   ├── Dockerfile
│   ├── requirements.txt         # Flask, Flask-SQLAlchemy, PyMySQL, Requests
│   └── app.py                   # Logika CRUD Mahasiswa & KRS (MySQL)
└── matkul-service/
    ├── Dockerfile
    ├── requirements.txt         # Flask, Flask-SQLAlchemy, Psycopg2
    └── app.py                   # Logika CRUD Mata Kuliah (PostgreSQL)
```

---

## 🛑 Menghentikan Layanan
Untuk menghentikan seluruh kontainer yang sedang berjalan, tekan **`Ctrl + C`** di terminal, atau jalankan:
```powershell
docker compose down
```
> *Gunakan `docker compose down -v` jika Anda ingin menghapus volume database dan memulai dari data kosong.*
