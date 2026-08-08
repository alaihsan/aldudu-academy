"""
Content Blueprint - links, files, and folder tree management for a course,
plus cross-course material import.
"""
import os
import uuid
import shutil
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, abort, current_app, send_from_directory
from flask_login import login_required, current_user
from app.core.extensions import db
from app.models import Course, UserRole, Quiz, Assignment, AssignmentStatus
from app.content.models import ContentFolder, Link, File
from app.helpers import sanitize_text, sanitize_rich_text, log_activity, get_jakarta_now
from app.core.authorization import get_school_id_or_abort, verify_course_in_school

logger = logging.getLogger(__name__)

content_bp = Blueprint('content', __name__, url_prefix='/api')

# Separate blueprint (no /api prefix) for file-serving routes, since
# content_bp's prefix is fixed to /api for its JSON routes.
content_files_bp = Blueprint('content_files', __name__)


def _trash_now():
    n = get_jakarta_now()
    return n.replace(tzinfo=None) if getattr(n, 'tzinfo', None) else n


def allowed_file(filename, allowed_extensions=None):
    """Check if file extension is allowed"""
    if allowed_extensions is None:
        allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {
            'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
            'png', 'jpg', 'jpeg', 'gif', 'webp',
            'txt', 'rtf', 'zip', 'rar', '7z'
        })
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def get_file_extension(filename):
    """Get file extension from filename"""
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return ''


def generate_secure_filename(original_filename):
    """Generate a secure filename with UUID to prevent path traversal"""
    ext = get_file_extension(original_filename)
    unique_id = uuid.uuid4().hex
    return f"{unique_id}.{ext}" if ext else unique_id


def _verify_material_owner(course):
    """Pastikan kelas valid & pemiliknya guru saat ini."""
    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)
    if course.teacher_id != current_user.id:
        return False
    return True


# ─── File serving ────────────────────────────────────────────────────────────

@content_files_bp.route('/files/<int:file_id>')
@login_required
def serve_file(file_id):
    file = db.session.get(File, file_id)
    if file is None:
        abort(404)

    course = file.course
    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)
    is_teacher = (current_user.id == course.teacher_id)

    if not is_teacher and current_user not in course.students:
        abort(403)

    now = get_jakarta_now()
    if file.start_date and now < file.start_date:
        abort(403, description="File is not yet available.")
    if file.end_date and now > file.end_date:
        abort(403, description="File has expired.")

    upload_folder = os.path.join(os.getcwd(), 'instance', 'uploads', str(course.id))
    return send_from_directory(upload_folder, file.filename, as_attachment=False)


@content_files_bp.route('/uploads/<int:course_id>/<path:filename>')
@login_required
def serve_question_image(course_id, filename):
    course = db.session.get(Course, course_id)
    if course is None:
        abort(404)
    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)
    is_teacher = (current_user.id == course.teacher_id)
    is_student = current_user in course.students
    if not is_teacher and not is_student:
        abort(403)
    upload_folder = os.path.join(os.getcwd(), 'instance', 'uploads', str(course_id))
    return send_from_directory(upload_folder, filename, as_attachment=False)


# ─── Links ───────────────────────────────────────────────────────────────────

