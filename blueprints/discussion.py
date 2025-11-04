
# blueprints/discussion.py

from flask import Blueprint, request, jsonify, abort
from flask_login import login_required, current_user
from models import db, Post, Discussion
from helpers import sanitize_text

discussion_bp = Blueprint('discussion', __name__, url_prefix='/api')

@discussion_bp.route('/posts/<int:post_id>', methods=['DELETE'])
@login_required
def api_delete_post(post_id):
    post = db.session.get(Post, post_id)
    if not post:
        abort(404, description="Postingan tidak ditemukan.")

    discussion = post.discussion
    course = discussion.course

    is_teacher = current_user.id == course.teacher_id
    is_discussion_creator = current_user.id == discussion.user_id

    if not is_teacher and not is_discussion_creator:
        abort(403, description="Anda tidak memiliki izin untuk menghapus postingan ini.")

    db.session.delete(post)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Postingan berhasil dihapus.'})

@discussion_bp.route('/posts/<int:post_id>', methods=['PUT'])
@login_required
def api_edit_post(post_id):
    post = db.session.get(Post, post_id)
    if not post:
        abort(404, description="Postingan tidak ditemukan.")

    if current_user.id != post.user_id:
        abort(403, description="Anda tidak memiliki izin untuk mengedit postingan ini.")

    data = request.get_json()
    content = data.get('content', '').strip()

    if not content:
        return jsonify({'success': False, 'message': 'Konten tidak boleh kosong.'}), 400

    post.content = sanitize_text(content, max_len=5000)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Postingan berhasil diperbarui.'})
