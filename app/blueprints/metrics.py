"""
Performance Metrics Blueprints

Provides performance metrics dashboard and APIs for monitoring.
"""

import os
import time
from flask import Blueprint, jsonify, render_template

metrics_bp = Blueprint('metrics', __name__)


@metrics_bp.route('/superadmin/metrics')
def metrics_dashboard():
    """Performance Metrics Dashboard for Superadmin."""
    return render_template('superadmin/metrics.html')


@metrics_bp.route('/superadmin/api/metrics/data', methods=['GET'])
def api_metrics_data():
    """Get comprehensive metrics data for dashboard."""
    import psutil
    from flask import current_app
    from app.models import User, UserRole, School, SchoolStatus, Course
    from sqlalchemy import func
    from app.extensions import db

    # Get Prometheus metrics if available
    prom_metrics = current_app.config.get('PROMETHEUS_METRICS', {})

    # System metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    # Application stats
    users_by_role = db.session.query(
        User.role, func.count(User.id)
    ).group_by(User.role).all()

    schools_by_status = db.session.query(
        School.status, func.count(School.id)
    ).group_by(School.status).all()

    # Calculate active users (logged in last 24h - mock for now)
    active_users = User.query.filter(User.is_active == True).count()

    # Update Prometheus gauges
    if prom_metrics.get('active_users'):
        prom_metrics['active_users'].set(active_users)

    # Students enrolled
    students_enrolled = User.query.filter(User.role == UserRole.MURID).count()
    if prom_metrics.get('students_enrolled'):
        prom_metrics['students_enrolled'].set(students_enrolled)

    metrics = {
        'system': {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_used_gb': round(memory.used / (1024**3), 2),
            'memory_total_gb': round(memory.total / (1024**3), 2),
            'disk_percent': disk.percent,
            'disk_used_gb': round(disk.used / (1024**3), 2),
            'disk_total_gb': round(disk.total / (1024**3), 2),
        },
        'application': {
            'total_requests': 0,  # Would come from Prometheus
            'avg_latency_ms': 0,  # Would come from Prometheus
            'error_rate': 0,  # Would come from Prometheus
            'active_users': active_users,
            'requests_per_second': 0,  # Would come from Prometheus
        },
        'users': {
            'total': User.query.count(),
            'by_role': {role.value: count for role, count in users_by_role},
        },
        'schools': {
            'total': School.query.count(),
            'by_status': {status.value: count for status, count in schools_by_status},
        },
        'business': {
            'courses': Course.query.count() if 'Course' in str(db.Model.registry._class_registry) else 0,
            'students_enrolled': students_enrolled,
            'quizzes_taken': 0,  # Would increment on quiz submission
        },
        'prometheus': {
            'enabled': current_app.config.get('PROMETHEUS_ENABLED', False),
            'endpoint': '/metrics' if current_app.config.get('PROMETHEUS_ENABLED', False) else None,
        }
    }

    return jsonify({'success': True, 'metrics': metrics})


@metrics_bp.route('/superadmin/api/metrics/refresh', methods=['POST'])
def api_metrics_refresh():
    """Force refresh metrics."""
    return jsonify({
        'success': True,
        'message': 'Metrics refreshed',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    })
