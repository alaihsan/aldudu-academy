"""
Gradebook Blueprint - Routes for managing grades
"""
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, abort
from flask_login import login_required, current_user
from app.models import Course, User, UserRole, Quiz, QuizStatus, AcademicYear
from app.models.gradebook import (
    GradeCategory, GradeCategoryType, LearningObjective, LearningGoal,
    GradeItem, GradeEntry
)
from app.extensions import db
from app.services.gradebook_service import (
    calculate_student_grade, calculate_category_grade, calculate_course_statistics,
    import_quiz_to_gradebook, sync_quiz_grades, get_student_grades_summary,
    bulk_save_grades
)
from app.helpers import log_activity, get_jakarta_now

gradebook_bp = Blueprint('gradebook', __name__, url_prefix='/gradebook')


# ─── Page Routes ───────────────────────────────────────────────────────────────

@gradebook_bp.route('/')
@login_required
def index():
    """Redirect to courses list"""
    if current_user.role == UserRole.SUPER_ADMIN:
        return redirect('/superadmin/dashboard')
    return redirect('/dashboard')


@gradebook_bp.route('/course/<int:course_id>')
@login_required
def course_gradebook(course_id):
    """Main gradebook page for a course (Teacher view)"""
    course = Course.query.get_or_404(course_id)
    
    # Check permission - only teacher can access
    if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        return render_template('error/403.html'), 403
    
    return render_template('gradebook/teacher_gradebook.html', course=course)


@gradebook_bp.route('/course/<int:course_id>/setup')
@login_required
def course_setup(course_id):
    """Setup page for CP/TP and categories (Teacher view)"""
    course = Course.query.get_or_404(course_id)
    
    if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        return render_template('error/403.html'), 403
    
    return render_template('gradebook/course_setup.html', course=course)


@gradebook_bp.route('/my-grades')
@login_required
def my_grades_index():
    """General view for student to see all their courses and grades"""
    if current_user.role != UserRole.MURID and current_user.role != UserRole.SUPER_ADMIN:
        abort(403)
    
    courses = current_user.courses_enrolled
    return render_template('gradebook/student_grades_index.html', courses=courses)


@gradebook_bp.route('/course/<int:course_id>/my-grades')
@login_required
def my_grades(course_id):
    """Student view of their own grades for a specific course"""
    course = Course.query.get_or_404(course_id)
    
    # Check if student is enrolled
    is_student = current_user.id in [s.id for s in course.students]
    is_teacher = course.teacher_id == current_user.id
    
    if not is_student and not is_teacher and current_user.role != UserRole.SUPER_ADMIN:
        return render_template('error/403.html'), 403
    
    # Template loads grades via JS API call to get_student_grades_summary()
    # which uses the unified calculate_final_grade() function
    return render_template('gradebook/student_grades.html', course=course)


# ─── API Routes - Categories ────────────────────────────────────────────────────

@gradebook_bp.route('/api/categories', methods=['GET'])
@login_required
def api_get_categories():
    """Get all categories for a course"""
    course_id = request.args.get('course_id', type=int)
    if not course_id:
        return jsonify({'success': False, 'message': 'course_id required'}), 400
    
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'success': False, 'message': 'Course not found'}), 404
    
    if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    categories = GradeCategory.query.filter_by(course_id=course_id).all()
    return jsonify({
        'success': True,
        'categories': [c.to_dict() for c in categories]
    })


@gradebook_bp.route('/api/categories', methods=['POST'])
@login_required
def api_create_category():
    """Create a new grade category"""
    data = request.get_json() or {}
    course_id = data.get('course_id')
    
    if not course_id:
        return jsonify({'success': False, 'message': 'course_id required'}), 400
    
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'success': False, 'message': 'Course not found'}), 404
    
    if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    name = data.get('name', '').strip()
    category_type = data.get('category_type', 'formatif')
    weight = data.get('weight', 0.0)
    description = data.get('description', '')
    
    if not name:
        return jsonify({'success': False, 'message': 'Nama kategori wajib diisi'}), 400
    
    try:
        cat_type = GradeCategoryType(category_type)
    except ValueError:
        return jsonify({'success': False, 'message': 'Tipe kategori tidak valid'}), 400
    
    category = GradeCategory(
        name=name,
        category_type=cat_type,
        weight=float(weight),
        description=description,
        course_id=course_id,
    )
    db.session.add(category)
    db.session.commit()
    
    log_activity(current_user.id, f"Created grade category: {name}")
    
    return jsonify({'success': True, 'category': category.to_dict()})


