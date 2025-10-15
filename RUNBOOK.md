RUNBOOK — Aldudu Academy
========================

Tujuan
------
Panduan langkah demi langkah untuk men-deploy aplikasi Aldudu Academy ke server produksi, serta operasi harian (start/stop/restart), backup, rollback, dan troubleshooting.

Prasyarat
---------
- Server Linux (Ubuntu/Debian) atau macOS; panduan ini menggunakan Ubuntu/Debian untuk contoh systemd.
- Akses SSH ke server dengan user yang memiliki sudo.
- Domain DNS A record menunjuk ke IP server (untuk TLS).
- Docker (opsional) atau Python 3.9+ dan virtualenv.
- PostgreSQL (managed or local) untuk production DB.
- Repo sudah di-clone ke server, path contoh: `/srv/aldudu-academy`.

File penting di repo
--------------------
- `deploy/Dockerfile` — Docker image untuk production.
- `deploy/docker-compose.prod.yml` — Compose untuk web + Postgres lokal.
- `deploy/nginx.conf` — contoh konfigurasi Nginx (templatizable).
- `deploy/aldudu.service` — contoh systemd service unit untuk Gunicorn.
- `deploy/provision_nginx.sh` — skrip untuk meng-install nginx + certbot dan meng-enable site.
- `deploy/run_local_docker.sh` — helper untuk build & run compose lokal.
- `scripts/migrate_with_alembic.py` — jalankan alembic upgrade lalu copy data dari SQLite → Postgres.

Checklist pre-deploy
--------------------
1. Pastikan backup tersedia (DB snapshot / pg_dump).
2. Pastikan `FLASK_SECRET_KEY` disimpan di secret manager / env (jangan di-commit).
3. Pastikan `DATABASE_URL` mengarah ke Postgres production.
4. Pastikan migrasi Alembic sudah dibuat (`flask db migrate`) jika ada perubahan model.
5. Untuk docker: pastikan registry & credentials tersedia.

Langkah A — Deploy ke server (systemd + Gunicorn + Nginx)
---------------------------------------------------------
Asumsi: server Ubuntu, Anda melakukan SSH sebagai user dengan sudo.

1) Clone repo

```bash
sudo mkdir -p /srv/aldudu-academy
sudo chown $USER /srv/aldudu-academy
cd /srv
git clone https://github.com/<owner>/aldudu-academy.git aldudu-academy
cd /srv/aldudu-academy
```

2) Buat virtualenv dan install dependencies

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

3) Siapkan environment variables (example)

Buat `/srv/aldudu-academy/.env` atau set di systemd unit environment. Contoh:

```
DATABASE_URL=postgresql://<user>:<pass>@127.0.0.1:5432/aldudu_prod
FLASK_SECRET_KEY=<secure-random-string>
POSTGRES_USER=<user>
POSTGRES_PASSWORD=<pass>
POSTGRES_DB=aldudu_prod
```

4) Buat database dan user (jika lokal)

```bash
sudo -u postgres createuser -P <user>
sudo -u postgres createdb -O <user> aldudu_prod
```

5) Apply migrations

```bash
export DATABASE_URL="postgresql://<user>:<pass>@127.0.0.1:5432/aldudu_prod"
. .venv/bin/activate
FLASK_APP=app .venv/bin/python -m flask db upgrade
```

6) Configure systemd unit (example)

Edit `deploy/aldudu.service` agar paths dan env sesuai. Copy ke systemd:

```bash
sudo cp deploy/aldudu.service /etc/systemd/system/aldudu.service
sudo systemctl daemon-reload
sudo systemctl enable --now aldudu
sudo systemctl status aldudu
```

7) Configure Nginx + TLS

- Copy template and set domain/static path, atau gunakan `deploy/provision_nginx.sh`:

```bash
sudo ./deploy/provision_nginx.sh yourdomain.example.com /srv/aldudu-academy aldudu
```

- Script akan: install nginx/certbot, place site config, reload nginx, run certbot.

8) Validate

- Check app: `curl -I https://yourdomain.example.com/` → 200 OK
- Check logs: `sudo journalctl -u aldudu -f` and `sudo tail -f /var/log/nginx/error.log`


Langkah B — Deploy via Docker Compose (staging / simple production)
-----------------------------------------------------------------
1) Set `.env` from `deploy/.env.example` in repo root (contains DB credentials if you use compose local DB).
2) Build & run (local server with Docker installed):

```bash
./deploy/run_local_docker.sh
```

3) Stop & remove:

```bash
docker compose -f deploy/docker-compose.prod.yml down
```


