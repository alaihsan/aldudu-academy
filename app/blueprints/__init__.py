from flask import Blueprint


def create_blueprints():
    from .auth import auth_bp
    from .courses import courses_bp
    from .main import main_bp
    from .quiz import quiz_bp
    from .discussion import discussion_bp
    from .issues import issues_bp
    from .admin import admin_bp
    from .superadmin import superadmin_bp
    from .tickets import tickets_bp
    from .gradebook import gradebook_bp
    from .assignment import assignment_bp

    return [main_bp, auth_bp, courses_bp, quiz_bp, discussion_bp, issues_bp, admin_bp, superadmin_bp, tickets_bp, gradebook_bp, assignment_bp]