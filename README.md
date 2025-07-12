# ScanSkin - Skin Type Detection App

Aplikasi web untuk deteksi jenis kulit menggunakan Vision Transformer (ViT) model.

## 🚀 Deployment ke Render

### Prerequisites
- Model file (`vit_model.pth`) harus ada di folder `models/`
- Repository harus sudah di-push ke GitHub

### Langkah-langkah Deployment:

1. **Persiapan Repository**
   ```bash
   git add .
   git commit -m "Add Docker configuration for deployment"
   git push origin main
   ```

2. **Deploy ke Render**
   - Login ke [Render](https://render.com/)
   - Klik "New" → "Web Service"
   - Connect repository GitHub Anda
   - Pilih repository `projek-skripsi-web`
   - Render akan otomatis mendeteksi `render.yaml` dan menggunakan konfigurasi Docker

3. **Environment Variables** (Opsional)
   - `SECRET_KEY`: Akan di-generate otomatis oleh Render
   - `FLASK_ENV`: Sudah diset ke `production`
   - `PORT`: Sudah diset ke `5000`

## 🐳 Local Development dengan Docker

### Menjalankan dengan Docker Compose:
```bash
# Build dan jalankan
docker-compose up --build

# Jalankan di background
docker-compose up -d

# Stop services
docker-compose down
```

### Menjalankan dengan Docker biasa:
```bash
# Build image
docker build -t scanskin-app .

# Run container
docker run -p 5000:5000 \
  -v $(pwd)/app/static/uploads:/app/app/static/uploads \
  -v $(pwd)/models:/app/models \
  -e FLASK_ENV=development \
  scanskin-app
```

## 📁 Struktur Project

```
projek-skripsi-scanSkin/
├── app.py                 # Entry point aplikasi
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Local development
├── render.yaml           # Render deployment config
├── requirements.txt      # Python dependencies
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── routes/
│   ├── service/
│   ├── static/
│   └── templates/
├── models/
│   └── vit_model.pth     # Model file (required)
```

## 🔧 Konfigurasi

### Environment Variables
- `FLASK_ENV`: `development` atau `production`
- `SECRET_KEY`: Secret key untuk Flask session
- `PORT`: Port untuk aplikasi (default: 5000)

### Model Configuration
Aplikasi akan otomatis mencari file model dengan urutan:
1. `vit_model.pth`
2. `skin_type_model.pt`
3. `skin_type_model.pth`
4. `model.pt`
5. `model.pth`
6. `best_model.pt`
7. `best_model.pth`

## 🚨 Troubleshooting

### Model tidak ditemukan
- Pastikan file model ada di folder `models/`
- Periksa nama file sesuai dengan yang didukung
- Pastikan file model tidak corrupt

### Memory issues di Render
- Render free tier memiliki keterbatasan memory
- Pertimbangkan untuk menggunakan paid plan jika model terlalu besar

### Build gagal
- Periksa logs di Render dashboard
- Pastikan semua dependencies ada di `requirements.txt`
- Pastikan model file tidak terlalu besar (< 500MB untuk free tier)

## 📝 Notes

- Render free tier memiliki keterbatasan:
  - 512MB RAM
  - 1GB storage
  - Aplikasi akan sleep setelah 15 menit tidak digunakan
- Untuk production, disarankan menggunakan paid plan untuk performa yang lebih baik