@content_bp.route('/courses/<int:course_id>/links', methods=['POST'])
@login_required
def api_create_link(course_id):
    """
    Membuat link baru untuk sebuah mata pelajaran.
    Hanya guru yang mengajar mata pelajaran tersebut yang bisa mengakses.
    """

    # 1. Validasi: Hanya guru yang bisa membuat link
    if current_user.role != UserRole.GURU:
        return jsonify({'success': False, 'message': 'Hanya guru yang dapat membuat link'}), 403

    # 2. Validasi: Temukan mata pelajarannya
    course = db.session.get(Course, course_id)
    if not course:
        return jsonify({'success': False, 'message': 'Mata pelajaran tidak ditemukan'}), 404

    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)

    # 3. Validasi Keamanan: Pastikan guru ini adalah pemilik mata pelajaran
    if course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Anda tidak memiliki izin untuk menambah link di mata pelajaran ini'}), 403

    # 4. Ambil dan bersihkan data input
    data = request.get_json() or {}
    name = sanitize_text(data.get('name', ''), max_len=200)
    url = data.get('url', '').strip()
    if url and not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    description = sanitize_rich_text(data.get('description') or '', max_len=5000) or None

    if not name:
        return jsonify({'success': False, 'message': 'Nama link wajib diisi'}), 400

    if not url:
        return jsonify({'success': False, 'message': 'URL link wajib diisi'}), 400

    # Basic URL validation
    if not url.startswith(('http://', 'https://')):
        return jsonify({'success': False, 'message': 'URL harus dimulai dengan http:// atau https://'}), 400

    # 5. Buat link di database
    try:
        new_link = Link(
            name=name,
            url=url,
            description=description,
            course_id=course_id
        )
        db.session.add(new_link)
        db.session.commit()

        # 6. Kembalikan data link yang baru dibuat
        return jsonify({
            'success': True,
            'link': {
                'id': new_link.id,
                'name': new_link.name,
                'url': new_link.url,
                'description': new_link.description,
                'course_id': new_link.course_id
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to create link for course {course_id}: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Terjadi kesalahan server'}), 500


@content_bp.route('/link/<int:link_id>/archive', methods=['POST'])
@login_required
def api_archive_link(link_id):
    """Archive a link"""
    link = Link.query.get_or_404(link_id)
    course = Course.query.get(link.course_id)

    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)

    if course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    link.is_archived = True
    db.session.commit()

    return jsonify({'success': True, 'message': 'Link berhasil diarsipkan'})


@content_bp.route('/link/<int:link_id>/restore', methods=['POST'])
@login_required
def api_restore_link(link_id):
    """Restore an archived link"""
    link = Link.query.get_or_404(link_id)
    course = Course.query.get(link.course_id)

    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)

    if course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    link.is_archived = False
    db.session.commit()

    return jsonify({'success': True, 'message': 'Link berhasil dipulihkan'})


@content_bp.route('/link/<int:link_id>', methods=['DELETE'])
@login_required
def api_delete_link(link_id):
    """Soft-delete link ke Ruang TPS."""
    link = Link.query.get_or_404(link_id)
    course = Course.query.get(link.course_id)

    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)

    if course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    link.is_trashed = True
    link.trashed_at = _trash_now()
    db.session.commit()

    return jsonify({'success': True, 'message': 'Link dipindahkan ke Ruang TPS'})


@content_bp.route('/link/<int:link_id>', methods=['PUT'])
@login_required
def api_update_link(link_id):
    """Edit judul (name) & isi (url) sebuah link."""
    link = Link.query.get_or_404(link_id)
    course = Course.query.get(link.course_id)
    if not _verify_material_owner(course):
        return jsonify({'success': False, 'message': 'Tidak memiliki izin'}), 403
    data = request.get_json() or {}
    if 'name' in data:
        name = sanitize_text(data.get('name'), max_len=200)
        if not name:
            return jsonify({'success': False, 'message': 'Judul tidak boleh kosong'}), 400
        link.name = name
    if 'url' in data:
        url = (data.get('url') or '').strip()
        if not url:
            return jsonify({'success': False, 'message': 'URL tidak boleh kosong'}), 400
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        link.url = url[:500]
    if 'description' in data:
        link.description = sanitize_rich_text(data.get('description') or '', max_len=5000) or None
    db.session.commit()
    return jsonify({'success': True, 'message': 'Link diperbarui'})


# ─── Files ───────────────────────────────────────────────────────────────────

