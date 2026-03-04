import os
from typing import Optional, Dict
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_talisman import Talisman

from .models import db, User
from .blueprints import create_blueprints

migrate = Migrate()

def create_app(test_config: Optional[Dict] = None) -> Flask:
    """
    Create and configure the Flask application.
    """
    load_dotenv()
    app = Flask(__name__, instance_relative_config=True)

    # Load secret key
    secret = os.environ.get('FLASK_SECRET_KEY')
    if secret:
        app.config['SECRET_KEY'] = secret
    else:
        app.config.from_pyfile('config.py', silent=True)
        if not app.config.get('SECRET_KEY'):
            app.config['SECRET_KEY'] = 'dev-secret-change-me'

    # Database configuration
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        # Fallback to sqlite if not set for dev
        database_url = 'sqlite:///dev.db'
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    if test_config:
        app.config.update(test_config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

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

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'main.index'

    @login_manager.user_loader
    def load_user(user_id: str) -> Optional[User]:
        try:
            return db.session.get(User, int(user_id))
        except (ValueError, TypeError):
            return None

    # Register blueprints
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
        return jsonify({'success': False, 'message': str(e.description) or 'Sumber daya tidak ditemukan'}), 404

    @app.errorhandler(500)
    def server_error(e):
        app.logger.error(f"Server Error: {e}")
        return jsonify({'success': False, 'message': 'Terjadi kesalahan internal pada server'}), 500

    @app.route('/healthz', methods=['GET'])
    def healthz():
        return jsonify({'status': 'ok'}), 200

    # CLI: initialize DB
    @app.cli.command('init-db')
    def init_db_command():
        from .models import User, AcademicYear, Course, UserRole
        from .helpers import generate_class_code
        
        db.create_all()
        # Logika sample users bisa ditambahkan di sini jika perlu
        print('Initialized the database.')

    return app
