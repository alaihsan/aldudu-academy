from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from app.models import WhatsNew
from app.extensions import db

whats_new_view_bp = Blueprint('whats_new_view', __name__)


@whats_new_view_bp.before_request
@login_required
def login_required():
    pass


@whats_new_view_bp.route('/whats-new')
def view_whats_new():
    """Halaman What's New untuk semua user (Admin, Guru, Murid)."""
    return render_template('whats_new.html')


@whats_new_view_bp.route('/api/whats-new/published', methods=['GET'])
def api_get_published_whats_new():
    """Get semua What's New posts yang published untuk user biasa."""
    posts = WhatsNew.query.filter_by(is_published=True).order_by(WhatsNew.created_at.desc()).all()
    return jsonify({
        'success': True,
        'posts': [p.to_dict(include_author=True) for p in posts]
    })


@whats_new_view_bp.route('/api/whats-new/<int:post_id>', methods=['GET'])
def api_get_whats_new_post(post_id):
    """Get single What's New post (hanya yang published)."""
    post = WhatsNew.query.filter_by(id=post_id, is_published=True).first()
    if not post:
        return jsonify({'success': False, 'message': 'Post tidak ditemukan'}), 404

    return jsonify({
        'success': True,
        'post': post.to_dict(include_author=True)
    })