@content_bp.route('/courses/<int:course_id>/files', methods=['POST'])
@login_required
def api_create_file(course_id):
    if current_user.role != UserRole.GURU:
        return jsonify({'success': False, 'message': 'Hanya guru yang dapat mengunggah file'}), 403

    course = db.session.get(Course, course_id)
    if not course:
        return jsonify({'success': False, 'message': 'Mata pelajaran tidak ditemukan'}), 404

    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)

    if course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Anda tidak memiliki izin untuk mengunggah file di mata pelajaran ini'}), 403

    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'Tidak ada file yang diunggah'}), 400

    file = request.files['file']
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    start_date_str = request.form.get('start_date')
    end_date_str = request.form.get('end_date')

    if not name:
        return jsonify({'success': False, 'message': 'Nama file wajib diisi'}), 400

    if file.filename == '':
        return jsonify({'success': False, 'message': 'Tidak ada file yang dipilih'}), 400

    # Validate file extension
    if not allowed_file(file.filename):
        allowed = current_app.config.get('ALLOWED_EXTENSIONS', [])
        return jsonify({
            'success': False,
            'message': f'Tipe file tidak diizinkan. Hanya file dengan ekstensi: {", ".join(sorted(allowed))}'
        }), 400

    # Validate file size (check Content-Length header)
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to beginning

    max_size = current_app.config.get('MAX_CONTENT_LENGTH', 16777216)  # 16MB default
    if file_size > max_size:
        return jsonify({
            'success': False,
            'message': f'Ukuran file terlalu besar. Maksimal: {max_size // (1024 * 1024)}MB'
        }), 400

    start_date = None
    if start_date_str:
        try:
            start_date = datetime.fromisoformat(start_date_str)
        except ValueError:
            return jsonify({'success': False, 'message': 'Format tanggal mulai tidak valid'}), 400

    end_date = None
    if end_date_str:
        try:
            end_date = datetime.fromisoformat(end_date_str)
        except ValueError:
            return jsonify({'success': False, 'message': 'Format tanggal selesai tidak valid'}), 400

    if file:
        # Generate secure filename with UUID
        secure_name = generate_secure_filename(file.filename)

        # Create upload folder
        upload_folder = os.path.join(os.getcwd(), 'instance', 'uploads', str(course_id))
        os.makedirs(upload_folder, exist_ok=True)

        # Save file with secure name
        file_path = os.path.join(upload_folder, secure_name)
        file.save(file_path)

        new_file = File(
            name=name,
            description=description,
            filename=secure_name,
            course_id=course_id,
            start_date=start_date,
            end_date=end_date
        )
        db.session.add(new_file)
        db.session.commit()

        return jsonify({
            'success': True,
            'file': {
                'id': new_file.id,
                'name': new_file.name,
                'description': new_file.description,
                'filename': new_file.filename,
                'course_id': new_file.course_id,
                'start_date': new_file.start_date.isoformat() if new_file.start_date else None,
                'end_date': new_file.end_date.isoformat() if new_file.end_date else None,
            }
        }), 201

    return jsonify({'success': False, 'message': 'Terjadi kesalahan saat mengunggah file'}), 500


@content_bp.route('/file/<int:file_id>', methods=['PUT'])
@login_required
def api_update_file(file_id):
    """Edit judul (name) & deskripsi (isi) sebuah berkas."""
    f = File.query.get_or_404(file_id)
    course = Course.query.get(f.course_id)
    if not _verify_material_owner(course):
        return jsonify({'success': False, 'message': 'Tidak memiliki izin'}), 403
    data = request.get_json() or {}
    if 'name' in data:
        name = sanitize_text(data.get('name'), max_len=200)
        if not name:
            return jsonify({'success': False, 'message': 'Judul tidak boleh kosong'}), 400
        f.name = name
    if 'description' in data:
        f.description = sanitize_rich_text(data.get('description') or '', max_len=5000) or None
    db.session.commit()
    return jsonify({'success': True, 'message': 'Berkas diperbarui'})


@content_bp.route('/file/<int:file_id>/archive', methods=['POST'])
@login_required
def api_archive_file(file_id):
    """API endpoint untuk mengarsipkan file"""
    file = db.session.get(File, file_id)
    if not file:
        return jsonify({'success': False, 'message': 'File tidak ditemukan'}), 404

    if file.course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Anda tidak memiliki izin'}), 403

    file.is_archived = True
    db.session.commit()

    return jsonify({'success': True, 'message': 'File berhasil diarsipkan'})


@content_bp.route('/file/<int:file_id>/restore', methods=['POST'])
@login_required
def api_restore_file(file_id):
    """API endpoint untuk memulihkan file dari arsip"""
    file = db.session.get(File, file_id)
    if not file:
        return jsonify({'success': False, 'message': 'File tidak ditemukan'}), 404

    if file.course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Anda tidak memiliki izin'}), 403

    file.is_archived = False
    db.session.commit()

    return jsonify({'success': True, 'message': 'File berhasil dipulihkan'})


@content_bp.route('/file/<int:file_id>', methods=['DELETE'])
@login_required
def api_delete_file(file_id):
    """Soft-delete berkas ke Ruang TPS."""
    file = db.session.get(File, file_id)
    if not file:
        return jsonify({'success': False, 'message': 'File tidak ditemukan'}), 404
    if file.course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Anda tidak memiliki izin'}), 403

    file.is_trashed = True
    file.trashed_at = _trash_now()
    db.session.commit()
    return jsonify({'success': True, 'message': 'Berkas dipindahkan ke Ruang TPS'})


# ─── Content reorder / move ──────────────────────────────────────────────────

