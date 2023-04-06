"""Console script for symlark."""

__author__ = """Diane Knappett"""
__contact__ = 'diane.knappett@stfc.ac.uk'
__copyright__ = "Copyright 2020 United Kingdom Research and Innovation"
__license__ = "BSD - see LICENSE file in top-level package directory"
import sys
import click


@click.command()
def main(args=None):
    """Console script for symlark."""
    click.echo("Replace this message by putting your code into "
               "symlark.cli.main")
    click.echo("See click documentation at https://click.palletsprojects.com/")
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
