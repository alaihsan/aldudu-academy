"""
Discussion Blueprint - forum threads, posts, and likes for a course.
"""
import logging
from flask import Blueprint, request, jsonify, abort, render_template
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload, selectinload
from app.core.extensions import db
from app.models import Course, UserRole
from app.discussion.models import Discussion, Post, Like
from app.helpers import sanitize_text
from app.core.authorization import get_school_id_or_abort, verify_course_in_school

logger = logging.getLogger(__name__)

discussion_bp = Blueprint('discussion', __name__, url_prefix='/api')

# Separate blueprint (no /api prefix) for page renders, since discussion_bp's
# prefix is fixed to /api for its JSON routes.
discussion_pages_bp = Blueprint('discussion_pages', __name__, template_folder='templates')


@discussion_pages_bp.route('/kelas/<int:course_id>/diskusi')
@login_required
def course_discussions(course_id):
    """Halaman Forum Diskusi per kelas"""
    course = db.session.get(Course, course_id)
    if course is None:
        abort(404)
    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)

    is_teacher = (current_user.id == course.teacher_id)
    is_student = current_user in course.students
    if not is_teacher and not is_student:
        abort(403)

    return render_template('discussion/course_discussions.html', course=course, is_teacher=is_teacher)


@discussion_pages_bp.route('/kelas/<int:course_id>/diskusi/<int:discussion_id>')
@login_required
def discussion_detail(course_id, discussion_id):
    course = db.session.get(Course, course_id)
    if course is None:
        abort(404)
    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)
    discussion = db.session.get(Discussion, discussion_id)
    if discussion is None or discussion.course_id != course_id:
        abort(404)
    is_teacher = (current_user.id == course.teacher_id)
    if not is_teacher and current_user not in course.students:
        abort(403)
    return render_template('discussion/discussion_detail.html', course=course, discussion=discussion, is_teacher=is_teacher)


@discussion_bp.route('/courses/<int:course_id>/discussions', methods=['POST'])
@login_required
def create_discussion(course_id):
    course = db.session.get(Course, course_id)
    if not course:
        return jsonify({'success': False, 'message': 'Mata pelajaran tidak ditemukan'}), 404

    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)

    if current_user.role != UserRole.GURU and current_user not in course.students:
        return jsonify({'success': False, 'message': 'Anda tidak memiliki izin untuk membuat diskusi di kelas ini'}), 403

    data = request.get_json() or {}
    title = sanitize_text(data.get('title', ''), max_len=200)
    content = sanitize_text(data.get('content', ''))

    if not title or not content:
        return jsonify({'success': False, 'message': 'Judul dan isi diskusi wajib diisi'}), 400

    try:
        new_discussion = Discussion(
            title=title,
            course_id=course_id,
            user_id=current_user.id
        )
        db.session.add(new_discussion)
        db.session.commit()

        new_post = Post(
            content=content,
            discussion_id=new_discussion.id,
            user_id=current_user.id
        )
        db.session.add(new_post)
        db.session.commit()

        return jsonify({'success': True, 'discussion': {'id': new_discussion.id, 'title': new_discussion.title}}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to create discussion for course {course_id}: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Terjadi kesalahan saat membuat diskusi'}), 500


@discussion_bp.route('/courses/<int:course_id>/discussions', methods=['GET'])
@login_required
def get_discussions(course_id):
    course = db.session.get(Course, course_id)
    if not course:
        return jsonify({'success': False, 'message': 'Mata pelajaran tidak ditemukan'}), 404

    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)

    if current_user.role != UserRole.GURU and current_user not in course.students:
        return jsonify({'success': False, 'message': 'Anda tidak memiliki izin untuk melihat diskusi di kelas ini'}), 403

    discussions = Discussion.query.filter_by(course_id=course_id)\
        .options(joinedload(Discussion.user), selectinload(Discussion.posts).joinedload(Post.user))\
        .order_by(Discussion.created_at.desc()).all()
    return jsonify({'success': True, 'discussions': [d.to_dict() for d in discussions]})


