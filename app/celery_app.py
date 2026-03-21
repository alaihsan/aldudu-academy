"""
Celery Configuration for Aldudu Academy

Digunakan untuk background processing:
- Rasch Model Analysis
- Email notifications
- Report generation
"""

from celery import Celery
from flask import Flask


def make_celery(app: Flask) -> Celery:
    """
    Create Celery instance with Flask app context.
    
    Usage:
        celery = make_celery(app)
    """
    celery = Celery(
        app.import_name,
        broker=app.config.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
        backend=app.config.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
        include=[
            'app.workers.rasch_worker',
        ]
    )
    
    # Celery configuration
    celery.conf.update(
        # Task settings
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='Asia/Jakarta',
        enable_utc=True,
        
        # Execution settings
        task_track_started=True,
        task_time_limit=3600,  # 1 hour max
        task_soft_time_limit=3000,
        
        # Rate limiting
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=100,
        
        # Retry settings
        task_default_retry_delay=60,
        task_max_retries=3,
        
        # Result settings
        result_expires=3600,  # 1 hour
        result_persistent=True,
    )
    
    # Flask context processor
    class ContextTask(celery.Task):
        """Task that runs within Flask app context"""
        
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    
    return celery


def init_celery(app: Flask = None) -> Celery:
    """
    Initialize Celery with Flask app.
    
    Usage:
        # In create_app()
        celery = init_celery(app)
    """
    if app is None:
        return None
    
    celery = make_celery(app)
    
    # Auto-discover tasks
    celery.autodiscover_tasks(['app.workers'])
    
    return celery
