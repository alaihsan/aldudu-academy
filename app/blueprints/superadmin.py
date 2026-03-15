from flask import Blueprint, render_template, request, jsonify, abort
from flask_login import login_required, current_user
from sqlalchemy import func
from app.extensions import db
from app.models import (
    User, UserRole, School, SchoolStatus,
    Ticket, TicketMessage, TicketStatus,
    ActivityLog, Issue, IssueStatus
)
from app.helpers import get_jakarta_now, sanitize_text
from app.services.email_service import send_school_approved_email, send_ticket_update_email, send_email
from app.services.ticket_service import transition_status, TicketStatus as TStat
from app.middleware import invalidate_school_cache

superadmin_bp = Blueprint('superadmin', __name__, url_prefix='/superadmin')


@superadmin_bp.before_request
@login_required
def superadmin_required():
    if current_user.role != UserRole.SUPER_ADMIN:
        abort(403)


# ─── Page Routes ────────────────────────────────────

@superadmin_bp.route('/dashboard')
def dashboard():
    stats = {
        'total_schools': School.query.count(),
        'active_schools': School.query.filter_by(status=SchoolStatus.ACTIVE).count(),
        'pending_schools': School.query.filter_by(status=SchoolStatus.PENDING).count(),
        'total_users': User.query.filter(User.role != UserRole.SUPER_ADMIN).count(),
        'open_tickets': Ticket.query.filter(
            Ticket.status.in_([TicketStatus.OPEN, TicketStatus.IN_QUEUE, TicketStatus.IN_PROGRESS])
        ).count(),
        'total_tickets': Ticket.query.count(),
        'open_issues': Issue.query.filter(
            Issue.status.in_([IssueStatus.OPEN, IssueStatus.IN_PROGRESS])
        ).count(),
        'total_issues': Issue.query.count(),
    }
    recent_logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(20).all()
    return render_template('superadmin/dashboard.html', stats=stats, recent_logs=recent_logs)


@superadmin_bp.route('/schools')
def schools():
    return render_template('superadmin/schools.html')


@superadmin_bp.route('/tickets')
def tickets():
    return render_template('superadmin/tickets.html')


@superadmin_bp.route('/tickets/<int:ticket_id>')
def ticket_detail(ticket_id):
    ticket = db.session.get(Ticket, ticket_id)
    if not ticket:
        abort(404)
    return render_template('superadmin/ticket_detail.html', ticket=ticket)


# ─── API Routes ─────────────────────────────────────

@superadmin_bp.route('/api/schools', methods=['GET'])
def api_get_schools():
    status_filter = request.args.get('status')
    query = School.query

    if status_filter:
        try:
            status = SchoolStatus(status_filter)
            query = query.filter_by(status=status)
        except ValueError:
            pass

    schools = query.order_by(School.created_at.desc()).all()
    return jsonify({'success': True, 'schools': [s.to_dict() for s in schools]})


@superadmin_bp.route('/api/schools/<int:school_id>/approve', methods=['POST'])
def api_approve_school(school_id):
    school = db.session.get(School, school_id)
    if not school:
        return jsonify({'success': False, 'message': 'Sekolah tidak ditemukan'}), 404

    if school.status not in (SchoolStatus.PENDING, SchoolStatus.VERIFIED):
        return jsonify({'success': False, 'message': 'Sekolah sudah aktif atau sedang disuspend'}), 400

    is_bypass = school.status == SchoolStatus.PENDING
    school.status = SchoolStatus.ACTIVE
    school.approved_at = get_jakarta_now()

    # Jika bypass dari PENDING, tandai email admin sebagai verified
    admin_user = User.query.filter_by(school_id=school.id, role=UserRole.ADMIN).first()
    if is_bypass and admin_user:
        admin_user.email_verified = True

    db.session.commit()
    invalidate_school_cache(school.slug)

    if admin_user:
        send_school_approved_email(admin_user, school)

    msg = 'Sekolah disetujui (bypass verifikasi email)' if is_bypass else 'Sekolah berhasil disetujui'
    return jsonify({'success': True, 'school': school.to_dict(), 'message': msg})


@superadmin_bp.route('/api/schools/<int:school_id>/suspend', methods=['POST'])
def api_suspend_school(school_id):
    school = db.session.get(School, school_id)
    if not school:
        return jsonify({'success': False, 'message': 'Sekolah tidak ditemukan'}), 404

    school.status = SchoolStatus.SUSPENDED
    db.session.commit()

    invalidate_school_cache(school.slug)

    return jsonify({'success': True, 'school': school.to_dict()})


@superadmin_bp.route('/api/schools/<int:school_id>/reactivate', methods=['POST'])
def api_reactivate_school(school_id):
    school = db.session.get(School, school_id)
    if not school:
        return jsonify({'success': False, 'message': 'Sekolah tidak ditemukan'}), 404

    school.status = SchoolStatus.ACTIVE
    db.session.commit()

    invalidate_school_cache(school.slug)

    return jsonify({'success': True, 'school': school.to_dict()})


