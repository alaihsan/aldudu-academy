import os
from datetime import datetime
from flask import Blueprint, request, jsonify, abort, render_template, current_app, redirect, url_for, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models import Assignment, AssignmentSubmission, AssignmentStatus, AssignmentSubmissionStatus, Course, GradeItem, GradeEntry, ActivityLog, UserRole
from app.helpers import get_jakarta_now

assignment_bp = Blueprint('assignment', __name__, url_prefix='/assignment')

def get_assignment_or_abort(assignment_id, check_teacher=False):
    from app.tenant import get_school_id_or_abort, verify_course_in_school
    assignment = db.session.get(Assignment, assignment_id)
    if not assignment:
        abort(404, description="Tugas tidak ditemukan.")
    school_id = get_school_id_or_abort()
    verify_course_in_school(assignment.course, school_id)
    
    if check_teacher and assignment.course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        abort(403, description="Anda tidak memiliki akses sebagai guru ke tugas ini.")
    elif not check_teacher:
        # Check if user is enrolled or is teacher
        if current_user.id != assignment.course.teacher_id and current_user.role != UserRole.SUPER_ADMIN and current_user not in assignment.course.students:
            abort(403, description="Anda tidak memiliki akses ke tugas ini.")
            
    return assignment

@assignment_bp.route('/course/<int:course_id>/create', methods=['POST'])
@login_required
def create_assignment(course_id):
    from app.tenant import get_school_id_or_abort, verify_course_in_school
    course = db.session.get(Course, course_id)
    if not course:
        abort(404)
        
    school_id = get_school_id_or_abort()
    verify_course_in_school(course, school_id)
    
    if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        abort(403)

    data = request.form
    title = data.get('title', 'Tugas Baru')
    description = data.get('description', '')
    max_score = float(data.get('max_score', 100))
    
    due_date_str = data.get('due_date')
    due_date = None
    if due_date_str:
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            pass

    assignment = Assignment(
        title=title,
        description=description,
        course_id=course.id,
        due_date=due_date,
        max_score=max_score,
        status=AssignmentStatus.PUBLISHED
    )
    db.session.add(assignment)
    db.session.flush()

    # Create Activity Log
    log = ActivityLog(
        user_id=current_user.id,
        action="membuat tugas baru",
        target_type="assignment",
        target_id=assignment.id,
        school_id=school_id
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({'success': True, 'assignment_id': assignment.id})

@assignment_bp.route('/<int:assignment_id>')
@login_required
def detail(assignment_id):
    assignment = get_assignment_or_abort(assignment_id)
    is_teacher = (current_user.id == assignment.course.teacher_id or current_user.role == UserRole.SUPER_ADMIN)
    
    submission = None
    all_submissions = []
    if is_teacher:
        all_submissions = assignment.submissions.all()
    else:
        submission = AssignmentSubmission.query.filter_by(assignment_id=assignment.id, student_id=current_user.id).first()
        
    return render_template(
        'assignment_detail.html',
        assignment=assignment,
        course=assignment.course,
        is_teacher=is_teacher,
        submission=submission,
        all_submissions=all_submissions
    )

@assignment_bp.route('/<int:assignment_id>/submit', methods=['POST'])
@login_required
def submit(assignment_id):
    assignment = get_assignment_or_abort(assignment_id)
    if current_user.id == assignment.course.teacher_id:
        abort(403, description="Guru tidak dapat mengumpulkan tugas.")
        
    content = request.form.get('content', '')
    file = request.files.get('file')
    
    submission = AssignmentSubmission.query.filter_by(assignment_id=assignment.id, student_id=current_user.id).first()
    if not submission:
        submission = AssignmentSubmission(
            assignment_id=assignment.id,
            student_id=current_user.id
        )
        db.session.add(submission)
        
    submission.content = content
    submission.submitted_at = get_jakarta_now()
    submission.status = AssignmentSubmissionStatus.SUBMITTED
    
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        upload_folder = os.path.join(current_app.instance_path, 'uploads', str(assignment.course.id), 'assignments', str(assignment.id))
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, f"{current_user.id}_{filename}")
        file.save(file_path)
        submission.file_path = f"{current_user.id}_{filename}"
        
    # Log Activity
    log = ActivityLog(
        user_id=current_user.id,
        action="mengumpulkan tugas",
        target_type="assignment",
        target_id=assignment.id,
        school_id=assignment.course.academic_year.school_id if assignment.course.academic_year else None
    )
    db.session.add(log)
    db.session.commit()
    
    return redirect(url_for('assignment.detail', assignment_id=assignment.id))

