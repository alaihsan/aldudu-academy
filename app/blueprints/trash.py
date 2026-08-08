"""
Ruang TPS (Tempat Pembuangan Sementara) per kelas.

Konsep:
- Hapus dari daftar materi = soft-delete (is_trashed=True, trashed_at=now).
- Item di TPS bisa di-Restore (dikembalikan ke lokasi asalnya: kelas + folder)
  atau Hapus Permanen (dihilangkan dari database).
- Auto-purge: setiap kali halaman TPS dibuka, item yang sudah > 30 hari di TPS
  dihapus permanen otomatis (lazy cleanup — tidak perlu cron/worker terpisah).
"""
import os
import logging
from datetime import timedelta
from flask import Blueprint, render_template, jsonify, abort, current_app
from flask_login import login_required, current_user
from app.core.extensions import db
from app.models import Course, Quiz, Assignment, File, Link, ContentFolder
from app.helpers import get_jakarta_now
from app.core.authorization import get_school_id_or_abort, verify_course_in_school

logger = logging.getLogger(__name__)

trash_bp = Blueprint('trash', __name__)

TRASH_RETENTION_DAYS = 30

# Tipe materi yang ditampung TPS → Model + label
TRASH_MODELS = {
    'quiz': (Quiz, 'Kuis', 'name'),
    'assignment': (Assignment, 'Tugas', 'title'),
    'file': (File, 'Berkas', 'name'),
    'link': (Link, 'Link', 'name'),
}


def _verify_owner(course):
    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)
    return course.teacher_id == current_user.id


def _now_naive():
    """Now sebagai datetime naive (kolom DB juga naive)."""
    n = get_jakarta_now()
    return n.replace(tzinfo=None) if getattr(n, 'tzinfo', None) else n


def _purge_expired(course_id):
    """Hapus permanen item yang sudah > 30 hari di TPS milik kelas ini.

    Dipanggil 'lazy' saat halaman TPS dibuka. Aman & idempotent.
    """
    cutoff = _now_naive() - timedelta(days=TRASH_RETENTION_DAYS)
    total = 0
    for Model, _label, _name_attr in TRASH_MODELS.values():
        expired = (Model.query
                   .filter_by(course_id=course_id, is_trashed=True)
                   .filter(Model.trashed_at != None, Model.trashed_at < cutoff)
                   .all())
        for obj in expired:
            # Bila File punya berkas fisik, hapus juga dari disk
            if Model is File:
                _delete_file_from_disk(obj)
            db.session.delete(obj)
            total += 1
    if total:
        db.session.commit()
        logger.info(f"[TPS] Auto-purged {total} item(s) > {TRASH_RETENTION_DAYS} hari dari kelas {course_id}")
    return total


def _delete_file_from_disk(file_obj):
    """Hapus berkas fisik dari upload folder (best-effort)."""
    try:
        upload_folder = current_app.config.get('UPLOAD_FOLDER', '')
        if upload_folder and file_obj.filename:
            path = os.path.join(upload_folder, file_obj.filename)
            if os.path.exists(path):
                os.remove(path)
    except Exception as e:
        logger.warning(f"[TPS] Gagal hapus file fisik {file_obj.filename}: {e}")


def _folder_path(folder_id, course):
    """Bangun path folder seperti 'Folder A › Sub Folder'. None = root kelas."""
    if not folder_id:
        return None
    parts = []
    cur = ContentFolder.query.get(folder_id)
    while cur and cur.course_id == course.id and len(parts) < 8:
        parts.insert(0, cur.name)
        cur = ContentFolder.query.get(cur.parent_folder_id) if getattr(cur, 'parent_folder_id', None) else None
    return ' › '.join(parts) if parts else None


