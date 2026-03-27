"""
CLI Commands for Aldudu Academy

Register custom Flask CLI commands.
"""


def register_cli_commands(app):
    """Register all CLI commands with the Flask app."""

    @app.cli.command('init-db')
    def init_db_command():
        """Initialize the database by creating all tables."""
        from app.extensions import db
        db.create_all()
        print('Initialized the database.')

    @app.cli.command('create-superadmin')
    def create_superadmin_command():
        """Create a new super admin user interactively."""
        import click
        from app.extensions import db
        from app.models import User, UserRole

        email = click.prompt('Email')
        name = click.prompt('Name')
        password = click.prompt('Password', hide_input=True, confirmation_prompt=True)

        existing = User.query.filter_by(email=email).first()
        if existing:
            print(f'User with email {email} already exists.')
            return

        user = User(
            name=name,
            email=email,
            role=UserRole.SUPER_ADMIN,
            is_active=True,
            email_verified=True,
            school_id=None,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f'Super Admin "{name}" created successfully.')
