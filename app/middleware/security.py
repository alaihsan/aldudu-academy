"""
Security Middleware

Adds security headers and validates content types for API requests.
"""

from flask import request, abort, current_app


def register_security_middleware(app):
    """Register security middleware."""

    @app.before_request
    def validate_content_type():
        """Validate Content-Type header for API POST/PUT requests."""
        if request.path.startswith('/api/') and request.method in ('POST', 'PUT'):
            if request.content_type and 'multipart/form-data' not in request.content_type:
                if 'application/json' not in request.content_type and \
                   'application/x-www-form-urlencoded' not in request.content_type:
                    abort(415, description='Unsupported Media Type. Use application/json.')

    @app.after_request
    def add_security_headers(response):
        """Add security headers to all responses."""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response
