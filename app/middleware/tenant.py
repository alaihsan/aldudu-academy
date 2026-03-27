"""
Tenant Middleware

Handles multi-tenancy by resolving school from URL slug.
"""

from flask import g, request, abort
from app.extensions import cache


def register_tenant_middleware(app):
    """Register tenant resolution middleware."""

    @app.before_request
    def resolve_tenant():
        g.school = None

        path = request.path

        # Skip tenant resolution for non-tenant routes
        skip_prefixes = (
            '/static/', '/healthz', '/api/login', '/api/logout', '/api/session',
            '/register', '/verify-email/', '/forgot-password', '/reset-password/',
            '/login', '/superadmin/', '/',
        )

        # Check if path starts with /s/<slug>/
        if path.startswith('/s/'):
            parts = path.split('/')
            if len(parts) >= 3 and parts[1] == 's' and parts[2]:
                slug = parts[2]
                school = _get_school_by_slug(slug)
                if school is None:
                    abort(404, description='Sekolah tidak ditemukan')
                from app.models import SchoolStatus
                if school.status != SchoolStatus.ACTIVE:
                    abort(403, description='Sekolah belum aktif atau telah disuspend')
                g.school = school


@cache.memoize(timeout=300)
def _get_school_by_slug(slug):
    """Get school by slug with caching."""
    from app.models import School
    return School.query.filter_by(slug=slug).first()


def invalidate_school_cache(slug):
    """Invalidate school cache for a specific slug."""
    cache.delete_memoized(_get_school_by_slug, slug)
