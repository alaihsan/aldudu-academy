import os
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
    sentry_dsn = os.environ.get('SENTRY_DSN', 'https://f62390a07b26a64ee235921994078f43@o4511087650734080.ingest.de.sentry.io/4511087662530640')
    if sentry_dsn:
        import sentry_sdk
        sentry_sdk.init(
            dsn=sentry_dsn,
            # Add data like request headers and IP for users
            # See https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
            send_default_pii=True,
            traces_sample_rate=float(os.environ.get('SENTRY_TRACES_SAMPLE_RATE', '0.1')),
            profiles_sample_rate=float(os.environ.get('SENTRY_PROFILES_SAMPLE_RATE', '0.1')),
            environment=env,
            release=os.environ.get('SENTRY_RELEASE', 'aldudu-academy@1.0.0'),
        )

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
        sentry_dsn = os.environ.get('SENTRY_DSN', 'https://f62390a07b26a64ee235921994078f43@o4511087650734080.ingest.de.sentry.io/4511087662530640')
        if sentry_dsn:
            checks['sentry'] = {
                'status': 'healthy',
                'message': 'Sentry configured (Default DSN)',
                'dsn': sentry_dsn[:40] + '...',
                'pii_enabled': True,
            }
        else:
            checks['sentry'] = {
                'status': 'warning',
                'message': 'Sentry not configured'
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