@gradebook_bp.route('/api/categories/<int:category_id>', methods=['PUT'])
@login_required
def api_update_category(category_id):
    """Update a grade category"""
    category = GradeCategory.query.get_or_404(category_id)
    course = Course.query.get(category.course_id)
    
    if not course or (course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    data = request.get_json() or {}
    
    if 'name' in data:
        category.name = data['name'].strip()
    if 'category_type' in data:
        try:
            category.category_type = GradeCategoryType(data['category_type'])
        except ValueError:
            return jsonify({'success': False, 'message': 'Tipe kategori tidak valid'}), 400
    if 'weight' in data:
        category.weight = float(data['weight'])
    if 'description' in data:
        category.description = data['description']
    
    db.session.commit()
    
    return jsonify({'success': True, 'category': category.to_dict()})


@gradebook_bp.route('/api/categories/<int:category_id>', methods=['DELETE'])
@login_required
def api_delete_category(category_id):
    """Delete a grade category"""
    category = GradeCategory.query.get_or_404(category_id)
    course = Course.query.get(category.course_id)
    
    if not course or (course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    db.session.delete(category)
    db.session.commit()
    
    return jsonify({'success': True})


# ─── API Routes - Learning Objectives (CP) ─────────────────────────────────────

@gradebook_bp.route('/api/learning-objectives', methods=['GET'])
@login_required
def api_get_learning_objectives():
    """Get all CP for a course"""
    course_id = request.args.get('course_id', type=int)
    if not course_id:
        return jsonify({'success': False, 'message': 'course_id required'}), 400
    
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'success': False, 'message': 'Course not found'}), 404
    
    if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    cps = LearningObjective.query.filter_by(course_id=course_id).order_by(LearningObjective.order).all()
    result = []
    for cp in cps:
        cp_data = cp.to_dict()
        cp_data['goals'] = [g.to_dict() for g in cp.learning_goals.order_by(LearningGoal.order).all()]
        result.append(cp_data)
    
    return jsonify({'success': True, 'learning_objectives': result})


@gradebook_bp.route('/api/learning-objectives', methods=['POST'])
@login_required
def api_create_learning_objective():
    """Create a new CP"""
    data = request.get_json() or {}
    course_id = data.get('course_id')
    
    if not course_id:
        return jsonify({'success': False, 'message': 'course_id required'}), 400
    
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'success': False, 'message': 'Course not found'}), 404
    
    if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    code = data.get('code', '').strip()
    description = data.get('description', '').strip()
    order = data.get('order', 0)
    
    if not code or not description:
        return jsonify({'success': False, 'message': 'Kode dan deskripsi wajib diisi'}), 400
    
    # Check for duplicate code
    existing = LearningObjective.query.filter_by(code=code, course_id=course_id).first()
    if existing:
        return jsonify({'success': False, 'message': 'Kode CP sudah digunakan'}), 400
    
    cp = LearningObjective(
        code=code,
        description=description,
        order=order,
        course_id=course_id,
    )
    db.session.add(cp)
    db.session.commit()
    
    return jsonify({'success': True, 'learning_objective': cp.to_dict()})


