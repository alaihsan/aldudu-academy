# Aldudu Academy - Project Context

## Project Overview

**Aldudu Academy** is a Learning Management System (LMS) built from scratch using **Flask**. It provides a platform for teachers and students to manage online teaching-learning activities.

### Core Features

- **Academic Year Management**: Organize classes and content by academic years
- **Class Management (CRUD)**: Create, edit, and view classes with visual card layouts
- **Self-Enrollment System**: Students can join classes using unique class codes
- **User Roles**: Distinguishes between Teacher (Guru) and Student (Murid) roles with different dashboards
- **Gradebook & Assessment**:
  - Integrated gradebook with categories (Formatif, Sumatif, Sikap, Portfolio)
  - Auto-sync quiz & assignment grades
  - **Rasch Model** integration for modern assessment analysis (Item Response Theory)
  - Wright Map visualization, fit statistics, reliability indices
  - Bloom's Taxonomy mapping for cognitive levels
- **Clean UI**: Custom CSS (no framework) with Tailwind CSS for lightweight, focused UX

### Technology Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Flask 3.1.2, Flask-SQLAlchemy, Flask-Login, Flask-Mail, Flask-Caching, Flask-Migrate |
| **Task Queue** | Celery 5.6.2 + Redis 7.3.0 |
| **Database** | MySQL (PyMySQL) / PostgreSQL / SQLite (dev) |
| **Frontend** | Jinja2 templates, Custom CSS, Vanilla JavaScript |
| **Security** | Flask-Talisman (CSP), Flask-Limiter |
| **Testing** | pytest 7.4.2 |
| **Deployment** | Docker, Gunicorn, Nginx |

---

## Project Structure

```
aldudu-academy/
├── app/                          # Main application package
│   ├── __init__.py               # Application factory (create_app)
│   ├── blueprints/               # Flask blueprints (routes)
│   │   ├── auth.py               # Authentication routes
│   │   ├── courses.py            # Course management
│   │   ├── quiz.py               # Quiz functionality
│   │   ├── assignment.py         # Assignment handling
│   │   ├── gradebook.py          # Gradebook API
│   │   ├── rasch.py              # Rasch analysis API
│   │   ├── rasch_dashboard.py    # Rasch dashboard views
│   │   ├── admin.py              # Admin routes
│   │   ├── superadmin.py         # Superadmin routes
│   │   └── ...
│   ├── models/                   # SQLAlchemy models
│   │   ├── user.py               # User model with roles
│   │   ├── course.py             # Course model
│   │   ├── quiz.py               # Quiz & submission models
│   │   ├── assignment.py         # Assignment models
│   │   ├── gradebook.py          # Gradebook models
│   │   ├── rasch.py              # Rasch analysis models
│   │   └── ...
│   ├── services/                 # Business logic layer
│   │   └── gradebook_service.py  # Gradebook operations
│   ├── workers/                  # Celery task workers
│   │   └── rasch_worker.py       # Rasch analysis tasks
│   ├── templates/                # Jinja2 templates
│   ├── static/                   # CSS, JS, images
│   ├── celery_app.py             # Celery configuration
│   ├── config.py                 # Configuration classes
│   ├── extensions.py             # Flask extensions initialization
│   └── middleware.py             # Custom middleware
├── migrations/                   # Alembic migrations
│   ├── versions/                 # Migration scripts
│   └── alembic.ini
├── tests/                        # pytest tests
│   ├── conftest.py               # Test fixtures
│   ├── test_gradebook.py         # Gradebook tests
│   ├── test_discussion.py        # Discussion tests
│   └── ...
├── scripts/                      # Utility scripts
│   ├── run_rasch_migration.py    # Rasch migration
│   ├── seed_*.py                 # Data seeding scripts
│   └── ...
├── instance/                     # Instance-specific config (gitignored)
├── docs/                         # Documentation
├── laporan/                      # Reports (Indonesian)
├── deploy/                       # Deployment configs (Docker, systemd)
├── requirements.txt              # Python dependencies
├── run.py                        # Development server entry point
├── run_worker.py                 # Celery worker entry point
└── README.md                     # Main documentation
```

---

## Building and Running

### Development Setup

```bash
# 1. Clone and navigate to project
cd aldudu-academy

# 2. Create virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variables (copy from example)
cp .env\ copy.example .env
# Edit .env with your configuration

# 5. Initialize database
flask db upgrade
flask init-db

# 6. Start Redis (required for Celery)
redis-server

# 7. Start Celery worker (Terminal 2)
python run_worker.py

# 8. Start Flask app (Terminal 1)
python run.py
# Or: flask run
```

**Access**: http://127.0.0.1:5000

**Demo Accounts**:
- Teacher: `guru@aldudu.com` / `123`
- Student: `murid@aldudu.com` / `123`

### Running Tests

```bash
pytest
# Or specific test file
pytest tests/test_gradebook.py -v
```