def _build_item(obj, type_key, label, name_attr, course):
    folder_id = getattr(obj, 'folder_id', None)
    folder_path = _folder_path(folder_id, course)
    days_left = TRASH_RETENTION_DAYS
    if obj.trashed_at:
        ta = obj.trashed_at
        if getattr(ta, 'tzinfo', None):
            ta = ta.replace(tzinfo=None)
        elapsed = (_now_naive() - ta).days
        days_left = max(0, TRASH_RETENTION_DAYS - elapsed)
    return {
        'id': obj.id,
        'type': type_key,
        'type_label': label,
        'title': getattr(obj, name_attr, 'Untitled'),
        'trashed_at': obj.trashed_at.strftime('%d %B %Y, %H:%M') if obj.trashed_at else '-',
        'days_left': days_left,
        'folder_id': folder_id,
        'origin_label': (
            f"Kelas: {course.name}"
            + (f" › Folder: {folder_path}" if folder_path else " › (Tanpa folder)")
        ),
    }


@trash_bp.route('/kelas/<int:course_id>/tps')
@login_required
def course_tps(course_id):
    course = db.session.get(Course, course_id)
    if course is None:
        abort(404)
    if not _verify_owner(course):
        abort(403, description='Hanya guru pemilik kelas yang dapat membuka Ruang TPS.')

    # Lazy auto-purge sebelum menampilkan
    purged = _purge_expired(course_id)

    items = []
    for type_key, (Model, label, name_attr) in TRASH_MODELS.items():
        rows = (Model.query
                .filter_by(course_id=course_id, is_trashed=True)
                .order_by(Model.trashed_at.desc())
                .all())
        for r in rows:
            items.append(_build_item(r, type_key, label, name_attr, course))

    # urutkan: paling baru dibuang di atas
    items.sort(key=lambda x: x['trashed_at'] if x['trashed_at'] != '-' else '', reverse=True)

    return render_template('course_tps.html',
                           course=course,
                           items=items,
                           retention_days=TRASH_RETENTION_DAYS,
                           purged_now=purged)


@trash_bp.route('/api/trash/<type_key>/<int:item_id>/restore', methods=['POST'])
@login_required
def api_restore(type_key, item_id):
    if type_key not in TRASH_MODELS:
        return jsonify({'success': False, 'message': 'Tipe tidak valid'}), 400
    Model, label, _ = TRASH_MODELS[type_key]
    obj = Model.query.get(item_id)
    if not obj:
        return jsonify({'success': False, 'message': f'{label} tidak ditemukan'}), 404
    course = Course.query.get(obj.course_id)
    if not _verify_owner(course):
        return jsonify({'success': False, 'message': 'Tidak memiliki izin'}), 403

    # Restore: folder_id tetap (otomatis kembali ke lokasi asal). Jika folder
    # sudah tidak ada, set ke root (None) supaya tidak orphan.
    if getattr(obj, 'folder_id', None):
        fol = ContentFolder.query.get(obj.folder_id)
        if not fol or fol.course_id != course.id:
            obj.folder_id = None

    obj.is_trashed = False
    obj.trashed_at = None
    db.session.commit()

    folder_path = _folder_path(getattr(obj, 'folder_id', None), course)
    location = f"Kelas: {course.name}" + (f" › Folder: {folder_path}" if folder_path else " › (Tanpa folder)")
    return jsonify({'success': True, 'message': f'{label} berhasil dikembalikan', 'location': location})


@trash_bp.route('/api/trash/<type_key>/<int:item_id>/permanent', methods=['DELETE'])
@login_required
def api_permanent_delete(type_key, item_id):
    if type_key not in TRASH_MODELS:
        return jsonify({'success': False, 'message': 'Tipe tidak valid'}), 400
    Model, label, _ = TRASH_MODELS[type_key]
    obj = Model.query.get(item_id)
    if not obj:
        return jsonify({'success': False, 'message': f'{label} tidak ditemukan'}), 404
    course = Course.query.get(obj.course_id)
    if not _verify_owner(course):
        return jsonify({'success': False, 'message': 'Tidak memiliki izin'}), 403

    if Model is File:
        _delete_file_from_disk(obj)
    db.session.delete(obj)
    db.session.commit()
    return jsonify({'success': True, 'message': f'{label} dihapus permanen'})
