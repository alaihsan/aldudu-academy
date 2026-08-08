"""
Request Logging Middleware

Logs slow requests for performance monitoring.
"""

import time
from flask import g, request


def register_request_logging(app):
    """Register request logging middleware."""

    @app.before_request
    def start_timer():
        """Start request timer."""
        g.start_time = time.time()

    @app.after_request
    def log_request(response):
        """Log slow requests (taking more than 1 second)."""
        duration = time.time() - g.get('start_time', time.time())
        if duration > 1.0:
            app.logger.warning(
                f"SLOW REQUEST: {request.method} {request.path} "
                f"took {duration:.2f}s [rid={g.get('request_id', 'unknown')}]"
            )
        return response
