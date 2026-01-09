# Postman Collection - Best Time Post API

## File yang Tersedia

1. **Best_Time_Post_API.postman_collection.json** - Main collection dengan semua endpoints
2. **Development.postman_environment.json** - Environment untuk development
3. **QA.postman_environment.json** - Environment untuk QA testing

## Cara Import ke Postman

### Import Collection

1. Buka Postman
2. Klik **Import** (pojok kiri atas)
3. Drag & drop file `Best_Time_Post_API.postman_collection.json`
4. Klik **Import**

### Import Environment

1. Klik icon **Environments** (sidebar kiri)
2. Klik **Import**
3. Pilih file environment yang diinginkan:
   - `Development.postman_environment.json` untuk development
   - `QA.postman_environment.json` untuk QA
4. Klik **Import**
5. Pilih environment dari dropdown (pojok kanan atas)

## Endpoints yang Tersedia

### 1. Health Check
- **GET** `/api/v1/best-time/health`
- Mengecek status API, database, dan model

### 2. List Categories
- **GET** `/api/v1/best-time/categories`
- Mendapatkan daftar kategori yang tersedia

### 3. Predict Best Time
- **POST** `/api/v1/best-time/predict`
- Prediksi waktu terbaik untuk posting

**Request Body:**
```json
{
  "category": "Food & Culinary",
  "window_hours": 3,
  "top_k": 3,
  "days_ahead": 7
}
```

**Available Categories:**
- E-commerce & Shopping
- Education & Career
- Entertainment
- Fashion & Beauty
- Finance & Investment
- Food & Culinary
- Gaming & Esports
- Health & Fitness
- Technology & Gadgets
- Travel & Tourism

## Parameter Reference

| Parameter | Type | Required | Range | Default | Description |
|-----------|------|----------|-------|---------|-------------|
| category | string | Yes | - | - | Kategori konten |
| window_hours | integer | No | 1-12 | 3 | Durasi window posting (jam) |
| top_k | integer | No | 1-10 | 3 | Jumlah rekomendasi |
| days_ahead | integer | No | 1-14 | 7 | Jumlah hari prediksi |

## Test Automation

Setiap request sudah dilengkapi dengan automated tests:

- Status code validation
- Response structure validation
- Data type validation
- Business logic validation

### Menjalankan Tests

1. Pilih collection atau folder
2. Klik **Run** (atau tekan Ctrl+R)
3. Pilih environment
4. Klik **Run Best Time Post API**

## Environment Variables

| Variable | Development | QA | Description |
|----------|-------------|-----|-------------|
| base_url | http://localhost:8000 | http://localhost:8000 | Base URL API |
| db_host | localhost | localhost | Database host |
| db_port | 5433 | 5433 | Database port |

## Error Scenarios

Collection sudah include test cases untuk error handling:

1. **Invalid Category** - Test kategori yang tidak valid
2. **Invalid Window Hours** - Test validasi range parameter
3. **Missing Required Field** - Test missing field validation

## Tips untuk QA

1. **Run Collection** - Jalankan seluruh collection untuk regression testing
2. **Check Tests Tab** - Lihat hasil automated tests setelah request
3. **Use Environment** - Switch environment untuk test berbagai konfigurasi
4. **Save Responses** - Save responses sebagai examples untuk dokumentasi

## Troubleshooting

**Connection Error:**
- Pastikan Docker containers running: `docker-compose ps`
- Check API logs: `docker-compose logs api`

**Unhealthy Status:**
- Check model loaded: GET `/api/v1/best-time/health`
- Verify database: Check `database_connected` field

**Invalid Category:**
- Get valid categories: GET `/api/v1/best-time/categories`
- Use exact category name (case-sensitive)
