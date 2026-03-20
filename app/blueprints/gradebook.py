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
    
    # Get all grade items and entries for this student
    categories = GradeCategory.query.filter_by(course_id=course.id).all()
    grade_data = []
    
    for category in categories:
        items = []
        cat_total_score = 0
        cat_max_score = 0
        
        for item in category.grade_items:
            entry = GradeEntry.query.filter_by(grade_item_id=item.id, student_id=current_user.id).first()
            items.append({
                'item': item,
                'entry': entry
            })
            if entry and entry.score is not None:
                cat_total_score += entry.score
            cat_max_score += item.max_score
            
        grade_data.append({
            'category': category,
            'items': items,
            'total_score': cat_total_score,
            'max_score': cat_max_score,
            'percentage': (cat_total_score / cat_max_score * 100) if cat_max_score > 0 else 0
        })

    return render_template('gradebook/student_grades.html', course=course, grade_data=grade_data)


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
    return jsonify({
        'success': True,
        'items': [item.to_dict() for item in items]
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
