from flask import Blueprint, request, jsonify, abort
from flask_login import login_required, current_user
from app.models import db, Issue, IssueStatus, IssuePriority, UserRole
from app.helpers import sanitize_text

issues_bp = Blueprint('issues', __name__, url_prefix='/api')

@issues_bp.route('/issues', methods=['GET'])
@login_required
def get_issues():
    # Teachers see their own issues, or we could let them see all if needed.
    # For now, let's show all issues but highlight the ones they created.
    status_filter = request.args.get('status')
    
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
    if current_user.role != UserRole.GURU:
        return jsonify({'success': False, 'message': 'Hanya guru yang dapat membuat laporan masalah'}), 403
        
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
        teacher_id=current_user.id
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
        
    if issue.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Anda tidak memiliki izin untuk mengubah laporan ini'}), 403
        
    data = request.get_json() or {}
    
    if 'title' in data:
        issue.title = sanitize_text(data.get('title'), max_len=200)
    if 'description' in data:
        issue.description = sanitize_text(data.get('description'))
    if 'priority' in data:
        try:
            issue.priority = IssuePriority[data.get('priority').upper()]
        except KeyError:
            pass
    if 'status' in data:
        try:
            issue.status = IssueStatus[data.get('status').upper()]
        except KeyError:
            pass
            
    db.session.commit()
    return jsonify({'success': True, 'issue': issue.to_dict()})

@issues_bp.route('/issues/<int:issue_id>', methods=['DELETE'])
@login_required
def delete_issue(issue_id):
    issue = db.session.get(Issue, issue_id)
    if not issue:
        abort(404)
        
    if issue.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Anda tidak memiliki izin untuk menghapus laporan ini'}), 403
        
    db.session.delete(issue)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Laporan masalah berhasil dihapus'})