@content_bp.route('/courses/<int:course_id>/content/reorder', methods=['POST'])
@login_required
def api_reorder_content(course_id):
    if current_user.role != UserRole.GURU:
        return jsonify({'success': False, 'message': 'Hanya guru yang dapat mengatur urutan'}), 403

    course = db.session.get(Course, course_id)
    if not course or course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Anda tidak memiliki izin'}), 403

    data = request.get_json() or {}
    items = data.get('items', [])

    try:
        for item in items:
            item_id = item.get('id')
            item_type = item.get('type')
            order = item.get('order', 0)
            folder_id = item.get('folder_id')  # None means root level

            if item_type == 'quiz':
                obj = db.session.get(Quiz, item_id)
            elif item_type == 'assignment':
                obj = db.session.get(Assignment, item_id)
            elif item_type == 'file':
                obj = db.session.get(File, item_id)
            elif item_type == 'link':
                obj = db.session.get(Link, item_id)
            elif item_type == 'folder':
                obj = db.session.get(ContentFolder, item_id)
            else:
                continue

            if obj and hasattr(obj, 'order'):
                obj.order = order
            if obj and item_type != 'folder' and hasattr(obj, 'folder_id'):
                obj.folder_id = folder_id
            if obj and item_type == 'folder' and hasattr(obj, 'parent_folder_id'):
                obj.parent_folder_id = folder_id

        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to reorder content for course {course_id}: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Gagal menyimpan urutan'}), 500


@content_bp.route('/courses/<int:course_id>/content/move-to-folder', methods=['POST'])
@login_required
def api_move_to_folder(course_id):
    if current_user.role != UserRole.GURU:
        return jsonify({'success': False, 'message': 'Hanya guru yang dapat memindahkan konten'}), 403

    course = db.session.get(Course, course_id)
    if not course or course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Anda tidak memiliki izin'}), 403

    data = request.get_json() or {}
    item_id = data.get('item_id')
    item_type = data.get('item_type')
    folder_id = data.get('folder_id')  # None to move to root

    if folder_id:
        folder = db.session.get(ContentFolder, folder_id)
        if not folder or folder.course_id != course_id:
            return jsonify({'success': False, 'message': 'Folder tidak valid'}), 400

    if item_type == 'quiz':
        obj = db.session.get(Quiz, item_id)
    elif item_type == 'assignment':
        obj = db.session.get(Assignment, item_id)
    elif item_type == 'file':
        obj = db.session.get(File, item_id)
    elif item_type == 'link':
        obj = db.session.get(Link, item_id)
    else:
        return jsonify({'success': False, 'message': 'Tipe konten tidak valid'}), 400

    if not obj:
        return jsonify({'success': False, 'message': 'Konten tidak ditemukan'}), 404

    obj.folder_id = folder_id
    db.session.commit()

    return jsonify({'success': True})


@content_bp.route('/materials/<material_type>/<int:material_id>/move', methods=['POST'])
@login_required
def api_move_material(material_type, material_id):
    """Move a material (quiz, assignment, file, link) to a folder"""
    data = request.get_json() or {}
    folder_id = data.get('folder_id')
    order = data.get('order', 0)

    # Map material types
    material_map = {
        'quiz': Quiz,
        'assignment': Assignment,
        'file': File,
        'link': Link
    }

    if material_type not in material_map:
        return jsonify({'success': False, 'message': 'Tipe material tidak valid'}), 400

    Material = material_map[material_type]
    material = Material.query.get_or_404(material_id)

    # Get course and verify permissions
    course_id = material.course_id
    course = Course.query.get(course_id)

    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)

    if course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    # Verify folder belongs to same course
    if folder_id:
        target_folder = ContentFolder.query.get(folder_id)
        if not target_folder or target_folder.course_id != course_id:
            return jsonify({'success': False, 'message': 'Target folder tidak valid'}), 400

    # Update material
    material.folder_id = folder_id
    if order >= 0:
        material.order = order

    db.session.commit()

    return jsonify({'success': True})


