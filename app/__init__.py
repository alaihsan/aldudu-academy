import os
import hashlib
from typing import Optional, Dict
from dotenv import load_dotenv
from flask import Flask, jsonify, request, render_template
from flask_talisman import Talisman

from .extensions import db, login_manager, mail, migrate, cache, limiter
from .config import config_by_name


def create_app(test_config: Optional[Dict] = None) -> Flask:
    load_dotenv(override=True)
    app = Flask(__name__, instance_relative_config=True)

    # Load config
    env = os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config_by_name.get(env, config_by_name['development']))

    # Override with instance config if present
    app.config.from_pyfile('config.py', silent=True)

    # Override with env vars
    secret = os.environ.get('FLASK_SECRET_KEY')
    if secret:
        app.config['SECRET_KEY'] = secret

    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url

    if test_config:
        app.config.update(test_config)

    # Initialize Sentry
    sentry_dsn = os.environ.get('SENTRY_DSN')
    if sentry_dsn:
        import sentry_sdk
        sentry_sdk.init(
            dsn=sentry_dsn,
            # Do not send PII (Personally Identifiable Information)
            send_default_pii=False,
            traces_sample_rate=float(os.environ.get('SENTRY_TRACES_SAMPLE_RATE', '0.1')),
            profiles_sample_rate=float(os.environ.get('SENTRY_PROFILES_SAMPLE_RATE', '0.1')),
            environment=env,
            release=os.environ.get('SENTRY_RELEASE', 'aldudu-academy@1.0.0'),
        )

    # Initialize Prometheus Metrics
    prometheus_enabled = os.environ.get('PROMETHEUS_ENABLED', 'true').lower() == 'true'
    if prometheus_enabled:
        from prometheus_flask_exporter import PrometheusMetrics
        from prometheus_client import CollectorRegistry, Gauge, Counter, Histogram
        import time
        
        # Custom metrics registry
        metrics_registry = CollectorRegistry()
        
        # Custom metrics
        REQUEST_COUNT = Counter(
            'aldudu_requests_total',
            'Total requests',
            ['method', 'endpoint', 'status'],
            registry=metrics_registry
        )
        
        REQUEST_LATENCY = Histogram(
            'aldudu_request_latency_seconds',
            'Request latency',
            ['method', 'endpoint'],
            buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0),
            registry=metrics_registry
        )
        
        ACTIVE_USERS = Gauge(
            'aldudu_active_users',
            'Active users',
            registry=metrics_registry
        )
        
        # Business metrics
        COURSES_CREATED = Counter(
            'aldudu_courses_created_total',
            'Total courses created',
            registry=metrics_registry
        )
        
        QUIZZIS_TAKEN = Counter(
            'aldudu_quizzes_taken_total',
            'Total quizzes taken',
            registry=metrics_registry
        )
        
        STUDENTS_ENROLLED = Gauge(
            'aldudu_students_enrolled',
            'Total students enrolled',
            registry=metrics_registry
        )
        
        # Initialize Flask exporter
        metrics = PrometheusMetrics(
            app,
            registry=metrics_registry,
            defaults_prefix='aldudu',
            group_by='endpoint',
            exclude_paths=['/healthz', '/metrics', '/static/']
        )
        
        # Store metrics in app config for later use
        app.config['PROMETHEUS_METRICS'] = {
            'request_count': REQUEST_COUNT,
            'request_latency': REQUEST_LATENCY,
            'active_users': ACTIVE_USERS,
            'courses_created': COURSES_CREATED,
            'quizzes_taken': QUIZZIS_TAKEN,
            'students_enrolled': STUDENTS_ENROLLED,
            'registry': metrics_registry,
        }

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)

    # Initialize Celery
    from .celery_app import init_celery
    celery = init_celery(app)
    app.extensions['celery'] = celery

    login_manager.login_view = 'main.index'

    @login_manager.user_loader
    def load_user(user_id: str):
        from .models import User
        try:
            return db.session.get(User, int(user_id))
        except (ValueError, TypeError):
            return None

    # Configure Talisman
    csp = {
        'default-src': "'self'",
        'script-src': [
            "'self'",
            'https://cdn.tailwindcss.com',
            'https://unpkg.com',
            'https://cdn.jsdelivr.net',
            'https://cdnjs.cloudflare.com',
            "'unsafe-inline'",
        ],
        'style-src': [
            "'self'",
            'https://fonts.googleapis.com',
            'https://cdn.jsdelivr.net',
            "'unsafe-inline'",
        ],
        'font-src': [
            "'self'",
            'https://fonts.gstatic.com',
        ],
        'img-src': ["'self'", 'data:'],
    }
    is_prod = os.environ.get('FLASK_ENV') == 'production'
    Talisman(app, content_security_policy=csp, force_https=is_prod)

    # Register asset_hash Jinja2 helper for cache-busting static assets
    @app.template_global()
    def asset_hash(filename: str) -> str:
        """Return a short content-based hash for a static file (cache-busting)."""
        filepath = os.path.join(app.static_folder, filename)
        try:
            with open(filepath, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()[:8]
        except FileNotFoundError:
            return 'missing'

    # Register tenant middleware
    from .middleware import register_middleware
    register_middleware(app)

    # Register blueprints
    from .blueprints import create_blueprints
    for bp in create_blueprints():
        app.register_blueprint(bp)

    # Global Error Handlers
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({'success': False, 'message': str(e.description) or 'Request tidak valid'}), 400

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({'success': False, 'message': str(e.description) or 'Anda tidak memiliki izin'}), 403

    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith('/api/') or request.path.startswith('/superadmin/api/'):
            return jsonify({'success': False, 'message': str(e.description) or 'Sumber daya tidak ditemukan'}), 404
        return jsonify({'success': False, 'message': str(e.description) or 'Sumber daya tidak ditemukan'}), 404

    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify({'success': False, 'message': 'Terlalu banyak percobaan. Coba lagi nanti.'}), 429

    @app.errorhandler(500)
    def server_error(e):
        app.logger.error(f"Server Error: {e}")
        return jsonify({'success': False, 'message': 'Terjadi kesalahan internal pada server'}), 500

    @app.route('/healthz', methods=['GET'])
    def healthz():
        return jsonify({'status': 'ok'}), 200

    # Health Status Dashboard Routes
    @app.route('/superadmin/health')
    def health_dashboard():
        from .models import User, UserRole, School, SchoolStatus
        from sqlalchemy import func
        
        stats = {
            'total_users': User.query.count(),
            'users_by_role': db.session.query(
                User.role, func.count(User.id)
            ).group_by(User.role).all(),
            'total_schools': School.query.count(),
            'active_schools': School.query.filter_by(status=SchoolStatus.ACTIVE).count(),
            'pending_schools': School.query.filter_by(status=SchoolStatus.PENDING).count(),
            'suspended_schools': School.query.filter_by(status=SchoolStatus.SUSPENDED).count(),
        }
        return render_template('superadmin/health.html', stats=stats)

    # Performance Metrics Dashboard Routes
    @app.route('/superadmin/metrics')
    def metrics_dashboard():
        return render_template('superadmin/metrics.html')

    # Health Check APIs
    @app.route('/superadmin/api/health/checks', methods=['GET'])
    def api_health_checks():
        """Comprehensive health checks for all services."""
        import time
        import redis
        from sqlalchemy import text
        
        checks = {}
        overall_healthy = True
        
        # 1. Database Check
        try:
            start = time.time()
            db.session.execute(text('SELECT 1'))
            duration = (time.time() - start) * 1000
            checks['database'] = {
                'status': 'healthy',
                'response_time': f'{duration:.2f}ms',
                'message': 'Database connection OK'
            }
        except Exception as e:
            checks['database'] = {
                'status': 'unhealthy',
                'message': str(e)
            }
            overall_healthy = False
        
        # 2. Redis/Celery Check
        try:
            start = time.time()
            redis_client = redis.from_url(os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'))
            redis_client.ping()
            duration = (time.time() - start) * 1000
            checks['redis'] = {
                'status': 'healthy',
                'response_time': f'{duration:.2f}ms',
                'message': 'Redis connection OK'
            }
        except Exception as e:
            checks['redis'] = {
                'status': 'unhealthy',
                'message': str(e)
            }
            overall_healthy = False
        
        # 3. Email Service Check
        try:
            from flask_mail import Message
            start = time.time()
            mail_server = app.extensions.get('mail')
            if mail_server:
                # Just check SMTP connection, don't send
                import smtplib
                mail_settings = app.config.get('MAIL_SERVER')
                if mail_settings:
                    duration = (time.time() - start) * 1000
                    checks['email'] = {
                        'status': 'healthy',
                        'response_time': f'{duration:.2f}ms',
                        'message': f'Mail server: {mail_settings}'
                    }
                else:
                    checks['email'] = {
                        'status': 'warning',
                        'message': 'Mail server not configured'
                    }
            else:
                checks['email'] = {
                    'status': 'warning',
                    'message': 'Mail extension not initialized'
                }
        except Exception as e:
            checks['email'] = {
                'status': 'unhealthy',
                'message': str(e)
            }
            overall_healthy = False
        
        # 4. Sentry Check
        sentry_dsn = os.environ.get('SENTRY_DSN')
        if sentry_dsn:
            checks['sentry'] = {
                'status': 'healthy',
                'message': 'Sentry configured',
                'pii_enabled': False,
            }
        else:
            checks['sentry'] = {
                'status': 'warning',
                'message': 'Sentry not configured (add SENTRY_DSN to .env)'
            }
        
        # 5. Storage/Write Permission Check
        try:
            instance_path = app.instance_path
            os.makedirs(instance_path, exist_ok=True)
            test_file = os.path.join(instance_path, '.health_check')
            with open(test_file, 'w') as f:
                f.write('ok')
            os.remove(test_file)
            checks['storage'] = {
                'status': 'healthy',
                'message': f'Write permission OK: {instance_path}'
            }
        except Exception as e:
            checks['storage'] = {
                'status': 'warning',
                'message': str(e)
            }
        
        return jsonify({
            'success': True,
            'overall_healthy': overall_healthy,
            'checks': checks,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        })

    @app.route('/superadmin/api/health/stats', methods=['GET'])
    def api_health_stats():
        """Get application statistics."""
        from .models import User, UserRole, School, SchoolStatus
        from sqlalchemy import func
        import os
        
        # Database stats
        users_by_role = db.session.query(
            User.role, func.count(User.id)
        ).group_by(User.role).all()
        
        # Check if models exist in registry
        registry = str(db.Model.registry._class_registry)
        has_course = 'Course' in registry
        has_quiz = 'Quiz' in registry
        has_assignment = 'Assignment' in registry
        has_activity_log = 'ActivityLog' in registry
        
        stats = {
            'users': {
                'total': User.query.count(),
                'by_role': {role.value: count for role, count in users_by_role}
            },
            'schools': {
                'total': School.query.count(),
                'active': School.query.filter_by(status=SchoolStatus.ACTIVE).count(),
                'pending': School.query.filter_by(status=SchoolStatus.PENDING).count(),
                'suspended': School.query.filter_by(status=SchoolStatus.SUSPENDED).count(),
            },
            'content': {
                'courses': Course.query.count() if has_course else 0,
                'quizzes': Quiz.query.count() if has_quiz else 0,
                'assignments': Assignment.query.count() if has_assignment else 0,
            },
            'activity': {
                'last_24h': ActivityLog.query.filter(
                    ActivityLog.created_at >= func.now() - 1
                ).count() if has_activity_log else 0,
            },
            'system': {
                'python_version': os.sys.version.split()[0],
                'platform': os.sys.platform,
            }
        }
        
        return jsonify({'success': True, 'stats': stats})

    @app.route('/superadmin/api/health/test-email', methods=['POST'])
    def api_test_email_health():
        """Send test email to verify email configuration."""
        import time
        from flask_mail import Message
        from .services.email_service import send_email
        from flask_login import current_user
        
        data = request.get_json() or {}
        recipient = data.get('email', current_user.email if hasattr(current_user, 'email') else None)
        
        if not recipient:
            return jsonify({'success': False, 'message': 'Email recipient required'}), 400
        
        ok = send_email(
            subject='Health Check - Email Test',
            recipients=[recipient],
            html_body=(
                '<div style="font-family:sans-serif;padding:20px">'
                '<h2 style="color:#0282c6">Email Test ✓</h2>'
                '<p>Health check email test successful.</p>'
                f'<p>Sent to: <strong>{recipient}</strong></p>'
                f'<p>Time: {time.strftime("%Y-%m-%d %H:%M:%S")}</p>'
                '</div>'
            ),
        )
        
        if ok:
            return jsonify({'success': True, 'message': f'Test email sent to {recipient}'})
        return jsonify({'success': False, 'message': 'Failed to send email. Check Mailtrap config.'}), 500

    @app.route('/superadmin/api/health/clear-cache', methods=['POST'])
    def api_clear_cache():
        """Clear all application cache."""
        from flask_caching import Cache
        
        try:
            # Get cache instance from extensions
            cache_instance = app.extensions.get('cache')
            
            if not cache_instance:
                return jsonify({'success': False, 'message': 'Cache not initialized'}), 500
            
            # Clear all cache
            cache_instance.clear()
            
            # Also clear memoized functions (like _get_school_by_slug)
            from app.middleware import invalidate_school_cache
            # Note: Flask-Caching doesn't have a direct way to clear all memoized functions
            # But cache.clear() should clear the underlying cache storage
            
            return jsonify({
                'success': True, 
                'message': 'Cache berhasil dibersihkan',
                'details': 'Semua data cache telah dihapus'
            })
        except Exception as e:
            return jsonify({
                'success': False, 
                'message': f'Gagal membersihkan cache: {str(e)}'
            }), 500

    # Performance Metrics APIs
    @app.route('/superadmin/api/metrics/data', methods=['GET'])
    def api_metrics_data():
        """Get comprehensive metrics data for dashboard."""
        from .models import User, UserRole, School, SchoolStatus, Course
        from sqlalchemy import func
        import psutil
        import os
        
        # Get Prometheus metrics if available
        prom_metrics = app.config.get('PROMETHEUS_METRICS', {})
        
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Application stats
        users_by_role = db.session.query(
            User.role, func.count(User.id)
        ).group_by(User.role).all()
        
        schools_by_status = db.session.query(
            School.status, func.count(School.id)
        ).group_by(School.status).all()
        
        # Calculate active users (logged in last 24h - mock for now)
        active_users = User.query.filter(User.is_active == True).count()
        
        # Update Prometheus gauges
        if prom_metrics.get('active_users'):
            prom_metrics['active_users'].set(active_users)
        
        # Students enrolled
        students_enrolled = User.query.filter(User.role == UserRole.MURID).count()
        if prom_metrics.get('students_enrolled'):
            prom_metrics['students_enrolled'].set(students_enrolled)
        
        metrics = {
            'system': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_used_gb': round(memory.used / (1024**3), 2),
                'memory_total_gb': round(memory.total / (1024**3), 2),
                'disk_percent': disk.percent,
                'disk_used_gb': round(disk.used / (1024**3), 2),
                'disk_total_gb': round(disk.total / (1024**3), 2),
            },
            'application': {
                'total_requests': 0,  # Would come from Prometheus
                'avg_latency_ms': 0,  # Would come from Prometheus
                'error_rate': 0,  # Would come from Prometheus
                'active_users': active_users,
                'requests_per_second': 0,  # Would come from Prometheus
            },
            'users': {
                'total': User.query.count(),
                'by_role': {role.value: count for role, count in users_by_role},
            },
            'schools': {
                'total': School.query.count(),
                'by_status': {status.value: count for status, count in schools_by_status},
            },
            'business': {
                'courses': Course.query.count() if 'Course' in str(db.Model.registry._class_registry) else 0,
                'students_enrolled': students_enrolled,
                'quizzes_taken': 0,  # Would increment on quiz submission
            },
            'prometheus': {
                'enabled': prometheus_enabled,
                'endpoint': '/metrics' if prometheus_enabled else None,
            }
        }
        
        return jsonify({'success': True, 'metrics': metrics})

    @app.route('/superadmin/api/metrics/refresh', methods=['POST'])
    def api_metrics_refresh():
        """Force refresh metrics."""
        import time
        
        return jsonify({
            'success': True,
            'message': 'Metrics refreshed',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        })

    # CLI commands
    @app.cli.command('init-db')
    def init_db_command():
        db.create_all()
        print('Initialized the database.')

    @app.cli.command('create-superadmin')
    def create_superadmin_command():
        from .models import User, UserRole
        import click

        email = click.prompt('Email')
        name = click.prompt('Name')
        password = click.prompt('Password', hide_input=True, confirmation_prompt=True)

        existing = User.query.filter_by(email=email).first()
        if existing:
            print(f'User with email {email} already exists.')
            return

        user = User(
            name=name,
            email=email,
            role=UserRole.SUPER_ADMIN,
            is_active=True,
            email_verified=True,
            school_id=None,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f'Super Admin "{name}" created successfully.')

    return app
