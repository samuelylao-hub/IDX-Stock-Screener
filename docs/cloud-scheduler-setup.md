# Menyiapkan scheduler cloud gratis

Workflow GitHub Actions tersedia untuk:
- Market screener: Senin–Jumat pukul 18.00 WIB (11.00 UTC).
- News ingestion: Senin–Jumat pukul 19.10 WIB (12.10 UTC).
- Keduanya juga dapat dijalankan manual dari tab **Actions**.

## Prasyarat penting

Workflow **belum dapat berjalan penuh hanya dengan mengaktifkan GitHub Actions**. PostgreSQL lokal di Docker tidak bisa dijangkau oleh runner cloud saat laptop mati. Siapkan PostgreSQL yang dapat diakses dari internet melalui koneksi TLS (misalnya database managed dengan paket gratis), lalu pindahkan skema dan data yang diperlukan dari PostgreSQL lokal. Jangan membuka port PostgreSQL laptop ke internet.

## GitHub Actions Secrets

Di repository, buka **Settings → Secrets and variables → Actions → New repository secret**, lalu buat:

- `DATABASE_HOST`: hostname database cloud, tanpa `https://`.
- `DATABASE_PORT`: port database (biasanya `5432`).
- `DATABASE_NAME`: nama database.
- `DATABASE_USER`: username database.
- `DATABASE_PASSWORD`: password database.
- `INDEX_ALPHA_API_KEY`: API key Index Alpha.
- `TELEGRAM_BOT_TOKEN`: token bot Telegram.
- `TELEGRAM_CHAT_ID`: chat ID tujuan notifikasi.

Jangan menaruh nilai rahasia dalam file workflow, commit, atau issue. Repository ini bersifat publik.

## Mengaktifkan dan menguji

1. Siapkan database cloud dan migrasikan data/schema yang dibutuhkan aplikasi. Pastikan `stocks`, kalender pasar, tabel screener, job log, flow, dan berita tersedia.
2. Tambahkan semua secrets di atas ke repository.
3. Setelah pull request ini digabung ke branch default `main`, buka tab **Actions**.
4. Jalankan **IDX Market Screener** secara manual sekali, lalu **IDX News Ingestion**. Pastikan keduanya sukses dan laporan Telegram diterima.
5. Setelah validasi berhasil, jadwal otomatis akan berjalan sesuai waktu di atas.

Workflow memeriksa secrets terlebih dahulu agar tidak memanggil API ketika konfigurasi belum lengkap. Jika job gagal setelah konfigurasi tersedia, workflow mencoba mengirim pemberitahuan kegagalan melalui Telegram.

## Batasan

- GitHub Actions adalah scheduler cloud, bukan proses server yang hidup terus-menerus. Ia menjalankan job sesuai jadwal; waktu mulai dapat terlambat karena antrean.
- Workflow ini tidak menjalankan scanner intraday setiap 5 menit. Continuous intraday memerlukan worker yang berjalan terus-menerus dan tidak dijamin gratis.
- Pemakaian tetap tunduk pada batas GitHub Actions, penyedia database, dan kuota Index Alpha.
