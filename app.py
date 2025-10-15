from flask import Flask
from typing import Optional, Dict
import os

from flask_login import LoginManager
from flask_migrate import Migrate

from models import db, User, AcademicYear, Course, UserRole
from blueprints import create_blueprints
from helpers import generate_class_code


migrate = Migrate()


def create_app(test_config: Optional[Dict] = None):
    """Create and configure the Flask application.

    test_config: optional dict to override configuration (used by tests).
    """
    app = Flask(__name__, instance_relative_config=True)

    # Load secret key from environment or instance config
    secret = os.environ.get('FLASK_SECRET_KEY')
    if secret:
        app.config['SECRET_KEY'] = secret
    else:
        app.config.from_pyfile('config.py', silent=True)
        if not app.config.get('SECRET_KEY'):
            app.config['SECRET_KEY'] = 'dev-secret-change-me'

    # Database configuration: prefer DATABASE_URL, otherwise default sqlite file
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        app.config.setdefault('SQLALCHEMY_DATABASE_URI', 'sqlite:///aldudu_academy.db')
    app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', False)

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
    def load_user(user_id):
        try:
            return db.session.get(User, int(user_id))
        except Exception:
            return None

    # Register blueprints
    for bp in create_blueprints():
        app.register_blueprint(bp)

    # CLI: initialize DB with sample data
    @app.cli.command('init-db')
    def init_db_command():
        with app.app_context():
            db.drop_all()
            db.create_all()
            guru = User(name='Bapak Budi', email='guru@aldudu.com', role=UserRole.GURU)
            guru.set_password('123')
            murid = User(name='Siti Murid', email='murid@aldudu.com', role=UserRole.MURID)
            murid.set_password('123')
            ay1 = AcademicYear(year='2025/2026', is_active=True)
            ay2 = AcademicYear(year='2024/2023')
            db.session.add_all([guru, murid, ay1, ay2])
            db.session.commit()

            course1 = Course(
                name='Matematika XI-A',
                academic_year_id=ay1.id,
                teacher_id=guru.id,
                class_code=generate_class_code(),
                color='#0ea5e9',
            )
            course2 = Course(
                name='Biologi XI-A',
                academic_year_id=ay1.id,
                teacher_id=guru.id,
                class_code=generate_class_code(),
                color='#10b981',
            )
            course3 = Course(
                name='Sejarah X-B',
                academic_year_id=ay2.id,
                teacher_id=guru.id,
                class_code=generate_class_code(),
                color='#f97316',
            )
            db.session.add_all([course1, course2, course3])
            murid.courses_enrolled.append(course3)
            db.session.commit()
            print('Initialized the database and added sample data.')

    return app


if __name__ == '__main__':
    create_app().run(debug=True)