DB migration & data migration (SQLite -> Postgres)
--------------------------------------------------
- To upgrade schema on target DB (target must be reachable by `DATABASE_URL`):

```bash
export DATABASE_URL="postgresql://<user>:<pass>@host:5432/db"
. .venv/bin/activate
FLASK_APP=app .venv/bin/python -m flask db upgrade
```

- To copy data from a SQLite export (local dev) to Postgres, use either:
  - `pgloader sqlite:///path/to/file.db postgresql://...` (recommended for large data), or
  - `scripts/migrate_with_alembic.py` (runs alembic upgrade then copies rows). Example:

```bash
export SQLITE_URL="sqlite:////path/to/aldudu_academy.db"
export POSTGRES_URL="postgresql://<user>:<pass>@host:5432/db"
. .venv/bin/activate
python scripts/migrate_with_alembic.py
```


Backups & Restore
-----------------
- Manual dump (Postgres):

```bash
pg_dump -U <user> -h <host> -F p -f backups/aldudu_$(date +%F).sql <db>
```

- Restore:

```bash
psql -U <user> -h <host> -d <db> -f backups/aldudu_YYYY-MM-DD.sql
```

- For nightly backups, schedule a cron job to run pg_dump and rotate files.


Rollback plan
-------------
1. Stop web service (`systemctl stop aldudu` or `docker compose down`).
2. Restore DB from last known-good backup:
   - `psql -U <user> -h <host> -d <db> -f backups/aldudu_last_good.sql`
3. Re-deploy previous image or checkout previous git tag and restart service.


Logs & monitoring
-----------------
- System logs: `journalctl -u aldudu -f`
- Gunicorn logs: wherever `--log-file` points (example: `/srv/aldudu-academy/gunicorn.log`)
- Nginx logs: `/var/log/nginx/access.log` and `/var/log/nginx/error.log`
- Add health endpoint `/healthz` (recommendation) for uptime checks.
- Consider setting up Prometheus + Grafana for metrics and Alertmanager for alerts.


Troubleshooting
---------------
- 500 errors: check `journalctl -u aldudu` and `gunicorn.log` for tracebacks.
- DB connection errors: confirm `DATABASE_URL` and that Postgres accepts remote connections (`pg_isready`), inspect firewall.
- TLS/Certbot errors: see `/var/log/letsencrypt` and ensure port 80 is reachable.
- Migration `UniqueViolation`: use idempotent migrations or `ON CONFLICT DO NOTHING` for copy scripts. We added idempotent behavior in `scripts/migrate_with_alembic.py`.


Maintenance tasks
-----------------
- Rotate logs (logrotate), prune old backups, and rotate secrets periodically.
- Upgrade dependencies in virtualenv and rebuild images regularly.
- Run tests and migrations in CI before deploying to production.


Emergency checklist (if site down)
----------------------------------
1. Check systemd: `sudo systemctl status aldudu` and `sudo journalctl -u aldudu -n 200`
2. Check Nginx: `sudo systemctl status nginx` and `sudo tail -n 200 /var/log/nginx/error.log`
3. Check DB: `pg_isready -h <host> -p 5432` and `psql -h <host> -U <user> -c "SELECT 1"`
4. If DB corrupted, restore last working backup.
5. If code bug, revert to previous git tag and restart service.


Appendix — useful commands
--------------------------
- Start/stop/restart systemd service:
  ```bash
  sudo systemctl start aldudu
  sudo systemctl stop aldudu
  sudo systemctl restart aldudu
  sudo systemctl status aldudu
  ```

- Logs:
  ```bash
  sudo journalctl -u aldudu -f
  sudo tail -f /var/log/nginx/error.log
  ```

- Run flask shell with env:
  ```bash
  export DATABASE_URL="postgresql://<user>:<pass>@127.0.0.1:5432/<db>"
  . .venv/bin/activate
  FLASK_APP=app .venv/bin/python -m flask shell
  ```

- Build & push docker image manually (if not using GHCR workflow):
  ```bash
  docker build -f deploy/Dockerfile -t myorg/aldudu-academy:latest .
  docker push myorg/aldudu-academy:latest
  ```

Jika Anda mau, saya bisa:
- Buat `deploy/provision_server.sh` untuk provisioning full server (systemd, venv, nginx, certbot) otomatis.
- Tambah `health` endpoint di aplikasi.
- Siapkan GitHub Actions CD yang deploy image ke server via SSH.

Sebutkan pilihan (contoh: "provision-script" atau "health-endpoint"), dan saya akan lanjutkan membuatnya.
