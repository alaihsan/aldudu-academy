from flask import Blueprint


def create_blueprints():
    from .auth import auth_bp
    from .courses import courses_bp
    from .main import main_bp
    from .quiz import quiz_bp
    from .discussion import discussion_bp
    
    return [main_bp, auth_bp, courses_bp, quiz_bp, discussion_bp]