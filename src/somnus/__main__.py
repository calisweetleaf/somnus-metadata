"""Module entry point so `python -m somnus` behaves like the `somnus` script."""

import sys

from somnus.cli import main

if __name__ == "__main__":
    sys.exit(main())
