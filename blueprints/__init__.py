from flask import Blueprint


def create_blueprints():
    from .auth import auth_bp
    from .courses import courses_bp
    from .main import main_bp
    return [main_bp, auth_bp, courses_bp]
