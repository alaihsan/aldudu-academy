from flask import Blueprint


def create_blueprints():
    from .auth import auth_bp
    from .courses import courses_bp
    from .main import main_bp
    
    # 1. Apakah Anda menambahkan baris impor ini?
    from .quiz import quiz_bp
    
    # 2. Apakah Anda menambahkan 'quiz_bp' ke dalam daftar return ini?
    return [main_bp, auth_bp, courses_bp, quiz_bp]