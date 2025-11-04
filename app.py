"""
Main Flask application for Aldudu Academy.

This module contains the Flask application factory and configuration.
"""

import os
import sys
from typing import Optional, Dict

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from flask_login import LoginManager
from flask_migrate import Migrate

from blueprints import create_blueprints
from models import db, User


migrate = Migrate()


def create_app(test_config: Optional[Dict] = None) -> Flask:
    """
    Create and configure the Flask application.

    Args:
        test_config: Optional dict to override configuration (used by tests).

    Returns:
        Flask application instance.
    """
    load_dotenv()
    app = Flask(__name__, instance_relative_config=True)

    # Load secret key from environment or instance config
    secret = os.environ.get('FLASK_SECRET_KEY')
    if secret:
        app.config['SECRET_KEY'] = secret
    else:
        app.config.from_pyfile('config.py', silent=True)
        if not app.config.get('SECRET_KEY'):
            app.config['SECRET_KEY'] = 'dev-secret-change-me'

    # Database configuration: require DATABASE_URL for PostgreSQL
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError(
            "DATABASE_URL environment variable is not set. "
            "Please set it to your PostgreSQL connection string."
        )

    db_host = os.environ.get('DB_HOST')
    if db_host:
        database_url = database_url.replace('127.0.0.1', db_host)

    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Allow tests to override configuration
    if test_config:
        app.config.update(test_config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'main.index'

    @login_manager.user_loader
    def load_user(user_id: str) -> Optional['User']:
        """Load user by ID for Flask-Login."""
        from models import User
        try:
            return db.session.get(User, int(user_id))
        except (ValueError, TypeError):
            return None

    # Register blueprints
    for bp in create_blueprints():
        app.register_blueprint(bp)

    @app.before_request
    def before_request() -> None:
        """Log request details for debugging."""
        print("--- Request Log ---")
        print(request.method, request.path)
        print(request.headers)
        print("--- End Request Log ---")

    # Simple health endpoint for readiness/liveness checks
    @app.route('/healthz', methods=['GET'])
    def healthz() -> tuple:
        """Health check endpoint."""
        return jsonify({'status': 'ok'}), 200

    # CLI: initialize DB with sample data
    @app.cli.command('init-db')
    def init_db_command() -> None:
        """Initialize database with sample data."""
        from models import User, AcademicYear, Course, UserRole
        from helpers import generate_class_code

        with app.app_context():
            db.create_all()

            # Create sample users if they don't exist
            _create_sample_users()
            _create_sample_academic_years()
            _create_sample_courses()

            db.session.commit()
            print('Initialized the database and added sample data.')

    return app


def _create_sample_users() -> None:
    """Create sample users for development."""
    from models import User, UserRole

    guru = User.query.filter_by(email='guru@aldudu.com').first()
    if not guru:
        guru = User(name='Bapak Budi', email='guru@aldudu.com', role=UserRole.GURU)
        guru.set_password('123')
        db.session.add(guru)

    murid = User.query.filter_by(email='murid@aldudu.com').first()
    if not murid:
        murid = User(name='Siti Murid', email='murid@aldudu.com', role=UserRole.MURID)
        murid.set_password('123')
        db.session.add(murid)


def _create_sample_academic_years() -> None:
    """Create sample academic years."""
    from models import AcademicYear

    ay1 = AcademicYear.query.filter_by(year='2025/2026').first()
    if not ay1:
        ay1 = AcademicYear(year='2025/2026', is_active=True)
        db.session.add(ay1)

    ay2 = AcademicYear.query.filter_by(year='2024/2023').first()
    if not ay2:
        ay2 = AcademicYear(year='2024/2023')
        db.session.add(ay2)


def _create_sample_courses() -> None:
    """Create sample courses."""
    from models import Course, User, UserRole, AcademicYear
    from helpers import generate_class_code

    guru = User.query.filter_by(email='guru@aldudu.com').first()
    murid = User.query.filter_by(email='murid@aldudu.com').first()
    ay1 = AcademicYear.query.filter_by(year='2025/2026').first()
    ay2 = AcademicYear.query.filter_by(year='2024/2023').first()

    # Create courses if they don't exist
    courses_data = [
        ('Matematika XI-A', ay1.id, guru.id, '#0ea5e9'),
        ('Biologi XI-A', ay1.id, guru.id, '#10b981'),
        ('Sejarah X-B', ay2.id, guru.id, '#f97316'),
    ]

    for name, ay_id, teacher_id, color in courses_data:
        course = Course.query.filter_by(name=name).first()
        if not course:
            course = Course(
                name=name,
                academic_year_id=ay_id,
                teacher_id=teacher_id,
                class_code=generate_class_code(),
                color=color,
            )
            db.session.add(course)

    # Enroll student in one course
    course3 = Course.query.filter_by(name='Sejarah X-B').first()
    if course3 and course3 not in murid.courses_enrolled:
        murid.courses_enrolled.append(course3)


if __name__ == '__main__':
    create_app().run(debug=True)

