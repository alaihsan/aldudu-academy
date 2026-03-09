from datetime import datetime
from app.extensions import db
from app.models import Ticket, TicketStatus, TicketMessage, UserRole
from app.helpers import get_jakarta_now


def generate_ticket_number():
    now = get_jakarta_now()
    year = now.strftime('%Y')

    last_ticket = Ticket.query.filter(
        Ticket.ticket_number.like(f'TKT-{year}-%')
    ).order_by(Ticket.id.desc()).first()

    if last_ticket:
        try:
            last_num = int(last_ticket.ticket_number.split('-')[-1])
        except (ValueError, IndexError):
            last_num = 0
    else:
        last_num = 0

    return f'TKT-{year}-{str(last_num + 1).zfill(5)}'


ALLOWED_TRANSITIONS = {
    # Super Admin transitions
    'super_admin': {
        TicketStatus.OPEN: [TicketStatus.IN_QUEUE],
        TicketStatus.IN_QUEUE: [TicketStatus.IN_PROGRESS],
        TicketStatus.IN_PROGRESS: [TicketStatus.WAITING_USER, TicketStatus.RESOLVED],
        TicketStatus.WAITING_USER: [TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED],
        TicketStatus.RESOLVED: [TicketStatus.CLOSED],
    },
    # User transitions
    'user': {
        TicketStatus.OPEN: [],
        TicketStatus.WAITING_USER: [TicketStatus.IN_PROGRESS],
        TicketStatus.RESOLVED: [TicketStatus.CLOSED],
    },
}


def can_transition(ticket, new_status, user):
    role_key = 'super_admin' if user.role == UserRole.SUPER_ADMIN else 'user'
    allowed = ALLOWED_TRANSITIONS.get(role_key, {}).get(ticket.status, [])
    return new_status in allowed


def transition_status(ticket, new_status, changed_by):
    if not can_transition(ticket, new_status, changed_by):
        return False, f'Tidak bisa mengubah status dari {ticket.status.value} ke {new_status.value}'

    ticket.status = new_status

    now = get_jakarta_now()
    if new_status == TicketStatus.RESOLVED:
        ticket.resolved_at = now
    elif new_status == TicketStatus.CLOSED:
        ticket.closed_at = now

    db.session.commit()
    return True, 'Status berhasil diperbarui'


def get_queue_position(ticket):
    if ticket.status not in (TicketStatus.OPEN, TicketStatus.IN_QUEUE):
        return 0

    count = Ticket.query.filter(
        Ticket.status.in_([TicketStatus.OPEN, TicketStatus.IN_QUEUE]),
        Ticket.created_at < ticket.created_at,
    ).count()

    return count + 1
