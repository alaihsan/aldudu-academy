"""
Health Check Blueprints

Provides health check endpoints for monitoring and diagnostics.
"""

import os
import time
from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user

health_bp = Blueprint('health', __name__)


@health_bp.route('/healthz', methods=['GET'])
def healthz():
    """Basic health check endpoint."""
    return jsonify({'status': 'ok'}), 200


@health_bp.route('/superadmin/health')
def health_dashboard():
    """Health Status Dashboard for Superadmin."""
    from app.models import User, UserRole, School, SchoolStatus
    from sqlalchemy import func
    from app.extensions import db

    stats = {
        'total_users': User.query.count(),
        'users_by_role': db.session.query(
            User.role, func.count(User.id)
        ).group_by(User.role).all(),
        'total_schools': School.query.count(),
        'active_schools': School.query.filter_by(status=SchoolStatus.ACTIVE).count(),
        'pending_schools': School.query.filter_by(status=SchoolStatus.PENDING).count(),
        'suspended_schools': School.query.filter_by(status=SchoolStatus.SUSPENDED).count(),
    }
    return render_template('superadmin/health.html', stats=stats)


@health_bp.route('/superadmin/api/health/checks', methods=['GET'])
def api_health_checks():
    """Comprehensive health checks for all services."""
    import redis
    from sqlalchemy import text
    from app.extensions import db, mail
    from flask import current_app

    checks = {}
    overall_healthy = True

    # 1. Database Check
    try:
        start = time.time()
        db.session.execute(text('SELECT 1'))
        duration = (time.time() - start) * 1000
        checks['database'] = {
            'status': 'healthy',
            'response_time': f'{duration:.2f}ms',
            'message': 'Database connection OK'
        }
    except Exception as e:
        checks['database'] = {
            'status': 'unhealthy',
            'message': str(e)
        }
        overall_healthy = False

    # 2. Redis/Celery Check
    try:
        start = time.time()
        redis_client = redis.from_url(os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'))
        redis_client.ping()
        duration = (time.time() - start) * 1000
        checks['redis'] = {
            'status': 'healthy',
            'response_time': f'{duration:.2f}ms',
            'message': 'Redis connection OK'
        }
    except Exception as e:
        checks['redis'] = {
            'status': 'unhealthy',
            'message': str(e)
        }
        overall_healthy = False

    # 3. Email Service Check
    try:
        start = time.time()
        mail_server = current_app.extensions.get('mail')
        if mail_server:
            mail_settings = current_app.config.get('MAIL_SERVER')
            if mail_settings:
                duration = (time.time() - start) * 1000
                checks['email'] = {
                    'status': 'healthy',
                    'response_time': f'{duration:.2f}ms',
                    'message': f'Mail server: {mail_settings}'
                }
            else:
                checks['email'] = {
                    'status': 'warning',
                    'message': 'Mail server not configured'
                }
        else:
            checks['email'] = {
                'status': 'warning',
                'message': 'Mail extension not initialized'
            }
    except Exception as e:
        checks['email'] = {
            'status': 'unhealthy',
            'message': str(e)
        }
        overall_healthy = False

    # 4. Sentry Check
    sentry_dsn = os.environ.get('SENTRY_DSN')
    if sentry_dsn:
        checks['sentry'] = {
            'status': 'healthy',
            'message': 'Sentry configured',
            'pii_enabled': False,
        }
    else:
        checks['sentry'] = {
            'status': 'warning',
            'message': 'Sentry not configured (add SENTRY_DSN to .env)'
        }

    # 5. Storage/Write Permission Check
    try:
        from flask import current_app
        instance_path = current_app.instance_path
        os.makedirs(instance_path, exist_ok=True)
        test_file = os.path.join(instance_path, '.health_check')
        with open(test_file, 'w') as f:
            f.write('ok')
        os.remove(test_file)
        checks['storage'] = {
            'status': 'healthy',
            'message': f'Write permission OK: {instance_path}'
        }
    except Exception as e:
        checks['storage'] = {
            'status': 'warning',
            'message': str(e)
        }

    return jsonify({
        'success': True,
        'overall_healthy': overall_healthy,
        'checks': checks,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    })


@health_bp.route('/superadmin/api/health/stats', methods=['GET'])
def api_health_stats():
    """Get application statistics."""
    from app.models import User, UserRole, School, SchoolStatus, Course, Quiz, Assignment, ActivityLog
    from sqlalchemy import func
    from app.extensions import db

    # Database stats
    users_by_role = db.session.query(
        User.role, func.count(User.id)
    ).group_by(User.role).all()

    # Check if models exist in registry
    registry = str(db.Model.registry._class_registry)
    has_course = 'Course' in registry
    has_quiz = 'Quiz' in registry
    has_assignment = 'Assignment' in registry
    has_activity_log = 'ActivityLog' in registry

    stats = {
        'users': {
            'total': User.query.count(),
            'by_role': {role.value: count for role, count in users_by_role}
        },
        'schools': {
            'total': School.query.count(),
            'active': School.query.filter_by(status=SchoolStatus.ACTIVE).count(),
            'pending': School.query.filter_by(status=SchoolStatus.PENDING).count(),
            'suspended': School.query.filter_by(status=SchoolStatus.SUSPENDED).count(),
        },
        'content': {
            'courses': Course.query.count() if has_course else 0,
            'quizzes': Quiz.query.count() if has_quiz else 0,
            'assignments': Assignment.query.count() if has_assignment else 0,
        },
        'activity': {
            'last_24h': ActivityLog.query.filter(
                ActivityLog.created_at >= func.now() - 1
            ).count() if has_activity_log else 0,
        },
        'system': {
            'python_version': os.sys.version.split()[0],
            'platform': os.sys.platform,
        }
    }

    return jsonify({'success': True, 'stats': stats})


@health_bp.route('/superadmin/api/health/test-email', methods=['POST'])
def api_test_email_health():
    """Send test email to verify email configuration."""
    from app.services.email_service import send_email

    data = request.get_json() or {}
    recipient = data.get('email', current_user.email if hasattr(current_user, 'email') else None)

    if not recipient:
        return jsonify({'success': False, 'message': 'Email recipient required'}), 400

    ok = send_email(
        subject='Health Check - Email Test',
        recipients=[recipient],
        html_body=(
            '<div style="font-family:sans-serif;padding:20px">'
            '<h2 style="color:#0282c6">Email Test ✓</h2>'
            '<p>Health check email test successful.</p>'
            f'<p>Sent to: <strong>{recipient}</strong></p>'
            f'<p>Time: {time.strftime("%Y-%m-%d %H:%M:%S")}</p>'
            '</div>'
        ),
    )

    if ok:
        return jsonify({'success': True, 'message': f'Test email sent to {recipient}'})
    return jsonify({'success': False, 'message': 'Failed to send email. Check Mailtrap config.'}), 500


@health_bp.route('/superadmin/api/health/clear-cache', methods=['POST'])
def api_clear_cache():
    """Clear all application cache."""
    from flask import current_app

    try:
        # Get cache instance from extensions
        cache_instance = current_app.extensions.get('cache')

        if not cache_instance:
            return jsonify({'success': False, 'message': 'Cache not initialized'}), 500

        # Clear all cache
        cache_instance.clear()

        return jsonify({
            'success': True,
            'message': 'Cache berhasil dibersihkan',
            'details': 'Semua data cache telah dihapus'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Gagal membersihkan cache: {str(e)}'
        }), 500
