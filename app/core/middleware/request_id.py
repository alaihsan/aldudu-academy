"""
Request ID Middleware

Adds unique request ID for tracing and debugging.
"""

import uuid
from flask import g, request


def register_request_id(app):
    """Register request ID middleware."""

    @app.before_request
    def set_request_id():
        """Set request ID from header or generate new one."""
        g.request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))

    @app.after_request
    def add_request_id_header(response):
        """Add request ID to response headers."""
        response.headers['X-Request-ID'] = g.get('request_id', '')
        return response