@gradebook_bp.route('/api/learning-objectives/<int:cp_id>', methods=['PUT'])
@login_required
def api_update_learning_objective(cp_id):
    """Update a CP"""
    cp = LearningObjective.query.get_or_404(cp_id)
    course = Course.query.get(cp.course_id)
    
    if not course or (course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    data = request.get_json() or {}
    
    if 'code' in data:
        # Check for duplicate
        existing = LearningObjective.query.filter_by(code=data['code'], course_id=cp.course_id).first()
        if existing and existing.id != cp.id:
            return jsonify({'success': False, 'message': 'Kode CP sudah digunakan'}), 400
        cp.code = data['code'].strip()
    if 'description' in data:
        cp.description = data['description'].strip()
    if 'order' in data:
        cp.order = data['order']
    
    db.session.commit()
    
    return jsonify({'success': True, 'learning_objective': cp.to_dict()})


@gradebook_bp.route('/api/learning-objectives/<int:cp_id>', methods=['DELETE'])
@login_required
def api_delete_learning_objective(cp_id):
    """Delete a CP"""
    cp = LearningObjective.query.get_or_404(cp_id)
    course = Course.query.get(cp.course_id)
    
    if not course or (course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    db.session.delete(cp)
    db.session.commit()
    
    return jsonify({'success': True})


# ─── API Routes - Learning Goals (TP) ──────────────────────────────────────────

@gradebook_bp.route('/api/learning-goals', methods=['POST'])
@login_required
def api_create_learning_goal():
    """Create a new TP"""
    data = request.get_json() or {}
    learning_objective_id = data.get('learning_objective_id')
    
    if not learning_objective_id:
        return jsonify({'success': False, 'message': 'learning_objective_id required'}), 400
    
    cp = LearningObjective.query.get_or_404(learning_objective_id)
    course = Course.query.get(cp.course_id)
    
    if not course or (course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    code = data.get('code', '').strip()
    description = data.get('description', '').strip()
    order = data.get('order', 0)
    
    if not code or not description:
        return jsonify({'success': False, 'message': 'Kode dan deskripsi wajib diisi'}), 400
    
    # Check for duplicate
    existing = LearningGoal.query.filter_by(code=code, learning_objective_id=learning_objective_id).first()
    if existing:
        return jsonify({'success': False, 'message': 'Kode TP sudah digunakan'}), 400
    
    tp = LearningGoal(
        code=code,
        description=description,
        order=order,
        learning_objective_id=learning_objective_id,
    )
    db.session.add(tp)
    db.session.commit()
    
    return jsonify({'success': True, 'learning_goal': tp.to_dict()})


@gradebook_bp.route('/api/learning-goals/<int:goal_id>', methods=['PUT'])
@login_required
def api_update_learning_goal(goal_id):
    """Update a TP"""
    tp = LearningGoal.query.get_or_404(goal_id)
    cp = LearningObjective.query.get(tp.learning_objective_id)
    course = Course.query.get(cp.course_id)
    
    if not course or (course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    data = request.get_json() or {}
    
    if 'code' in data:
        existing = LearningGoal.query.filter_by(code=data['code'], learning_objective_id=tp.learning_objective_id).first()
        if existing and existing.id != tp.id:
            return jsonify({'success': False, 'message': 'Kode TP sudah digunakan'}), 400
        tp.code = data['code'].strip()
    if 'description' in data:
        tp.description = data['description'].strip()
    if 'order' in data:
        tp.order = data['order']
    
    db.session.commit()
    
    return jsonify({'success': True, 'learning_goal': tp.to_dict()})


@gradebook_bp.route('/api/learning-goals/<int:goal_id>', methods=['DELETE'])
@login_required
def api_delete_learning_goal(goal_id):
    """Delete a TP"""
    tp = LearningGoal.query.get_or_404(goal_id)
    cp = LearningObjective.query.get(tp.learning_objective_id)
    course = Course.query.get(cp.course_id)
    
    if not course or (course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    db.session.delete(tp)
    db.session.commit()
    
    return jsonify({'success': True})


# ─── API Routes - Grade Items ───────────────────────────────────────────────────

@gradebook_bp.route('/api/items', methods=['GET'])
@login_required
def api_get_grade_items():
    """Get all grade items for a course"""
    course_id = request.args.get('course_id', type=int)
    if not course_id:
        return jsonify({'success': False, 'message': 'course_id required'}), 400
    
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'success': False, 'message': 'Course not found'}), 404
    
    if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    items = GradeItem.query.filter_by(course_id=course_id).all()
    
    items_data = []
    for item in items:
        item_dict = item.to_dict()
        item_dict['is_assignment'] = item.assignment_id is not None
        item_dict['assignment_id'] = item.assignment_id
        items_data.append(item_dict)
    
    return jsonify({
        'success': True,
        'items': items_data
    })


@gradebook_bp.route('/api/items', methods=['POST'])
@login_required
def api_create_grade_item():
    """Create a new grade item"""
    data = request.get_json() or {}
    course_id = data.get('course_id')
    
    if not course_id:
        return jsonify({'success': False, 'message': 'course_id required'}), 400
    
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'success': False, 'message': 'Course not found'}), 404
    
    if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    name = data.get('name', '').strip()
    category_id = data.get('category_id')
    learning_objective_id = data.get('learning_objective_id')
    learning_goal_id = data.get('learning_goal_id')
    max_score = data.get('max_score', 100.0)
    weight = data.get('weight', 0.0)
    description = data.get('description', '')
    due_date = data.get('due_date')
    
    if not name or not category_id:
        return jsonify({'success': False, 'message': 'Nama dan kategori wajib diisi'}), 400
    
    item = GradeItem(
        name=name,
        description=description,
        category_id=category_id,
        learning_objective_id=learning_objective_id,
        learning_goal_id=learning_goal_id,
        max_score=float(max_score),
        weight=float(weight),
        course_id=course_id,
    )
    
    if due_date:
        try:
            item.due_date = datetime.strptime(due_date, '%Y-%m-%d')
        except ValueError:
            pass
    
    db.session.add(item)
    db.session.commit()
    
    return jsonify({'success': True, 'item': item.to_dict()})


@gradebook_bp.route('/api/items/<int:item_id>', methods=['PUT'])
@login_required
def api_update_grade_item(item_id):
    """Update a grade item"""
    item = GradeItem.query.get_or_404(item_id)
    course = Course.query.get(item.course_id)
    
    if not course or (course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    data = request.get_json() or {}
    
    if 'name' in data:
        item.name = data['name'].strip()
    if 'description' in data:
        item.description = data['description']
    if 'category_id' in data:
        item.category_id = data['category_id']
    if 'learning_objective_id' in data:
        item.learning_objective_id = data['learning_objective_id']
    if 'learning_goal_id' in data:
        item.learning_goal_id = data['learning_goal_id']
    if 'max_score' in data:
        item.max_score = float(data['max_score'])
    if 'weight' in data:
        item.weight = float(data['weight'])
    if 'due_date' in data and data['due_date']:
        try:
            item.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d')
        except ValueError:
            pass
    
    db.session.commit()
    
    return jsonify({'success': True, 'item': item.to_dict()})


@gradebook_bp.route('/api/items/<int:item_id>', methods=['DELETE'])
@login_required
def api_delete_grade_item(item_id):
    """Delete a grade item"""
    item = GradeItem.query.get_or_404(item_id)
    course = Course.query.get(item.course_id)
    
    if not course or (course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    db.session.delete(item)
    db.session.commit()
    
    return jsonify({'success': True})


# ─── API Routes - Grade Entries ─────────────────────────────────────────────────

@gradebook_bp.route('/api/entries', methods=['GET'])
@login_required
def api_get_grade_entries():
    """Get grade entries for a grade item"""
    grade_item_id = request.args.get('grade_item_id', type=int)
    if not grade_item_id:
        return jsonify({'success': False, 'message': 'grade_item_id required'}), 400
    
    item = GradeItem.query.get_or_404(grade_item_id)
    course = Course.query.get(item.course_id)
    
    # Check permission
    is_teacher = course.teacher_id == current_user.id
    is_student = current_user.id in [s.id for s in course.students.all()]
    
    if not is_teacher and not is_student and current_user.role != UserRole.SUPER_ADMIN:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    if is_student:
        # Student can only see their own grades
        entries = GradeEntry.query.filter_by(grade_item_id=grade_item_id, student_id=current_user.id).all()
    else:
        # Teacher sees all
        entries = GradeEntry.query.filter_by(grade_item_id=grade_item_id).all()
    
    result = []
    for entry in entries:
        entry_data = entry.to_dict()
        entry_data['student_name'] = entry.student.name
        result.append(entry_data)
    
    return jsonify({'success': True, 'entries': result})


@gradebook_bp.route('/api/entries/bulk', methods=['POST'])
@login_required
def api_bulk_save_entries():
    """Bulk save grade entries"""
    data = request.get_json() or {}
    entries_data = data.get('entries', [])
    
    if not entries_data:
        return jsonify({'success': False, 'message': 'No entries provided'}), 400
    
    # Validate permission for first entry
    if entries_data:
        first_item = GradeItem.query.get(entries_data[0].get('grade_item_id'))
        if first_item:
            course = Course.query.get(first_item.course_id)
            if not course or (course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN):
                return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    saved_count = bulk_save_grades(entries_data, current_user.id)
    
    return jsonify({'success': True, 'saved_count': saved_count})


@gradebook_bp.route('/api/entries/<int:entry_id>', methods=['PUT'])
@login_required
def api_update_grade_entry(entry_id):
    """Update a grade entry"""
    entry = GradeEntry.query.get_or_404(entry_id)
    item = GradeItem.query.get(entry.grade_item_id)
    course = Course.query.get(item.course_id)
    
    if not course or (course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    data = request.get_json() or {}
    
    if 'score' in data:
        entry.score = float(data['score'])
        entry.percentage = (entry.score / item.max_score * 100) if item.max_score > 0 else 0
    if 'feedback' in data:
        entry.feedback = data['feedback']
    
    entry.graded_at = get_jakarta_now()
    entry.graded_by = current_user.id
    
    db.session.commit()
    
    return jsonify({'success': True, 'entry': entry.to_dict()})


# ─── API Routes - Statistics & Reports ─────────────────────────────────────────

@gradebook_bp.route('/api/stats/<int:course_id>', methods=['GET'])
@login_required
def api_get_course_stats(course_id):
    """Get course grade statistics"""
    course = Course.query.get_or_404(course_id)
    
    if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    stats = calculate_course_statistics(course_id)
    return jsonify({'success': True, 'stats': stats})


@gradebook_bp.route('/api/student/<int:student_id>/course/<int:course_id>', methods=['GET'])
@login_required
def api_get_student_grades(student_id, course_id):
    """Get comprehensive grade summary for a student"""
    course = Course.query.get_or_404(course_id)
    
    # Check permission
    is_self = current_user.id == student_id
    is_teacher = course.teacher_id == current_user.id
    
    if not is_self and not is_teacher and current_user.role != UserRole.SUPER_ADMIN:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    summary = get_student_grades_summary(student_id, course_id)
    return jsonify({'success': True, 'summary': summary})


# ─── API Routes - Quiz Integration ─────────────────────────────────────────────

@gradebook_bp.route('/api/quizzes/<int:quiz_id>/import', methods=['POST'])
@login_required
def api_import_quiz(quiz_id):
    """Import quiz to gradebook"""
    quiz = Quiz.query.get_or_404(quiz_id)
    course = Course.query.get(quiz.course_id)
    
    if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    data = request.get_json() or {}
    category_id = data.get('category_id')
    learning_goal_id = data.get('learning_goal_id')
    
    if not category_id:
        return jsonify({'success': False, 'message': 'category_id required'}), 400
    
    item, error = import_quiz_to_gradebook(quiz_id, category_id, learning_goal_id)
    
    if error:
        return jsonify({'success': False, 'message': error}), 400
    
    return jsonify({'success': True, 'item': item.to_dict()})


@gradebook_bp.route('/api/quizzes/<int:quiz_id>/sync', methods=['POST'])
@login_required
def api_sync_quiz_grades(quiz_id):
    """Sync quiz grades with gradebook"""
    quiz = Quiz.query.get_or_404(quiz_id)
    course = Course.query.get(quiz.course_id)
    
    if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    updated_count = sync_quiz_grades(quiz_id)
    
    return jsonify({'success': True, 'updated_count': updated_count})


@gradebook_bp.route('/api/quizzes/available', methods=['GET'])
@login_required
def api_get_available_quizzes():
    """Get quizzes that haven't been imported to gradebook"""
    course_id = request.args.get('course_id', type=int)
    if not course_id:
        return jsonify({'success': False, 'message': 'course_id required'}), 400
    
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'success': False, 'message': 'Course not found'}), 404
    
    if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    # Get imported quiz IDs
    imported_quiz_ids = db.session.query(GradeItem.quiz_id).filter(
        GradeItem.course_id == course_id,
        GradeItem.quiz_id.isnot(None)
    ).all()
    imported_ids = [q[0] for q in imported_quiz_ids if q[0]]
    
    # Get quizzes not yet imported
    quizzes = Quiz.query.filter(
        Quiz.course_id == course_id,
        Quiz.id.notin_(imported_ids) if imported_ids else Quiz.id.isnot(None)
    ).all()
    
    return jsonify({
        'success': True,
        'quizzes': [{
            'id': q.id,
            'name': q.name,
            'points': q.points,
            'submissions_count': q.submissions.count(),
        } for q in quizzes]
    })


@gradebook_bp.route('/api/course/<int:course_id>/quizzes-with-analysis', methods=['GET'])
@login_required
def api_get_quizzes_with_analysis(course_id):
    """Get quizzes with submissions for CTT analysis"""
    course = Course.query.get_or_404(course_id)
    
    if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    # Get all quizzes with at least 1 submission
    quizzes = Quiz.query.filter(
        Quiz.course_id == course_id
    ).all()
    
    quiz_list = []
    for q in quizzes:
        submission_count = q.submissions.count()
        if submission_count > 0:
            quiz_list.append({
                'id': q.id,
                'name': q.name,
                'submissions_count': submission_count,
            })
    
    return jsonify({
        'success': True,
        'quizzes': quiz_list
    })


@gradebook_bp.route('/api/quiz/<int:quiz_id>/ctt-analysis', methods=['GET'])
@login_required
def api_get_ctt_analysis(quiz_id):
    """
    Get Classical Test Theory (CTT) analysis for a quiz.
    
    Returns:
    - p_value (difficulty index) for each question
    - point_biserial (discrimination index) for each question
    - Summary statistics
    """
    from app.models.quiz import Question, QuizSubmission, Answer
    
    quiz = Quiz.query.get_or_404(quiz_id)
    course = Course.query.get(quiz.course_id)
    
    if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    # Get all questions in the quiz
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    
    if not questions:
        return jsonify({
            'success': True,
            'items': [],
            'summary': {}
        })
    
    # Get all submissions
    submissions = QuizSubmission.query.filter_by(quiz_id=quiz_id).all()
    total_students = len(submissions)
    
    if total_students == 0:
        return jsonify({
            'success': True,
            'items': [],
            'summary': {}
        })
    
    # Build response matrix: item scores per student and total scores
    total_scores = [s.score for s in submissions]
    item_scores_matrix = {}  # question_id -> list of 0/1 per student
    item_selected_options = {}  # question_id -> list of selected_option_id per student

    for question in questions:
        scores = []
        selected_opts = []
        for submission in submissions:
            answer = Answer.query.filter_by(
                submission_id=submission.id,
                question_id=question.id
            ).first()

            is_correct = bool(answer and answer.is_correct)
            scores.append(1 if is_correct else 0)
            selected_opts.append(answer.selected_option_id if answer else None)

        item_scores_matrix[question.id] = scores
        item_selected_options[question.id] = selected_opts

    # Upper-Lower 27% groups for discrimination analysis
    n_group = max(1, int(len(submissions) * 0.27))
    sorted_indices = sorted(range(len(total_scores)), key=lambda i: total_scores[i], reverse=True)
    upper_indices = set(sorted_indices[:n_group])
    lower_indices = set(sorted_indices[-n_group:])

    # Total score statistics
    mean_total = sum(total_scores) / len(total_scores) if total_scores else 0
    variance_total = sum((s - mean_total) ** 2 for s in total_scores) / len(total_scores) if total_scores else 0

    # Calculate CTT metrics for each question
    items_analysis = []
    all_p_values = []
    all_point_biserials = []
    sum_pq = 0.0

    for question in questions:
        student_scores = item_scores_matrix[question.id]
        correct_count = sum(student_scores)

        # P-value (difficulty index)
        p_value = correct_count / total_students if total_students > 0 else 0
        q_value = 1 - p_value
        item_variance = p_value * q_value
        sum_pq += item_variance
        all_p_values.append(p_value)

        # Point-biserial correlation (discrimination)
        if len(student_scores) > 1 and len(total_scores) > 1:
            mean_x = sum(student_scores) / len(student_scores)
            mean_y = mean_total

            numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(student_scores, total_scores))
            std_x = (sum((x - mean_x) ** 2 for x in student_scores)) ** 0.5
            std_y = variance_total ** 0.5 * (len(total_scores) ** 0.5)

            # Use population std for consistency
            pop_std_x = (sum((x - mean_x) ** 2 for x in student_scores) / len(student_scores)) ** 0.5
            pop_std_y = variance_total ** 0.5

            if pop_std_x > 0 and pop_std_y > 0:
                point_biserial = (sum((x - mean_x) * (y - mean_y) for x, y in zip(student_scores, total_scores)) / len(student_scores)) / (pop_std_x * pop_std_y)
            else:
                point_biserial = 0
        else:
            point_biserial = 0

        # Corrected point-biserial (remove item's own score from total)
        corrected_total_scores = [total_scores[i] - student_scores[i] for i in range(len(total_scores))]
        corrected_mean_y = sum(corrected_total_scores) / len(corrected_total_scores) if corrected_total_scores else 0
        corrected_var_y = sum((s - corrected_mean_y) ** 2 for s in corrected_total_scores) / len(corrected_total_scores) if corrected_total_scores else 0

        if len(student_scores) > 1 and corrected_var_y > 0:
            mean_x = sum(student_scores) / len(student_scores)
            pop_std_x = (sum((x - mean_x) ** 2 for x in student_scores) / len(student_scores)) ** 0.5
            pop_std_cy = corrected_var_y ** 0.5

            if pop_std_x > 0 and pop_std_cy > 0:
                corrected_rpbis = (sum((x - mean_x) * (y - corrected_mean_y) for x, y in zip(student_scores, corrected_total_scores)) / len(student_scores)) / (pop_std_x * pop_std_cy)
            else:
                corrected_rpbis = 0
        else:
            corrected_rpbis = 0

        all_point_biserials.append(point_biserial)

        # Upper-Lower discrimination (27% groups)
        upper_correct = sum(1 for i in upper_indices if student_scores[i] == 1)
        lower_correct = sum(1 for i in lower_indices if student_scores[i] == 1)
        discrimination_index = (upper_correct - lower_correct) / n_group if n_group > 0 else 0

        # Difficulty interpretation
        if p_value < 0.3:
            difficulty_label = 'Sukar'
        elif p_value > 0.7:
            difficulty_label = 'Mudah'
        else:
            difficulty_label = 'Sedang'

        # Discrimination interpretation
        if discrimination_index >= 0.4:
            discrimination_label = 'Sangat Baik'
        elif discrimination_index >= 0.3:
            discrimination_label = 'Baik'
        elif discrimination_index >= 0.2:
            discrimination_label = 'Cukup'
        else:
            discrimination_label = 'Perlu Perbaikan'

        # Distractor analysis for multiple choice questions
        distractor_analysis = None
        if question.question_type in ['multiple_choice', 'true_false', 'dropdown']:
            from app.models.quiz import Option
            options = Option.query.filter_by(question_id=question.id).all()
            distractor_analysis = []

            selected_opts = item_selected_options[question.id]
            for option in options:
                opt_count = sum(1 for opt_id in selected_opts if opt_id == option.id)
                upper_count = sum(1 for i in upper_indices if selected_opts[i] == option.id)
                lower_count = sum(1 for i in lower_indices if selected_opts[i] == option.id)

                distractor_analysis.append({
                    'option_id': option.id,
                    'option_text': option.text[:100] if option.text else '',
                    'is_correct': option.is_correct,
                    'total_selected': opt_count,
                    'percentage': round(opt_count / total_students * 100, 1) if total_students > 0 else 0,
                    'upper_group': upper_count,
                    'lower_group': lower_count,
                })

        items_analysis.append({
            'question_id': question.id,
            'p_value': round(p_value, 4),
            'item_variance': round(item_variance, 4),
            'correct_count': correct_count,
            'total_students': total_students,
            'point_biserial': round(point_biserial, 4),
            'corrected_point_biserial': round(corrected_rpbis, 4),
            'discrimination_index': round(discrimination_index, 4),
            'difficulty_label': difficulty_label,
            'discrimination_label': discrimination_label,
            'distractor_analysis': distractor_analysis,
        })

    # Summary statistics
    k = len(questions)
    avg_p_value = sum(all_p_values) / len(all_p_values) if all_p_values else 0
    avg_point_biserial = sum(all_point_biserials) / len(all_point_biserials) if all_point_biserials else 0

    # KR-20 Reliability: KR-20 = (k/(k-1)) * (1 - Σpq / σ²_total)
    if k > 1 and variance_total > 0:
        kr20 = (k / (k - 1)) * (1 - sum_pq / variance_total)
        reliability = max(0.0, min(1.0, kr20))
    else:
        reliability = 0.0

    # Interpret difficulty level
    if avg_p_value < 0.3:
        difficulty_level = 'Sukar'
    elif avg_p_value > 0.7:
        difficulty_level = 'Mudah'
    else:
        difficulty_level = 'Sedang'

    # Interpret discrimination level
    if avg_point_biserial >= 0.4:
        discrimination_level = 'Baik'
    elif avg_point_biserial >= 0.2:
        discrimination_level = 'Cukup'
    else:
        discrimination_level = 'Perlu Perbaikan'

    if reliability >= 0.9:
        reliability_label = 'Sangat Baik'
    elif reliability >= 0.7:
        reliability_label = 'Baik'
    elif reliability >= 0.5:
        reliability_label = 'Cukup'
    else:
        reliability_label = 'Kurang'

    return jsonify({
        'success': True,
        'quiz_id': quiz_id,
        'total_students': total_students,
        'group_size_27pct': n_group,
        'items': items_analysis,
        'summary': {
            'avg_p_value': round(avg_p_value, 4),
            'difficulty_level': difficulty_level,
            'avg_point_biserial': round(avg_point_biserial, 4),
            'discrimination_level': discrimination_level,
            'reliability_kr20': round(reliability, 4),
            'reliability_label': reliability_label,
            'total_score_mean': round(mean_total, 2),
            'total_score_variance': round(variance_total, 4),
            'sum_pq': round(sum_pq, 4),
            'num_items': k,
        }
    })


@gradebook_bp.route('/api/assignments/<int:assignment_id>/submissions', methods=['GET'])
@login_required
def api_get_assignment_submissions(assignment_id):
    """Get assignment submissions with attachments for preview"""
    from app.models.assignment import Assignment, AssignmentSubmission
    
    assignment = Assignment.query.get_or_404(assignment_id)
    course = Course.query.get(assignment.course_id)
    
    if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    # Get all submissions
    submissions = AssignmentSubmission.query.filter_by(
        assignment_id=assignment_id
    ).all()
    
    submission_list = []
    for sub in submissions:
        student = User.query.get(sub.student_id)
        submission_list.append({
            'id': sub.id,
            'student_id': sub.student_id,
            'student_name': student.name if student else 'Unknown',
            'content': sub.content,
            'file_path': sub.file_path,
            'status': sub.status.value,
            'submitted_at': sub.submitted_at.strftime('%Y-%m-%d %H:%M') if sub.submitted_at else None,
        })
    
    return jsonify({
        'success': True,
        'assignment_id': assignment_id,
        'total_submissions': len(submission_list),
        'submissions': submission_list
    })


@gradebook_bp.route('/api/course/<int:course_id>/wizard-setup', methods=['POST'])
@login_required
def api_wizard_setup(course_id):
    """
    Wizard setup for new semester.
    Creates default categories and learning objectives.
    
    Request JSON:
    {
        "step": 1|2|3,
        "categories": [{"name": "...", "type": "formatif", "weight": 30}],
        "learning_objectives": [{"code": "CP-1", "description": "..."}]
    }
    """
    from app.models.gradebook import GradeCategory, GradeCategoryType, LearningObjective
    
    course = Course.query.get_or_404(course_id)
    
    if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    data = request.get_json() or {}
    step = data.get('step', 1)
    
    if step == 1:
        # Create categories
        categories_data = data.get('categories', [])
        created_categories = []
        
        for cat_data in categories_data:
            name = cat_data.get('name')
            cat_type = cat_data.get('type')
            weight = cat_data.get('weight', 0)
            
            if not name or not cat_type:
                continue
            
            try:
                category_type = GradeCategoryType(cat_type)
            except ValueError:
                continue
            
            category = GradeCategory(
                name=name,
                category_type=category_type,
                weight=weight,
                course_id=course_id
            )
            db.session.add(category)
            created_categories.append({
                'id': category.id,
                'name': category.name,
                'type': category_type.value,
                'weight': weight
            })
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'step': 1,
            'message': 'Kategori berhasil dibuat',
            'categories': created_categories
        })
    
    elif step == 2:
        # Create learning objectives (CP)
        cp_data = data.get('learning_objectives', [])
        created_cps = []
        
        for cp in cp_data:
            code = cp.get('code')
            description = cp.get('description')
            
            if not code or not description:
                continue
            
            lo = LearningObjective(
                code=code,
                description=description,
                course_id=course_id,
                order=len(created_cps)
            )
            db.session.add(lo)
            created_cps.append({
                'id': lo.id,
                'code': lo.code,
                'description': lo.description
            })
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'step': 2,
            'message': 'Capaian Pembelajaran berhasil dibuat',
            'learning_objectives': created_cps
        })
    
    elif step == 3:
        # Finalize setup
        categories_count = GradeCategory.query.filter_by(course_id=course_id).count()
        cp_count = LearningObjective.query.filter_by(course_id=course_id).count()
        
        return jsonify({
            'success': True,
            'step': 3,
            'message': 'Setup semester selesai',
            'summary': {
                'categories_count': categories_count,
                'learning_objectives_count': cp_count
            }
        })
    
    return jsonify({'success': False, 'message': 'Invalid step'}), 400


@gradebook_bp.route('/api/course/<int:course_id>/wizard-status', methods=['GET'])
@login_required
def api_wizard_status(course_id):
    """Get wizard setup status for a course"""
    course = Course.query.get_or_404(course_id)
    
    if course.teacher_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    categories_count = GradeCategory.query.filter_by(course_id=course_id).count()
    cp_count = LearningObjective.query.filter_by(course_id=course_id).count()
    
    # Determine setup progress
    progress = 0
    next_step = 1
    message = "Mulai setup semester"
    
    if categories_count > 0:
        progress = 33
        next_step = 2
        message = "Lanjutkan dengan menambah CP"
    
    if cp_count > 0:
        progress = 66
        next_step = 3
        message = "Finalisasi setup"
    
    if categories_count > 0 and cp_count > 0:
        progress = 100
        next_step = 0
        message = "Setup selesai"
    
    return jsonify({
        'success': True,
        'setup_complete': progress == 100,
        'progress': progress,
        'next_step': next_step,
        'message': message,
        'categories_count': categories_count,
        'learning_objectives_count': cp_count
    })
