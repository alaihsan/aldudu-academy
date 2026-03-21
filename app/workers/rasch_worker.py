"""
Celery Workers for Rasch Analysis

Background tasks untuk menjalankan Rasch Model analysis.
"""

import logging
from datetime import datetime
from typing import Optional

from app.celery_app import init_celery
from app.models.rasch import RaschAnalysis, RaschAnalysisStatus, RaschThresholdLog, ThresholdCheckType, ThresholdAction

logger = logging.getLogger(__name__)


def run_rasch_analysis_task(analysis_id: int) -> dict:
    """
    Run Rasch analysis untuk analysis_id tertentu.
    
    Task ini akan:
    1. Load data dari database
    2. Jalankan JMLE algorithm
    3. Save results
    
    Args:
        analysis_id: ID dari rasch_analyses record
        
    Returns:
        dict: Result status
    """
    from app import create_app, db
    from app.services.rasch_analysis_service import RaschAnalysisService
    
    app = create_app()
    
    with app.app_context():
        try:
            # Get analysis record
            analysis = RaschAnalysis.query.get(analysis_id)
            
            if not analysis:
                logger.error(f"Analysis {analysis_id} not found")
                return {'status': 'failed', 'error': 'Analysis not found'}
            
            # Update status
            analysis.status = RaschAnalysisStatus.PROCESSING.value
            analysis.started_at = datetime.utcnow()
            analysis.status_message = "Starting JMLE algorithm..."
            db.session.commit()
            
            logger.info(f"Starting Rasch analysis {analysis_id} for {analysis.name}")
            
            # Run analysis
            service = RaschAnalysisService(analysis_id=analysis_id)
            success = service.run_analysis()
            
            if success:
                logger.info(f"Rasch analysis {analysis_id} completed successfully")
                return {
                    'status': 'completed',
                    'analysis_id': analysis_id,
                    'converged': analysis.status == RaschAnalysisStatus.COMPLETED.value,
                    'num_persons': analysis.num_persons,
                    'num_items': analysis.num_items,
                }
            else:
                logger.warning(f"Rasch analysis {analysis_id} completed with issues")
                return {
                    'status': 'partial',
                    'analysis_id': analysis_id,
                    'error': analysis.error_message,
                }
                
        except Exception as e:
            logger.error(f"Rasch analysis {analysis_id} failed: {e}", exc_info=True)
            
            # Update analysis status
            if analysis:
                analysis.status = RaschAnalysisStatus.FAILED.value
                analysis.error_message = str(e)
                analysis.completed_at = datetime.utcnow()
                db.session.commit()
            
            return {
                'status': 'failed',
                'analysis_id': analysis_id,
                'error': str(e),
            }


# Celery task decorator (akan di-register saat autodiscover)
try:
    from app.celery_app import make_celery
    from flask import current_app
    
    # Get celery instance from app
    celery = None
    
    @current_app.before_first_request
    def register_tasks():
        global celery
        celery = current_app.extensions.get('celery')
        
        if celery:
            @celery.task(bind=True, max_retries=3, default_retry_delay=60)
            def rasch_analysis(self, analysis_id: int) -> dict:
                """
                Celery task untuk menjalankan Rasch analysis.
                
                Usage:
                    rasch_analysis.delay(analysis_id=1)
                """
                try:
                    return run_rasch_analysis_task(analysis_id)
                except Exception as exc:
                    # Retry dengan exponential backoff
                    raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
    
except Exception:
    # Fallback untuk testing tanpa Celery
    logger.info("Celery not configured, using sync execution")
