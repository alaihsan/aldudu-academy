import os
from typing import Optional, Dict
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_talisman import Talisman

from .extensions import db, login_manager, mail, migrate, cache, limiter
from .config import config_by_name


def create_app(test_config: Optional[Dict] = None) -> Flask:
    load_dotenv()
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

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)

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