@content_bp.route('/courses/<int:course_id>/materials/reorder', methods=['POST'])
@login_required
def api_reorder_materials(course_id):
    """Reorder materials in a course"""
    course = Course.query.get_or_404(course_id)
    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)

    if course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    data = request.get_json() or {}
    order_list = data.get('order', [])

    for item in order_list:
        material_id = item.get('id')
        material_type = item.get('type')
        order = item.get('order', 0)

        if material_type == 'quiz':
            quiz = Quiz.query.get(material_id)
            if quiz and quiz.course_id == course_id:
                quiz.order = order
        elif material_type == 'assignment':
            assignment = Assignment.query.get(material_id)
            if assignment and assignment.course_id == course_id:
                assignment.order = order
        elif material_type == 'file':
            file = File.query.get(material_id)
            if file and file.course_id == course_id:
                file.order = order
        elif material_type == 'link':
            link = Link.query.get(material_id)
            if link and link.course_id == course_id:
                link.order = order

    db.session.commit()
    return jsonify({'success': True})


# ─── Folder tree management ──────────────────────────────────────────────────

@content_bp.route('/courses/<int:course_id>/folders', methods=['GET'])
@login_required
def api_get_course_folders(course_id):
    """Get all folders in a course with hierarchical structure"""
    course = db.session.get(Course, course_id)
    if not course:
        abort(404)

    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)

    # Get all folders (sorted by order)
    folders = ContentFolder.query.filter_by(course_id=course_id).order_by(ContentFolder.order).all()

    # Build hierarchical structure
    def build_folder_tree(parent_id=None):
        items = []
        for folder in folders:
            if folder.parent_folder_id == parent_id:
                item = folder.to_dict(include_children=False)
                item['children'] = build_folder_tree(folder.id)
                items.append(item)
        return items

    folder_tree = build_folder_tree()

    return jsonify({
        'success': True,
        'folders': folder_tree
    })


@content_bp.route('/courses/<int:course_id>/folders', methods=['POST'])
@login_required
def api_create_folder(course_id):
    """Create a new folder in a course"""
    course = db.session.get(Course, course_id)
    if not course:
        abort(404)

    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)

    # Only teacher can create folders (not admin or super admin)
    if course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Anda tidak memiliki izin untuk membuat folder'}), 403

    data = request.get_json() or {}
    name = sanitize_text(data.get('name', ''), max_len=200).strip()
    parent_folder_id = data.get('parent_folder_id')

    if not name:
        return jsonify({'success': False, 'message': 'Nama folder wajib diisi'}), 400

    # Verify parent folder belongs to same course
    if parent_folder_id:
        parent_folder = ContentFolder.query.get(parent_folder_id)
        if not parent_folder or parent_folder.course_id != course_id:
            return jsonify({'success': False, 'message': 'Parent folder tidak valid'}), 400

    # Get the next order number
    max_order = db.session.query(db.func.max(ContentFolder.order)).filter(
        ContentFolder.course_id == course_id,
        ContentFolder.parent_folder_id == parent_folder_id
    ).scalar() or 0

    folder = ContentFolder(
        name=name,
        course_id=course_id,
        parent_folder_id=parent_folder_id,
        order=max_order + 1
    )

    db.session.add(folder)
    db.session.commit()

    log_activity(current_user.id, f"Created folder: {name} in course {course.name}")

    return jsonify({
        'success': True,
        'folder': folder.to_dict(include_children=True)
    }), 201


@content_bp.route('/folders/<int:folder_id>', methods=['PUT'])
@login_required
def api_update_folder(folder_id):
    """Update folder (rename, reorder)"""
    folder = ContentFolder.query.get_or_404(folder_id)
    course = Course.query.get(folder.course_id)

    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)

    # Only teacher can update folder
    if course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    data = request.get_json() or {}

    if 'name' in data:
        name = sanitize_text(data['name'], max_len=200).strip()
        if name:
            folder.name = name

    if 'order' in data:
        try:
            folder.order = int(data['order'])
        except (ValueError, TypeError):
            pass

    db.session.commit()

    return jsonify({
        'success': True,
        'folder': folder.to_dict(include_children=False)
    })


@content_bp.route('/folders/<int:folder_id>', methods=['DELETE'])
@login_required
def api_delete_folder(folder_id):
    """Delete a folder and move its contents to parent"""
    folder = ContentFolder.query.get_or_404(folder_id)
    course = Course.query.get(folder.course_id)

    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)

    # Only teacher can delete folder
    if course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    folder_id_val = folder.id
    parent_id = folder.parent_folder_id

    # Move all child folders to parent
    child_folders = ContentFolder.query.filter_by(parent_folder_id=folder_id_val).all()
    for child in child_folders:
        child.parent_folder_id = parent_id

    # Move all materials to parent folder
    Quiz.query.filter_by(folder_id=folder_id_val).update({Quiz.folder_id: parent_id})
    Assignment.query.filter_by(folder_id=folder_id_val).update({Assignment.folder_id: parent_id})
    File.query.filter_by(folder_id=folder_id_val).update({File.folder_id: parent_id})
    Link.query.filter_by(folder_id=folder_id_val).update({Link.folder_id: parent_id})

    db.session.delete(folder)
    db.session.commit()

    log_activity(current_user.id, f"Deleted folder {folder_id_val}")

    return jsonify({'success': True})


