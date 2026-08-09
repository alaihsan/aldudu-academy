"""
Blueprint Registry

Central, explicit list of every blueprint registered on the app — the
Flask analog of Django's INSTALLED_APPS. Every feature now lives in its
own app/<feature>/ package (the per-app restructure is complete —
app/blueprints/ no longer exists); only the import lines here need to
change as features evolve.
"""


def register_blueprints(app):
    from app.auth.routes import auth_bp
    from app.courses.routes import courses_bp, courses_pages_bp
    from app.pages.routes import main_bp
    from app.quiz.routes import quiz_bp, quiz_pages_bp
    from app.discussion.routes import discussion_bp, discussion_pages_bp
    from app.kbm.routes import kbm_bp
    from app.issues.routes import issues_bp, issues_pages_bp
    from app.admin.routes import admin_bp
    from app.superadmin.routes import superadmin_bp
    from app.tickets.routes import tickets_bp
    from app.gradebook.routes import gradebook_bp
    from app.assignment.routes import assignment_bp, assignment_api_bp
    from app.whats_new.routes import whats_new_view_bp
    from app.trash.routes import trash_bp
    from app.health.routes import health_bp
    from app.metrics.routes import metrics_bp
    from app.content.routes import content_bp, content_files_bp
    from app.classroom.routes import classroom_bp, classroom_pages_bp

    blueprints = [
        main_bp,
        auth_bp,
        courses_bp,
        courses_pages_bp,
        quiz_bp,
        quiz_pages_bp,
        discussion_bp,
        discussion_pages_bp,
        kbm_bp,
        issues_bp,
        issues_pages_bp,
        admin_bp,
        superadmin_bp,
        tickets_bp,
        gradebook_bp,
        assignment_bp,
        assignment_api_bp,
        whats_new_view_bp,
        trash_bp,
        health_bp,
        metrics_bp,
        content_bp,
        content_files_bp,
        classroom_bp,
        classroom_pages_bp,
    ]
    for bp in blueprints:
        app.register_blueprint(bp)
