from flask import Blueprint, request, jsonify, render_template, g, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Ticket, TicketMessage, TicketStatus, TicketPriority, TicketCategory, UserRole
from app.helpers import sanitize_text
from app.services.ticket_service import generate_ticket_number, transition_status
from app.services.email_service import send_ticket_update_email

tickets_bp = Blueprint('tickets', __name__)


# ─── Page Routes ────────────────────────────────────

@tickets_bp.route('/s/<slug>/tickets')
@login_required
def tickets_page(slug):
    return render_template('tickets.html')


@tickets_bp.route('/s/<slug>/tickets/<int:ticket_id>')
@login_required
def ticket_detail_page(slug, ticket_id):
    ticket = db.session.get(Ticket, ticket_id)
    if not ticket:
        abort(404)
    # Users can only see their own tickets, admin can see all in their school
    if current_user.role == UserRole.MURID and ticket.user_id != current_user.id:
        abort(403)
    if ticket.school_id != current_user.school_id:
        abort(403)
    return render_template('ticket_detail.html', ticket=ticket)


# ─── API Routes ─────────────────────────────────────

@tickets_bp.route('/s/<slug>/api/tickets', methods=['GET'])
@login_required
def api_get_tickets(slug):
    status_filter = request.args.get('status')

    if current_user.role == UserRole.MURID:
        query = Ticket.query.filter_by(user_id=current_user.id, school_id=current_user.school_id)
    else:
        query = Ticket.query.filter_by(school_id=current_user.school_id)

    if status_filter == 'active':
        query = query.filter(Ticket.status.in_([
            TicketStatus.OPEN, TicketStatus.IN_QUEUE,
            TicketStatus.IN_PROGRESS, TicketStatus.WAITING_USER
        ]))
    elif status_filter == 'resolved':
        query = query.filter(Ticket.status.in_([TicketStatus.RESOLVED, TicketStatus.CLOSED]))

    tickets = query.order_by(Ticket.created_at.desc()).all()
    return jsonify({
        'success': True,
        'tickets': [t.to_dict() for t in tickets]
    })


@tickets_bp.route('/s/<slug>/api/tickets', methods=['POST'])
@login_required
def api_create_ticket(slug):
    data = request.get_json() or {}

    title = sanitize_text(data.get('title', ''), max_len=200)
    description = sanitize_text(data.get('description', ''), max_len=2000)
    category_str = data.get('category', 'general').lower()
    priority_str = data.get('priority', 'medium').lower()

    if not title or not description:
        return jsonify({'success': False, 'message': 'Judul dan deskripsi wajib diisi'}), 400

    try:
        category = TicketCategory(category_str)
    except ValueError:
        category = TicketCategory.GENERAL

    try:
        priority = TicketPriority(priority_str)
    except ValueError:
        priority = TicketPriority.MEDIUM

    ticket = Ticket(
        ticket_number=generate_ticket_number(school_id=current_user.school_id),
        title=title,
        description=description,
        category=category,
        priority=priority,
        school_id=current_user.school_id,
        user_id=current_user.id,
    )

    db.session.add(ticket)
    db.session.commit()

    return jsonify({
        'success': True,
        'ticket': ticket.to_dict(),
        'message': f'Ticket {ticket.ticket_number} berhasil dibuat'
    }), 201


@tickets_bp.route('/s/<slug>/api/tickets/<int:ticket_id>', methods=['GET'])
@login_required
def api_get_ticket(slug, ticket_id):
    ticket = db.session.get(Ticket, ticket_id)
    if not ticket:
        return jsonify({'success': False, 'message': 'Ticket tidak ditemukan'}), 404

    if ticket.school_id != current_user.school_id:
        return jsonify({'success': False, 'message': 'Tidak memiliki izin'}), 403

    if current_user.role == UserRole.MURID and ticket.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Tidak memiliki izin'}), 403

    # Filter internal messages for non-superadmin
    ticket_data = ticket.to_dict(include_messages=True)
    if current_user.role != UserRole.SUPER_ADMIN:
        ticket_data['messages'] = [m for m in ticket_data['messages'] if not m['is_internal']]

    return jsonify({'success': True, 'ticket': ticket_data})


@tickets_bp.route('/s/<slug>/api/tickets/<int:ticket_id>/message', methods=['POST'])
@login_required
def api_add_ticket_message(slug, ticket_id):
    ticket = db.session.get(Ticket, ticket_id)
    if not ticket:
        return jsonify({'success': False, 'message': 'Ticket tidak ditemukan'}), 404

    if ticket.school_id != current_user.school_id:
        return jsonify({'success': False, 'message': 'Tidak memiliki izin'}), 403

    if ticket.status in (TicketStatus.CLOSED, TicketStatus.RESOLVED):
        return jsonify({'success': False, 'message': 'Ticket sudah ditutup/diselesaikan'}), 400

    data = request.get_json() or {}
    content = sanitize_text(data.get('content', ''), max_len=2000)

    if not content:
        return jsonify({'success': False, 'message': 'Pesan tidak boleh kosong'}), 400

    message = TicketMessage(
        ticket_id=ticket.id,
        user_id=current_user.id,
        content=content,
        is_internal=False,
    )
    db.session.add(message)

    # Auto-transition: if user replies while WAITING_USER, move to IN_PROGRESS
    if ticket.status == TicketStatus.WAITING_USER:
        ticket.status = TicketStatus.IN_PROGRESS

    db.session.commit()

    return jsonify({'success': True, 'message': message.to_dict()})


@tickets_bp.route('/s/<slug>/api/tickets/<int:ticket_id>/close', methods=['POST'])
@login_required
def api_close_ticket(slug, ticket_id):
    ticket = db.session.get(Ticket, ticket_id)
    if not ticket:
        return jsonify({'success': False, 'message': 'Ticket tidak ditemukan'}), 404

    if ticket.school_id != current_user.school_id:
        return jsonify({'success': False, 'message': 'Tidak memiliki izin'}), 403

    if ticket.user_id != current_user.id and current_user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        return jsonify({'success': False, 'message': 'Tidak memiliki izin'}), 403

    success, msg = transition_status(ticket, TicketStatus.CLOSED, current_user)
    if not success:
        return jsonify({'success': False, 'message': msg}), 400

    return jsonify({'success': True, 'ticket': ticket.to_dict()})