### Docker Deployment (Production-like)

```bash
# Build and run containers
docker compose -f deploy/docker-compose.prod.yml up -d --build --force-recreate

# Run migrations
docker compose -f deploy/docker-compose.prod.yml exec web flask db upgrade

# Seed database
docker compose -f deploy/docker-compose.prod.yml exec web flask init-db

# Access: http://localhost:8000
```

---

## Key Configuration

### Environment Variables (`.env`)

```env
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/aldudu_academy
SECRET_KEY=your-secret-key-here
FLASK_SECRET_KEY=your-flask-secret-key
FLASK_ENV=development  # or production

# Email (Mailtrap for development)
MAIL_SERVER=sandbox.smtp.mailtrap.io
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-mailtrap-username
MAIL_PASSWORD=your-mailtrap-password

# Celery/Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Configuration Classes (`app/config.py`)

- `DevelopmentConfig`: Debug mode, SQLite/MySQL local
- `ProductionConfig`: Secure cookies, no debug
- `TestingConfig`: SQLite test database

---

## Development Conventions

### Code Style

- **Python**: Standard Flask application factory pattern
- **Models**: SQLAlchemy ORM with explicit relationships
- **Blueprints**: Modular route organization by feature
- **Services**: Business logic separated from routes

### Database Migrations

```bash
# Create new migration
flask db migrate -m "description"

# Apply migrations
flask db upgrade

# Downgrade (if needed)
flask db downgrade
```

### Testing Practices

- Tests use pytest fixtures (`tests/conftest.py`)
- Integration tests for major features (gradebook, discussion, etc.)
- Test files named `test_<feature>.py`

### Git Workflow

- Feature branches for new functionality
- Migration scripts versioned in `migrations/versions/`
- Documentation updates in Markdown files

---

## Important Documentation Files

| File | Description |
|------|-------------|
| `README.md` | Main project overview and quickstart |
| `DEPLOY.md` | Production deployment guide (SQLite → PostgreSQL) |
| `RUNBOOK.md` | Step-by-step deployment and operations guide |
| `GRADEBOOK_IMPLEMENTATION.md` | Gradebook feature technical details |
| `RASCH_IMPLEMENTATION.md` | Rasch Model integration details |
| `PHASE3_COMPLETE.md` | Phase 3 completion summary |
| `scripts/README.md` | Migration scripts documentation |

---

## API Endpoints Summary

### Authentication
- `POST /login` - User login
- `POST /logout` - User logout

### Courses
- `GET /courses` - List courses
- `GET /course/<id>` - Course detail
- `POST /course/create` - Create course

### Gradebook
- `GET /gradebook/course/<id>` - Course gradebook view
- `POST /gradebook/api/categories` - Create grade category
- `POST /gradebook/api/items` - Create grade item
- `POST /gradebook/api/entries/bulk` - Bulk save grades
- `POST /gradebook/api/quiz/import` - Import quiz to gradebook

### Rasch Analysis
- `GET /api/rasch/quizzes/:id/threshold-status` - Check threshold
- `POST /api/rasch/quizzes/:id/analyze` - Trigger analysis
- `GET /api/rasch/analyses/:id/persons` - Get ability measures
- `GET /api/rasch/analyses/:id/items` - Get difficulty measures
- `GET /api/rasch/analyses/:id/wright-map` - Wright Map data

### Health Check
- `GET /healthz` - Health check endpoint

---

## Common Tasks

### Add a New Blueprint

1. Create `app/blueprints/<feature>.py`
2. Define blueprint and routes
3. Register in `app/blueprints/__init__.py`

### Add a New Model

1. Create `app/models/<feature>.py`
2. Define SQLAlchemy model
3. Import in `app/models/__init__.py`
4. Create migration: `flask db migrate -m "add <feature>"`

### Background Task (Celery)

1. Add task to `app/workers/<task>_worker.py`
2. Ensure worker is included in `celery_app.py`
3. Call task asynchronously: `task.delay(args)`

### Seed Data

```bash
# Example seeding scripts
python scripts/seed_schools_teachers.py
python scripts/seed_students.py
```

---

## Troubleshooting

### Celery Worker Issues (Windows)

```bash
# Use solo pool for Windows development
python run_worker.py --pool=solo --without-gossip --without-mingle
```

### Database Connection

```bash
# Test MySQL connection
python scripts/test_mysql_connection.py

# For PostgreSQL, ensure psycopg2-binary is installed
pip install psycopg2-binary
```

### Migration Errors

```bash
# Check current migration version
flask db current

# Show migration history
flask db history
```

---

## Security Notes

- **SECRET_KEY**: Never commit to Git. Use environment variables or `instance/config.py`
- **Database Credentials**: Store in `.env` (gitignored) or secret manager
- **Production**: Use `FLASK_ENV=production` for secure cookie settings
- **Talisman**: CSP configured in `app/__init__.py` for production deployments