@discussion_bp.route('/discussions/<int:discussion_id>/posts', methods=['GET'])
@login_required
def get_posts(discussion_id):
    discussion = db.session.get(Discussion, discussion_id)
    if not discussion:
        return jsonify({'success': False, 'message': 'Diskusi tidak ditemukan'}), 404

    if current_user.role != UserRole.GURU and current_user not in discussion.course.students:
        return jsonify({'success': False, 'message': 'Anda tidak memiliki izin untuk melihat diskusi ini'}), 403

    posts = Post.query.filter_by(discussion_id=discussion_id)\
        .options(joinedload(Post.user), selectinload(Post.replies).joinedload(Post.user), selectinload(Post.likes).joinedload(Like.user))\
        .order_by(Post.created_at.asc()).all()
    return jsonify({'success': True, 'posts': [p.to_dict() for p in posts]})


@discussion_bp.route('/discussions/<int:discussion_id>/posts', methods=['POST'])
@login_required
def add_post(discussion_id):
    discussion = db.session.get(Discussion, discussion_id)
    if not discussion:
        return jsonify({'success': False, 'message': 'Diskusi tidak ditemukan'}), 404

    if discussion.closed:
        return jsonify({'success': False, 'message': 'Diskusi ini sudah ditutup'}), 403

    data = request.get_json() or {}
    content = sanitize_text(data.get('content', ''))
    parent_id = data.get('parent_id')

    if not content:
        return jsonify({'success': False, 'message': 'Isi respon tidak boleh kosong'}), 400

    new_post = Post(
        content=content,
        discussion_id=discussion_id,
        user_id=current_user.id,
        parent_id=parent_id
    )
    db.session.add(new_post)
    db.session.commit()

    return jsonify({'success': True, 'post': new_post.to_dict()}), 201


@discussion_bp.route('/posts/<int:post_id>/like', methods=['POST'])
@login_required
def like_post(post_id):
    post = db.session.get(Post, post_id)
    if not post:
        return jsonify({'success': False, 'message': 'Post tidak ditemukan'}), 404

    like = Like.query.filter_by(post_id=post_id, user_id=current_user.id).first()
    if like:
        db.session.delete(like)
        db.session.commit()
        return jsonify({'success': True, 'action': 'unliked'})
    else:
        new_like = Like(post_id=post_id, user_id=current_user.id)
        db.session.add(new_like)
        db.session.commit()
        return jsonify({'success': True, 'action': 'liked'})


@discussion_bp.route('/posts/<int:post_id>', methods=['DELETE'])
@login_required
def delete_post(post_id):
    post = db.session.get(Post, post_id)
    if not post:
        return jsonify({'success': False, 'message': 'Post tidak ditemukan'}), 404

    school_id = get_school_id_or_abort()
    verify_course_in_school(post.discussion.course, school_id)

    # Allow deletion if user is the post author or the discussion creator (teacher)
    if current_user.id != post.user_id and current_user.id != post.discussion.user_id:
        return jsonify({'success': False, 'message': 'Anda tidak memiliki izin untuk menghapus post ini'}), 403

    db.session.delete(post)
    db.session.commit()

    return jsonify({'success': True})


@discussion_bp.route('/posts/<int:post_id>', methods=['PUT'])
@login_required
def api_edit_post(post_id):
    post = db.session.get(Post, post_id)
    if not post:
        abort(404, description="Postingan tidak ditemukan.")

    school_id = get_school_id_or_abort()
    verify_course_in_school(post.discussion.course, school_id)

    if current_user.id != post.user_id:
        abort(403, description="Anda tidak memiliki izin untuk mengedit postingan ini.")

    data = request.get_json()
    content = data.get('content', '').strip()

    if not content:
        return jsonify({'success': False, 'message': 'Konten tidak boleh kosong.'}), 400

    post.content = sanitize_text(content, max_len=5000)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Postingan berhasil diperbarui.'})


@discussion_bp.route('/discussions/<int:discussion_id>/close', methods=['POST'])
@login_required
def close_discussion(discussion_id):
    discussion = db.session.get(Discussion, discussion_id)
    if not discussion:
        return jsonify({'success': False, 'message': 'Diskusi tidak ditemukan'}), 404

    if discussion.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Hanya pembuat diskusi yang dapat menutupnya'}), 403

    discussion.closed = True
    db.session.commit()

    return jsonify({'success': True, 'message': 'Diskusi telah ditutup'})
