"""
Blueprint Registry

Central, explicit list of every blueprint registered on the app — the
Flask analog of Django's INSTALLED_APPS. As features move out of
app/blueprints/ into their own app/<feature>/ packages (see the
per-app restructure), only the import lines here need to change.
"""


def register_blueprints(app):
    from app.auth.routes import auth_bp
    from app.blueprints.courses import courses_bp
    from app.blueprints.main import main_bp
    from app.quiz.routes import quiz_bp
    from app.blueprints.discussion import discussion_bp
    from app.issues.routes import issues_bp, issues_pages_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.superadmin import superadmin_bp
    from app.tickets.routes import tickets_bp
    from app.gradebook.routes import gradebook_bp
    from app.assignment.routes import assignment_bp
    from app.whats_new.routes import whats_new_view_bp
    from app.trash.routes import trash_bp
    from app.blueprints.health import health_bp
    from app.blueprints.metrics import metrics_bp

    blueprints = [
        main_bp,
        auth_bp,
        courses_bp,
        quiz_bp,
        discussion_bp,
        issues_bp,
        issues_pages_bp,
        admin_bp,
        superadmin_bp,
        tickets_bp,
        gradebook_bp,
        assignment_bp,
        whats_new_view_bp,
        trash_bp,
        health_bp,
        metrics_bp,
    ]
    for bp in blueprints:
        app.register_blueprint(bp)
