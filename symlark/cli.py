"""Console script for symlark."""

__author__ = """Diane Knappett"""
__contact__ = 'diane.knappett@stfc.ac.uk'
__copyright__ = "Copyright 2020 United Kingdom Research and Innovation"
__license__ = "BSD - see LICENSE file in top-level package directory"
import sys
from symlark.symlark import main as symlark_main


def main():
    """Console script for symlark."""
    args = sys.argv[1:]

    if len(args) != 2:
        print("[ERROR] Must provide 'gws' and 'archive' directories as 2 command-line arguments.")
        sys.exit(0)

    gws_dir, arc_dir = args
    symlark_main(gws_dir, arc_dir)


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
