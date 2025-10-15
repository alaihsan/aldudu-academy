from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, current_user
from models import User
from helpers import is_valid_email

auth_bp = Blueprint('auth', __name__, url_prefix='/api')


@auth_bp.route('/session', methods=['GET'])
def api_session():
    if current_user.is_authenticated:
        return jsonify({'isAuthenticated': True, 'user': {'name': current_user.name, 'role': current_user.role.value}})
    return jsonify({'isAuthenticated': False})


@auth_bp.route('/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')
    if not email or not password or not is_valid_email(email):
        return jsonify({'success': False, 'message': 'Email atau password tidak valid'}), 400
    user = User.query.filter_by(email=email.strip()).first()
    if user and user.check_password(password):
        login_user(user)
        return jsonify({'success': True, 'user': {'name': user.name, 'role': user.role.value}})
    return jsonify({'success': False, 'message': 'Email atau password salah'}), 401


@auth_bp.route('/logout', methods=['POST'])
def api_logout():
    if current_user.is_authenticated:
        logout_user()
        return jsonify({'success': True})
    return jsonify({'success': False}), 401