@superadmin_bp.route('/api/tickets', methods=['GET'])
def api_get_tickets():
    status_filter = request.args.get('status')
    page = request.args.get('page', 1, type=int)
    per_page = 15

    query = Ticket.query

    if status_filter == 'active':
        query = query.filter(Ticket.status.in_([
            TicketStatus.OPEN, TicketStatus.IN_QUEUE,
            TicketStatus.IN_PROGRESS, TicketStatus.WAITING_USER
        ]))
    elif status_filter == 'resolved':
        query = query.filter(Ticket.status.in_([TicketStatus.RESOLVED, TicketStatus.CLOSED]))
    elif status_filter:
        try:
            status = TicketStatus(status_filter)
            query = query.filter_by(status=status)
        except ValueError:
            pass

    # Priority ordering: URGENT > HIGH > MEDIUM > LOW, then by created_at
    priority_order = func.field(Ticket.priority, 'urgent', 'high', 'medium', 'low')
    pagination = query.order_by(priority_order, Ticket.created_at.asc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'success': True,
        'tickets': [t.to_dict() for t in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
    })


@superadmin_bp.route('/api/tickets/<int:ticket_id>', methods=['GET'])
def api_get_ticket(ticket_id):
    ticket = db.session.get(Ticket, ticket_id)
    if not ticket:
        return jsonify({'success': False, 'message': 'Ticket tidak ditemukan'}), 404

    return jsonify({'success': True, 'ticket': ticket.to_dict(include_messages=True)})


@superadmin_bp.route('/api/tickets/<int:ticket_id>/reply', methods=['POST'])
def api_reply_ticket(ticket_id):
    ticket = db.session.get(Ticket, ticket_id)
    if not ticket:
        return jsonify({'success': False, 'message': 'Ticket tidak ditemukan'}), 404

    data = request.get_json() or {}
    content = sanitize_text(data.get('content', ''), max_len=2000)
    is_internal = data.get('is_internal', False)

    if not content:
        return jsonify({'success': False, 'message': 'Pesan tidak boleh kosong'}), 400

    message = TicketMessage(
        ticket_id=ticket.id,
        user_id=current_user.id,
        content=content,
        is_internal=bool(is_internal),
    )
    db.session.add(message)
    db.session.commit()

    # Send email notification to user (only if not internal)
    if not is_internal:
        send_ticket_update_email(ticket, content)

    return jsonify({'success': True, 'message': message.to_dict()})


@superadmin_bp.route('/api/tickets/<int:ticket_id>/status', methods=['POST'])
def api_update_ticket_status(ticket_id):
    ticket = db.session.get(Ticket, ticket_id)
    if not ticket:
        return jsonify({'success': False, 'message': 'Ticket tidak ditemukan'}), 404

    data = request.get_json() or {}
    new_status_str = data.get('status', '')

    try:
        new_status = TicketStatus(new_status_str)
    except ValueError:
        return jsonify({'success': False, 'message': 'Status tidak valid'}), 400

    success, msg = transition_status(ticket, new_status, current_user)
    if not success:
        return jsonify({'success': False, 'message': msg}), 400

    # Notify user
    is_resolved = new_status in (TicketStatus.RESOLVED, TicketStatus.CLOSED)
    send_ticket_update_email(ticket, f'Status diperbarui menjadi: {new_status.value}', is_resolved)

    return jsonify({'success': True, 'ticket': ticket.to_dict()})


# ─── Issues Routes ─────────────────────────────────

@superadmin_bp.route('/issues')
def issues():
    return render_template('superadmin/issues.html')


@superadmin_bp.route('/api/issues', methods=['GET'])
def api_get_issues():
    status_filter = request.args.get('status')
    query = Issue.query

    if status_filter == 'active':
        query = query.filter(Issue.status.in_([IssueStatus.OPEN, IssueStatus.IN_PROGRESS]))
    elif status_filter == 'resolved':
        query = query.filter(Issue.status.in_([IssueStatus.RESOLVED, IssueStatus.CLOSED]))

    issues = query.order_by(Issue.created_at.desc()).all()
    result = []
    for issue in issues:
        d = issue.to_dict()
        d['school_name'] = issue.school.name if issue.school else '-'
        result.append(d)

    return jsonify({'success': True, 'issues': result})


@superadmin_bp.route('/api/issues/<int:issue_id>/status', methods=['POST'])
def api_update_issue_status(issue_id):
    issue = db.session.get(Issue, issue_id)
    if not issue:
        return jsonify({'success': False, 'message': 'Laporan tidak ditemukan'}), 404

    data = request.get_json() or {}
    new_status_str = data.get('status', '').upper()

    try:
        issue.status = IssueStatus[new_status_str]
    except KeyError:
        return jsonify({'success': False, 'message': 'Status tidak valid'}), 400

    db.session.commit()
    return jsonify({'success': True, 'issue': issue.to_dict()})


@superadmin_bp.route('/api/test-email', methods=['POST'])
def api_test_email():
    data = request.get_json() or {}
    recipient = data.get('email', current_user.email)
    ok = send_email(
        subject='Test Email - Aldudu Academy',
        recipients=[recipient],
        html_body=(
            '<div style="font-family:sans-serif;padding:20px">'
            '<h2 style="color:#0282c6">Email Berhasil! ✅</h2>'
            '<p>Konfigurasi Mailtrap berfungsi dengan baik.</p>'
            f'<p>Dikirim ke: <strong>{recipient}</strong></p>'
            '</div>'
        ),
    )
    if ok:
        return jsonify({'success': True, 'message': f'Email test berhasil dikirim ke {recipient}'})
    return jsonify({'success': False, 'message': 'Gagal mengirim email. Cek kredensial Mailtrap di .env.'}), 500
