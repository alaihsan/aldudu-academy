# Aldudu Academy - Development Setup

## Quick Start (Windows)

### 1. Activate Virtual Environment
```bash
# From project root directory
venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
# Copy example env file
copy .env\ copy.example .env

# Edit .env with your configuration
# IMPORTANT: Generate a secure SECRET_KEY:
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### 4. Setup Database
```bash
# Run migrations
flask db upgrade

# Initialize database with seed data
flask init-db
```

### 5. Run Application
```bash
# Option 1: Using Flask (development)
flask run

# Option 2: Using Python directly
python run.py
```

### 6. Start Celery Worker (Optional - for Rasch analysis)
```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Celery worker
venv\Scripts\activate
python run_worker.py
```

## Access the Application

- **URL**: http://localhost:5000
- **Teacher Login**: guru@aldudu.com / 123
- **Student Login**: murid@aldudu.com / 123

---

## Common Issues

### Environment Contamination
**Problem**: App menggunakan venv dari project lain

**Solution**: 
1. Pastikan venv di dalam folder project: `aldudu-academy/venv/`
2. Always activate venv before running: `venv\Scripts\activate`
3. Check which Python is being used: `where python`
4. Should point to: `C:\Users\iksan\dev\aldudu-academy\venv\Scripts\python.exe`

### SQLAlchemy Error: 'does not support object population'
**Problem**: Eager loading conflict with lazy='dynamic'

**Solution**: Already fixed by changing relationships to use `lazy='selectin'`

### Redis Not Running
**Problem**: Celery worker tidak bisa connect

**Solution**:
```bash
# Install Redis for Windows
# Download from: https://github.com/microsoftarchive/redis/releases
# Or use WSL: redis-server

# Check if Redis is running
redis-cli ping
# Should return: PONG
```

---

## Project Structure

```
aldudu-academy/
├── app/                      # Application code
│   ├── blueprints/          # Flask blueprints (routes)
│   ├── models/              # Database models
│   ├── services/            # Business logic
│   ├── templates/           # Jinja2 templates
│   └── static/              # CSS, JS, images
├── migrations/               # Database migrations
├── tests/                    # Unit tests
├── venv/                     # Virtual environment (DO NOT COMMIT)
├── .env                      # Environment variables (DO NOT COMMIT)
├── run.py                    # Development server
└── run_worker.py            # Celery worker
```

---

## Running Tests

```bash
# Activate venv first
venv\Scripts\activate

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v
```

---

## Database Commands

```bash
# Create migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Rollback migration
flask db downgrade -1

# Check migration status
flask db check
```

---

## Production Deployment

See `deploy/` folder for Docker Compose configuration.

```bash
# Build and run with Docker
docker compose -f deploy/docker-compose.prod.yml up -d --build

# Run migrations in container
docker compose -f deploy/docker-compose.prod.yml exec web flask db upgrade
```
