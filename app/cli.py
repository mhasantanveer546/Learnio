import click
from flask.cli import with_appcontext

from app.extensions import db
from app.models import User


@click.command("create-admin")
@click.argument("email")
@with_appcontext
def create_admin(email):
    """Promotes an existing user to admin by email.
    Usage: flask create-admin user@example.com
    """
    user = User.query.filter_by(email=email).first()

    if not user:
        click.echo(f"No user found with email '{email}'.")
        return

    if user.is_admin:
        click.echo(f"'{email}' is already an admin.")
        return

    user.is_admin = True
    db.session.commit()
    click.echo(f"'{email}' is now an admin.")