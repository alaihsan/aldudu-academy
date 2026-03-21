"""
Run Celery Worker for Aldudu Academy

Usage:
    python run_worker.py
    
Or with specific queue:
    python run_worker.py -Q default

For development without Redis:
    python run_worker.py --without-gossip --without-mingle --without-heartbeat
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

app = create_app()

if __name__ == '__main__':
    # Start Celery worker
    # Note: For production, use: celery -A run_worker.celery worker --loglevel=info
    
    from app.celery_app import make_celery
    
    celery = make_celery(app)
    
    # Default worker arguments
    argv = sys.argv[1:] or [
        'worker',
        '--loglevel=info',
        '--pool=solo',  # Use solo pool for better debugging on Windows
        '--without-gossip',
        '--without-mingle',
        '--without-heartbeat',
    ]
    
    # Start worker
    celery.start(argv)