@content_bp.route('/courses/<int:course_id>/folders/reorder', methods=['POST'])
@login_required
def api_reorder_folders(course_id):
    """Reorder folders in a course"""
    course = Course.query.get_or_404(course_id)
    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)

    if course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    data = request.get_json() or {}
    order_list = data.get('order', [])

    for item in order_list:
        folder_id = item.get('id')
        order = item.get('order', 0)

        folder = ContentFolder.query.get(folder_id)
        if folder and folder.course_id == course_id:
            folder.order = order

    db.session.commit()
    return jsonify({'success': True})


@content_bp.route('/folders/<int:folder_id>/move', methods=['PUT'])
@login_required
def api_move_folder(folder_id):
    """Move a folder to a parent folder"""
    data = request.get_json() or {}
    new_parent_id = data.get('parent_folder_id')

    folder = ContentFolder.query.get_or_404(folder_id)
    course = Course.query.get(folder.course_id)

    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)

    if course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    # Prevent moving folder into itself or its descendants
    if new_parent_id:
        child_ids = [f.id for f in ContentFolder.query.filter_by(parent_folder_id=folder_id).all()]
        if new_parent_id in child_ids or new_parent_id == folder_id:
            return jsonify({'success': False, 'message': 'Invalid parent folder'}), 400

    folder.parent_folder_id = new_parent_id
    db.session.commit()

    log_activity(current_user.id, f"Moved folder {folder_id} to parent {new_parent_id}")

    return jsonify({'success': True})


# ─── Cross-course import ──────────────────────────────────────────────────────

@content_bp.route('/courses/<int:course_id>/importable-materials', methods=['GET'])
@login_required
def api_get_importable_materials(course_id):
    """Mendapatkan daftar materi dari kelas lain yang dapat diimpor"""
    course = db.session.get(Course, course_id)
    if not course:
        return jsonify({'success': False, 'message': 'Kelas tidak ditemukan'}), 404

    # Security check: must be the teacher of this course
    if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    # We only import non-archived and non-trashed items
    quizzes = Quiz.query.filter_by(course_id=course_id, is_archived=False, is_trashed=False).all()
    assignments = Assignment.query.filter_by(course_id=course_id, is_trashed=False).filter(Assignment.status != AssignmentStatus.ARCHIVED).all()
    files = File.query.filter_by(course_id=course_id, is_archived=False, is_trashed=False).all()
    links = Link.query.filter_by(course_id=course_id, is_archived=False, is_trashed=False).all()

    return jsonify({
        'success': True,
        'quizzes': [{'id': q.id, 'name': q.name, 'points': q.points} for q in quizzes],
        'assignments': [{'id': a.id, 'title': a.title, 'max_score': a.max_score} for a in assignments],
        'files': [{'id': f.id, 'name': f.name, 'filename': f.filename} for f in files],
        'links': [{'id': l.id, 'name': l.name, 'url': l.url} for l in links]
    })


