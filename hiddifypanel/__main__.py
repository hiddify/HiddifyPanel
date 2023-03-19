import click
from flask.cli import FlaskGroup

from . import create_app_wsgi,create_cli_app


@click.group(cls=FlaskGroup, create_app=create_cli_app)
def main():
    """Management script for the hiddifypanel application."""


if __name__ == "__main__":  # pragma: no cover
    main()
