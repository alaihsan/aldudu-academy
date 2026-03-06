from flask import Blueprint, request, jsonify, abort
from flask_login import login_required, current_user
from app.models import db, Issue, IssueStatus, IssuePriority, UserRole
from app.helpers import sanitize_text

issues_bp = Blueprint('issues', __name__, url_prefix='/api')

@issues_bp.route('/issues', methods=['GET'])
@login_required
def get_issues():
    status_filter = request.args.get('status')
    
    # Murid only see their own, Admin/Guru see all
    if current_user.role == UserRole.MURID:
        query = Issue.query.filter(Issue.user_id == current_user.id)
    else:
        query = Issue.query
    
    if status_filter == 'resolved':
        query = query.filter(Issue.status == IssueStatus.RESOLVED)
    elif status_filter == 'active':
        query = query.filter(Issue.status.in_([IssueStatus.OPEN, IssueStatus.IN_PROGRESS]))
    
    issues = query.order_by(Issue.created_at.desc()).all()
    return jsonify({
        'success': True,
        'issues': [issue.to_dict() for issue in issues]
    })

@issues_bp.route('/issues', methods=['POST'])
@login_required
def create_issue():
    # All roles can create issues now
    data = request.get_json() or {}
    title = sanitize_text(data.get('title', ''), max_len=200)
    description = sanitize_text(data.get('description', ''))
    priority_str = data.get('priority', 'Medium').upper()
    
    if not title or not description:
        return jsonify({'success': False, 'message': 'Judul dan deskripsi wajib diisi'}), 400
        
    try:
        priority = IssuePriority[priority_str]
    except KeyError:
        priority = IssuePriority.MEDIUM
        
    new_issue = Issue(
        title=title,
        description=description,
        priority=priority,
        user_id=current_user.id
    )
    
    db.session.add(new_issue)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'issue': new_issue.to_dict(),
        'message': 'Laporan masalah berhasil dikirim'
    }), 201

@issues_bp.route('/issues/<int:issue_id>', methods=['PUT'])
@login_required
def update_issue(issue_id):
    issue = db.session.get(Issue, issue_id)
    if not issue:
        abort(404)
        
    # Only owner or Admin/Guru can update status? 
    # Usually owner can close, but Guru/Admin manages the resolution.
    # For now, allow owner to edit content, but only Guru/Admin can change status to In Progress etc.
    is_owner = issue.user_id == current_user.id
    is_privileged = current_user.role in [UserRole.GURU, UserRole.ADMIN]
    
    if not is_owner and not is_privileged:
        return jsonify({'success': False, 'message': 'Anda tidak memiliki izin'}), 403
        
    data = request.get_json() or {}
    
    if 'title' in data and is_owner:
        issue.title = sanitize_text(data.get('title'), max_len=200)
    if 'description' in data and is_owner:
        issue.description = sanitize_text(data.get('description'))
    if 'priority' in data and is_owner:
        try:
            issue.priority = IssuePriority[data.get('priority').upper()]
        except KeyError:
            pass
    if 'status' in data:
        # Only Guru/Admin can resolve/progress issues
        if is_privileged:
            try:
                issue.status = IssueStatus[data.get('status').upper()]
            except KeyError:
                pass
        else:
            return jsonify({'success': False, 'message': 'Hanya Guru/Admin yang dapat memproses laporan'}), 403
            
    db.session.commit()
    return jsonify({'success': True, 'issue': issue.to_dict()})

@issues_bp.route('/issues/<int:issue_id>', methods=['DELETE'])
@login_required
def delete_issue(issue_id):
    issue = db.session.get(Issue, issue_id)
    if not issue:
        abort(404)
        
    # Only owner or Admin can delete
    if issue.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        return jsonify({'success': False, 'message': 'Anda tidak memiliki izin'}), 403
        
    db.session.delete(issue)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Laporan masalah berhasil dihapus'})