@assignment_bp.route('/<int:assignment_id>/download/<int:submission_id>')
@login_required
def download_submission(assignment_id, submission_id):
    assignment = get_assignment_or_abort(assignment_id)
    submission = db.session.get(AssignmentSubmission, submission_id)
    
    if not submission or submission.assignment_id != assignment.id:
        abort(404, description="Submission tidak ditemukan.")
        
    if current_user.id != assignment.course.teacher_id and current_user.id != submission.student_id and current_user.role != UserRole.SUPER_ADMIN:
        abort(403)
        
    if not submission.file_path:
        abort(404, description="File tidak ditemukan.")
        
    upload_folder = os.path.join(current_app.instance_path, 'uploads', str(assignment.course.id), 'assignments', str(assignment.id))
    file_path = os.path.join(upload_folder, submission.file_path)
    
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    abort(404, description="File fisik tidak ditemukan.")

@assignment_bp.route('/<int:assignment_id>/grade/<int:submission_id>', methods=['POST'])
@login_required
def grade(assignment_id, submission_id):
    assignment = get_assignment_or_abort(assignment_id, check_teacher=True)
    submission = db.session.get(AssignmentSubmission, submission_id)
    
    if not submission or submission.assignment_id != assignment.id:
        abort(404)
        
    data = request.form
    score_str = data.get('score')
    feedback = data.get('feedback', '')
    
    if not score_str:
        return jsonify({'success': False, 'message': 'Nilai wajib diisi.'}), 400
        
    try:
        score = float(score_str)
    except ValueError:
        return jsonify({'success': False, 'message': 'Format nilai tidak valid.'}), 400
        
    if score < 0:
        return jsonify({'success': False, 'message': 'Nilai tidak boleh negatif.'}), 400
        
    if score > assignment.max_score:
        return jsonify({'success': False, 'message': f'Nilai tidak boleh melebihi nilai maksimal ({assignment.max_score}).'}), 400
        
    submission.status = AssignmentSubmissionStatus.GRADED
    
    # Update or Create GradeEntry
    # Find grade_item for this assignment or create one
    grade_item = assignment.grade_item
    if not grade_item:
        # Re-check with explicit query in case relationship cache is stale
        grade_item = GradeItem.query.filter_by(assignment_id=assignment.id).first()
    if not grade_item:
        # Create a default GradeItem in the first category
        category = assignment.course.grade_categories.first()
        if not category:
            from app.models import GradeCategory, GradeCategoryType
            category = GradeCategory(name="Tugas", course_id=assignment.course.id, category_type=GradeCategoryType.FORMATIF, weight=100.0)
            db.session.add(category)
            db.session.flush()
            
        grade_item = GradeItem(
            name=f"Tugas: {assignment.title}",
            category_id=category.id,
            max_score=assignment.max_score,
            course_id=assignment.course.id,
            assignment_id=assignment.id,
            due_date=assignment.due_date
        )
        db.session.add(grade_item)
        db.session.flush()
        
    grade_entry = GradeEntry.query.filter_by(grade_item_id=grade_item.id, student_id=submission.student_id).first()
    if not grade_entry:
        grade_entry = GradeEntry(
            grade_item_id=grade_item.id,
            student_id=submission.student_id
        )
        db.session.add(grade_entry)
        
    grade_entry.score = score
    grade_entry.percentage = (score / assignment.max_score) * 100 if assignment.max_score > 0 else 0
    grade_entry.feedback = feedback
    grade_entry.graded_at = get_jakarta_now()
    grade_entry.graded_by = current_user.id
    
    # Notify student
    log = ActivityLog(
        user_id=submission.student_id,
        action=f"Nilai tugas '{assignment.title}' telah diberikan",
        target_type="assignment_graded",
        target_id=assignment.id,
        school_id=assignment.course.academic_year.school_id if assignment.course.academic_year else None
    )
    db.session.add(log)
    
    db.session.commit()
    
    return jsonify({'success': True})
