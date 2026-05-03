import os
from flask import Flask
from sqlalchemy import inspect, text
from app.config import Config
from app.extensions import db, login_manager
from app.helpers import matching_pair, plain_text
from app.models import User


def create_app(config_object=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_object)

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    app.jinja_env.filters["plain_text"] = plain_text
    app.jinja_env.filters["matching_left"] = lambda value: matching_pair(value)[0]
    app.jinja_env.filters["matching_right"] = lambda value: matching_pair(value)[1]

    from app.blueprints.auth import auth_bp
    from app.blueprints.main import main_bp
    from app.blueprints.quiz import quiz_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(quiz_bp, url_prefix="/api")

    @app.cli.command("init-db")
    def init_db_command():
        db.create_all()
        ensure_schema()
        print("Database initialized.")

    with app.app_context():
        ensure_schema()

    return app


def ensure_schema():
    db.create_all()
    inspector = inspect(db.engine)
    if "quizzes" not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns("quizzes")}
    additions = {
        "theme_font": "VARCHAR(50) NOT NULL DEFAULT 'Inter'",
        "theme_text_size": "VARCHAR(20) NOT NULL DEFAULT 'normal'",
        "theme_background": "VARCHAR(30) NOT NULL DEFAULT 'plain'",
        "theme_background_intensity": "INTEGER NOT NULL DEFAULT 20",
        "theme_form_width": "VARCHAR(20) NOT NULL DEFAULT 'standard'",
        "theme_card_radius": "VARCHAR(20) NOT NULL DEFAULT 'google'",
        "theme_density": "VARCHAR(20) NOT NULL DEFAULT 'normal'",
    }
    with db.engine.begin() as connection:
        for column, ddl in additions.items():
            if column not in existing:
                connection.execute(text(f"ALTER TABLE quizzes ADD COLUMN {column} {ddl}"))