@content_bp.route('/courses/<int:course_id>/import', methods=['POST'])
@login_required
def api_import_materials(course_id):
    """Mengimpor materi terpilih ke kelas tujuan (course_id)"""
    from app.quiz.models import Question, Option, QuestionBloomTaxonomy

    dest_course = db.session.get(Course, course_id)
    if not dest_course:
        return jsonify({'success': False, 'message': 'Kelas tujuan tidak ditemukan'}), 404

    # Verify destination course permission
    if dest_course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    data = request.get_json() or {}
    source_course_id = data.get('source_course_id')
    items = data.get('items', [])  # List of {type: 'quiz'|'assignment'|'file'|'link', id: int}

    if not source_course_id:
        return jsonify({'success': False, 'message': 'Kelas asal wajib ditentukan'}), 400

    source_course = db.session.get(Course, source_course_id)
    if not source_course:
        return jsonify({'success': False, 'message': 'Kelas asal tidak ditemukan'}), 404

    # Verify source course permission
    if source_course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    try:
        imported_count = 0
        for item in items:
            item_type = item.get('type')
            item_id = item.get('id')

            if item_type == 'quiz':
                quiz = Quiz.query.filter_by(id=item_id, course_id=source_course_id).first()
                if quiz:
                    # Duplicate Quiz
                    new_quiz = Quiz(
                        name=quiz.name,
                        description=quiz.description,
                        theme_color=quiz.theme_color,
                        bg_pattern=quiz.bg_pattern,
                        font_question=quiz.font_question,
                        font_answer=quiz.font_answer,
                        course_id=course_id,
                        grade_type=quiz.grade_type,
                        status=quiz.status,
                        points=quiz.points,
                        duration=quiz.duration,
                        max_attempts=quiz.max_attempts,
                        is_quiz=quiz.is_quiz,
                        collect_email=quiz.collect_email,
                        shuffle_questions=quiz.shuffle_questions,
                        confirmation_message=quiz.confirmation_message,
                        default_points=quiz.default_points,
                        required_by_default=quiz.required_by_default,
                        questions_per_page=quiz.questions_per_page,
                        bg_opacity=quiz.bg_opacity
                    )
                    db.session.add(new_quiz)
                    db.session.flush()  # Flush to get new_quiz.id

                    # Duplicate Questions & Options
                    questions = Question.query.filter_by(quiz_id=quiz.id).all()
                    for q in questions:
                        new_q = Question(
                            question_text=q.question_text,
                            question_type=q.question_type,
                            quiz_id=new_quiz.id,
                            order=q.order,
                            description=q.description,
                            image=q.image,
                            is_required=q.is_required,
                            points=q.points,
                            max_file_size=q.max_file_size,
                            allowed_file_types=q.allowed_file_types
                        )
                        db.session.add(new_q)
                        db.session.flush()

                        # Duplicate bloom taxonomy if exists
                        if q.bloom_taxonomy:
                            new_bt = QuestionBloomTaxonomy(
                                question_id=new_q.id,
                                bloom_level=q.bloom_taxonomy.bloom_level,
                                bloom_description=q.bloom_taxonomy.bloom_description
                            )
                            db.session.add(new_bt)

                        # Duplicate Options
                        options = Option.query.filter_by(question_id=q.id).all()
                        for opt in options:
                            new_opt = Option(
                                option_text=opt.option_text,
                                is_correct=opt.is_correct,
                                question_id=new_q.id,
                                order=opt.order
                            )
                            db.session.add(new_opt)
                    imported_count += 1

            elif item_type == 'assignment':
                assignment = Assignment.query.filter_by(id=item_id, course_id=source_course_id).first()
                if assignment:
                    new_assignment = Assignment(
                        title=assignment.title,
                        description=assignment.description,
                        course_id=course_id,
                        due_date=assignment.due_date,
                        max_score=assignment.max_score,
                        status=assignment.status
                    )
                    db.session.add(new_assignment)
                    imported_count += 1

            elif item_type == 'file':
                file_item = File.query.filter_by(id=item_id, course_id=source_course_id).first()
                if file_item:
                    # Duplicate DB record
                    new_file = File(
                        name=file_item.name,
                        description=file_item.description,
                        filename=file_item.filename,
                        course_id=course_id
                    )
                    db.session.add(new_file)

                    # Copy physical file
                    src_dir = os.path.join(os.getcwd(), 'instance', 'uploads', str(source_course_id))
                    dest_dir = os.path.join(os.getcwd(), 'instance', 'uploads', str(course_id))
                    os.makedirs(dest_dir, exist_ok=True)

                    src_path = os.path.join(src_dir, file_item.filename)
                    dest_path = os.path.join(dest_dir, file_item.filename)
                    if os.path.exists(src_path):
                        shutil.copy2(src_path, dest_path)
                    imported_count += 1

            elif item_type == 'link':
                link = Link.query.filter_by(id=item_id, course_id=source_course_id).first()
                if link:
                    new_link = Link(
                        name=link.name,
                        url=link.url,
                        description=link.description,
                        course_id=course_id
                    )
                    db.session.add(new_link)
                    imported_count += 1

        db.session.commit()
        return jsonify({'success': True, 'message': f'Berhasil mengimpor {imported_count} materi.'})

    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to import materials: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Terjadi kesalahan server saat mengimpor'}), 500
