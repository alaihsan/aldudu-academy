import os
import hashlib
import warnings
from typing import Optional, Dict
from dotenv import load_dotenv
from flask import Flask, jsonify, request, render_template
from flask_talisman import Talisman

from .extensions import db, login_manager, mail, migrate, cache, limiter
from .config import config_by_name
from .validators.env import run_all_validations


def create_app(test_config: Optional[Dict] = None) -> Flask:
    load_dotenv(override=True)
    app = Flask(__name__, instance_relative_config=True)

    # Validate environment variables
    testing = test_config is not None or os.environ.get('TESTING', 'false').lower() == 'true'
    try:
        run_all_validations(testing=testing)
    except Exception as e:
        if not testing:
            raise
        warnings.warn(f"Environment validation warning (testing mode): {str(e)}")

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

    # Register middleware
    from .middleware import register_all_middleware
    register_all_middleware(app)

    # Register blueprints
    from .blueprints import create_blueprints
    for bp in create_blueprints():
        app.register_blueprint(bp)

    # Register health and metrics blueprints
    from .blueprints.health import health_bp
    from .blueprints.metrics import metrics_bp
    app.register_blueprint(health_bp)
    app.register_blueprint(metrics_bp)

    # Register CLI commands
    from .cli import register_cli_commands
    register_cli_commands(app)

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

    return app
