# YouTube Spam Comment Remover

Sebuah alat bertenaga AI untuk mendeteksi dan menghapus komentar spam dari video YouTube menggunakan Gemini AI, dibangun dengan backend Flask dan frontend Next.js.

## 🚀 Memulai Cepat

1. **Clone repository**:
   ```bash
   git clone <repository-url>
   cd judolslayer
   ```

2. **Setup backend** (lihat [Setup Backend](#setup-backend))
3. **Setup frontend** (lihat [Setup Frontend](#setup-frontend))
4. **Konfigurasi API keys** di file environment
5. **Jalankan kedua server** dan kunjungi `http://localhost:3000`

## Fitur

- 🤖 **Deteksi Bertenaga AI**: Menggunakan Gemini AI Google (gemini-2.0-flash) untuk deteksi spam yang cerdas
- 🎯 **Filter Lanjutan**: Mendeteksi judi, penipuan, promosi, dan jenis spam lainnya
- 🔍 **Mode Dry Run**: Preview apa yang akan dihapus sebelum mengambil tindakan
- 📊 **Analitik Detail**: Lihat statistik dan analisis komprehensif
- 🚀 **UI Modern**: Interface yang indah dan responsif dibangun dengan Next.js dan Tailwind CSS
- 🔄 **Pemrosesan Batch**: Proses beberapa video sekaligus
- 📤 **Ekspor Hasil**: Download hasil analisis sebagai JSON atau CSV
- ⚡ **Pemrosesan Real-time**: Update langsung selama pemrosesan

## Perbandingan Mode Operasi

| Fitur | Mode Analisis/Dry Run | Mode Hapus |
|-------|----------------------|------------|
| **Tujuan** | Preview dan analisis | Hapus spam aktual |
| **Keamanan** | ✅ Aman, tidak ada perubahan | ⚠️ Permanen, tidak bisa dibatalkan |
| **Output** | Laporan deteksi spam | Komentar spam dihapus |
| **Rekomendasi** | Selalu gunakan dulu | Gunakan setelah review |
| **Risiko** | Tidak ada risiko | Risiko hapus komentar valid |
| **Fungsi** | Identifikasi dan statistik | Moderasi aktual |
| **Reversible** | ✅ Ya (tidak ada aksi) | ❌ Tidak (penghapusan permanen) |
| **Ideal untuk** | Testing, review, analisis | Pembersihan final |

## Arsitektur

### Backend (Flask + LangGraph)
- **Flask**: Server API RESTful
- **LangGraph**: Orkestrasi workflow untuk logika deteksi spam yang kompleks
- **Gemini AI**: Model bahasa canggih untuk klasifikasi spam
- **YouTube Data API**: Mengambil dan mengelola komentar
- **TensorFlow/PyTorch**: Kemampuan ML tambahan (dapat diperluas)

### Frontend (Next.js)
- **Next.js 14**: Framework React dengan App Router
- **TypeScript**: Pengembangan yang type-safe
- **Tailwind CSS**: Styling utility-first
- **React Query**: Pengambilan data dan caching
- **React Hook Form**: Manajemen form dengan validasi
- **Heroicons**: Ikon yang indah

## Prasyarat

- **Python 3.8+** dengan pip
- **Node.js 18+** dengan npm
- **YouTube Data API v3 key** dari [Google Cloud Console](https://console.cloud.google.com/)
- **Google AI (Gemini) API key** dari [Google AI Studio](https://makersuite.google.com/)
- **Git** untuk version control

### Mendapatkan API Keys

1. **YouTube Data API v3**:
   - Kunjungi [Google Cloud Console](https://console.cloud.google.com/)
   - Buat project baru atau pilih yang sudah ada
   - Aktifkan YouTube Data API v3
   - Buat credentials (API key)
   - Batasi key untuk YouTube Data API v3 demi keamanan

2. **Google AI (Gemini) API**:
   - Kunjungi [Google AI Studio](https://makersuite.google.com/)
   - Masuk dengan akun Google Anda
   - Buat API key baru
   - Salin key untuk digunakan di file environment Anda

## Instalasi

### Setup Backend

1. Navigasi ke direktori backend:
```bash
cd backend
```

2. Buat virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Di Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Buat file environment:
```bash
cp .env.example .env
```

5. Konfigurasi file `.env` Anda:
```env
# API Keys (Required)
YOUTUBE_API_KEY=your_youtube_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=generated_secure_secret_key_here

# CORS Settings
CORS_ORIGINS=http://localhost:3000

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60

# Logging
LOG_LEVEL=INFO
```

**Penting**: 
- Ganti `your_youtube_api_key_here` dengan YouTube Data API v3 key Anda yang sebenarnya
- Ganti `your_gemini_api_key_here` dengan Google AI (Gemini) API key Anda yang sebenarnya
- SECRET_KEY telah dibuat secara otomatis untuk keamanan
- Jangan pernah commit file `.env` Anda ke version control

6. Jalankan aplikasi Flask:
```bash
python app.py
```

Backend akan tersedia di `http://localhost:5000`

### Setup Frontend

1. Navigasi ke direktori frontend:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Buat file environment:
```bash
cp .env.local.example .env.local
```

4. Konfigurasi file `.env.local` Anda:
```env
NEXT_PUBLIC_API_URL=http://localhost:5000
```

5. Jalankan development server:
```bash
npm run dev
```

Frontend akan tersedia di `http://localhost:3000`

## API Endpoints

### Backend API

- `GET /api/health` - Health check
- `POST /api/process-video` - Proses video untuk deteksi spam
- `POST /api/analyze-comment` - Analisis satu komentar
- `POST /api/video-info` - Dapatkan informasi video
- `POST /api/batch-process` - Proses beberapa video

**Catatan**: Semua API keys sekarang dikonfigurasi melalui environment variables untuk keamanan yang lebih baik. Tidak perlu menyertakannya dalam request API.

### Contoh Request

#### Proses Video untuk Deteksi Spam
```bash
curl -X POST http://localhost:5000/api/process-video \
  -H "Content-Type: application/json" \
  -d '{
    "video_id": "dQw4w9WgXcQ",
    "max_results": 100,
    "dry_run": true
  }'
```

#### Analisis Satu Komentar
```bash
curl -X POST http://localhost:5000/api/analyze-comment \
  -H "Content-Type: application/json" \
  -d '{
    "comment_text": "Check out my crypto trading bot!"
  }'
```

## Penggunaan

1. **Jalankan Aplikasi**:
   - Pastikan server backend dan frontend berjalan
   - Buka `http://localhost:3000` di browser Anda

2. **Masukkan Informasi Video**:
   - Paste YouTube video ID atau URL lengkap
   - Konfigurasi pengaturan deteksi (API keys dimuat otomatis dari environment)
   - Sesuaikan opsi lanjutan jika diperlukan

3. **Jalankan Analisis**:
   - **Direkomendasikan**: Gunakan "Dry Run" dulu untuk preview hasil tanpa membuat perubahan
   - Review analisis dan statistik
   - Jika puas, nonaktifkan "Dry Run" dan klik "Remove Spam" untuk menghapus komentar spam yang terdeteksi

4. **Review Hasil**:
   - Lihat statistik detail dan skor confidence
   - Filter komentar berdasarkan tipe (All, Spam, Clean)
   - Urutkan berdasarkan confidence, tanggal, atau level risiko
   - Ekspor hasil untuk analisis lebih lanjut

### ⚠️ Catatan Penting

- **Selalu test dengan Dry Run dulu** untuk menghindari penghapusan komentar yang sah secara tidak sengaja
- **Penghapusan spam bersifat permanen** - komentar yang dihapus tidak dapat dipulihkan
- **Rate limits berlaku** - YouTube API memiliki kuota harian
- **Review hasil dengan hati-hati** - deteksi AI mungkin memiliki false positives

## Konfigurasi

### Pengaturan Deteksi Spam

- **Confidence Threshold**: Level confidence minimum untuk klasifikasi spam (0.0-1.0)
- **Risk Levels**: Kategorisasi risiko Tinggi, Sedang, Rendah
- **Spam Types**: Judi, Penipuan, Promosi, Ofensif, dll.
- **Dry Run**: Mode preview tanpa penghapusan aktual

### Opsi Lanjutan

- **Max Comments**: Batasi jumlah komentar yang diproses
- **Include Replies**: Proses balasan komentar
- **Custom Patterns**: Tambahkan pola deteksi spam kustom
- **Batch Processing**: Proses beberapa video secara bersamaan

## Development

### Backend Development

```bash
# Jalankan dengan auto-reload
python app.py

# Jalankan tests (jika file test ada)
python -m pytest tests/

# Format code (install tools dulu: pip install black flake8)
black .
flake8 .
```

### Frontend Development

```bash
# Development server
npm run dev

# Build untuk production
npm run build

# Jalankan production server
npm start

# Lint code
npm run lint

# Type check
npm run type-check
```

## Deployment

### Backend (Flask)

1. **Menggunakan Gunicorn**:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

2. **Menggunakan Docker**:
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

### Frontend (Next.js)

1. **Static Export**:
```bash
npm run build
npm run export
```

2. **Vercel Deployment**:
```bash
npm install -g vercel
vercel
```

## Pertimbangan Keamanan

- **API Keys**: 
  - Semua API keys dikelola melalui environment variables
  - Jangan pernah commit file `.env` ke version control
  - Gunakan `.env.example` sebagai template untuk variabel yang diperlukan
  - `credentials.json` secara otomatis diabaikan oleh Git
- **Secret Key**: Generate Flask secret key yang aman untuk production
- **Rate Limiting**: Implementasikan rate limiting yang tepat untuk production
- **CORS**: Konfigurasi CORS dengan benar untuk domain Anda
- **Input Validation**: Semua input divalidasi dan disanitasi
- **Error Handling**: Error handling dan logging yang komprehensif
- **Git Security**: 
  - File `.gitignore` yang komprehensif melindungi data sensitif
  - OAuth credentials dan API keys dikecualikan dari version control
  - Jika Anda tidak sengaja commit file sensitif, hapus dari Git history

## Kontribusi

1. Fork repository
2. Buat feature branch
3. Buat perubahan Anda
4. Tambahkan tests jika diperlukan
5. Submit pull request

## Lisensi

MIT License - lihat file LICENSE untuk detail

## Support

Untuk issues dan pertanyaan:
- Buat issue di GitHub
- Periksa dokumentasi
- Review contoh API

## Troubleshooting

### Masalah Umum

1. **Error "API key not found"**:
   - Pastikan file `.env` ada di direktori backend
   - Periksa bahwa API keys sudah diset dengan benar di environment variables
   - Restart server backend setelah mengubah environment variables

2. **Error "Video not found"**:
   - Verifikasi YouTube video ID atau URL sudah benar
   - Pastikan video bersifat public dan komentar diaktifkan
   - Periksa apakah video ada dan dapat diakses

3. **CORS errors**:
   - Pastikan backend berjalan di port 5000
   - Periksa pengaturan CORS_ORIGINS di backend `.env`
   - Verifikasi frontend mengakses URL backend yang benar

4. **Rate limit exceeded**:
   - YouTube API memiliki kuota harian
   - Tunggu reset kuota atau minta peningkatan kuota
   - Kurangi jumlah komentar yang diproses per request

### Mendapatkan Bantuan

- Periksa browser console untuk pesan error
- Review backend logs untuk informasi error yang detail
- Pastikan semua dependencies terinstall dengan benar
- Verifikasi API keys memiliki permissions yang tepat

## Acknowledgments

- Google AI untuk Gemini API
- YouTube Data API
- LangGraph untuk workflow orchestration
- Komunitas Next.js dan React
- Tailwind CSS untuk styling
- Komunitas open source untuk tools dan libraries