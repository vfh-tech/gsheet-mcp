# Strategi Deployment & Distribusi MCP

Proyek ini dirancang agar bisa digunakan oleh banyak orang secara aman dengan memanfaatkan ekosistem `uv`.

## 1. Model Distribusi
Proyek ini menggunakan model **Distributed Local Execution**. Kode sumber di-hosting secara terpusat di GitHub, namun eksekusi dilakukan di lingkungan lokal masing-masing pengguna.

## 2. Cara Kerja untuk Pengguna Lain
Orang lain dapat menggunakan MCP server ini dengan langkah-langkah berikut:

1. **Persiapan Kredensial**: 
   - Pengguna membuat Service Account di Google Cloud Console mereka sendiri.
   - Pengguna mengunduh file `service-account-key.json` dan menyimpannya di komputer mereka (misalnya di `C:\keys\my-key.json`).

2. **Menjalankan via UVX**:
   Pengguna cukup menjalankan perintah berikut di terminal mereka:
   ```bash
   uvx --from git+https://github.com/[USERNAME]/sheet-mcp sheet-mcp
   ```

3. **Konfigurasi Environment**:
   Agar server bisa menemukan kunci lokal tersebut, pengguna harus menyertakan environment variable:
   ```bash
   # Contoh di Windows PowerShell
   $env:SERVICE_ACCOUNT_FILE="D:\keys\my-key.json"
   $env:SPREADSHEET_ID="your_spreadsheet_id_here"
   uvx --from git+https://github.com/[USERNAME]/sheet-mcp sheet-mcp
   ```

## 3. Keuntungan Strategi Ini
- **Keamanan**: `service-account-key.json` tidak pernah keluar dari komputer pengguna.
- **Kemudahan**: Tidak perlu melakukan `git clone` atau mengelola virtual environment secara manual.
- **Update Otomatis**: `uvx` akan selalu mengambil versi terbaru dari kode di GitHub (atau sesuai tag yang ditentukan).

## 4. Persyaratan Sistem
- Python 3.13+
- [uv](https://github.com/astral-sh/uv) terinstal di komputer pengguna.