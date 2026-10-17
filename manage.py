#!/usr/bin/env python

import os
import sys


def main():
    """Run Django management commands."""
    os.environ.setdefault(
        'DJANGO_SETTINGS_MODULE',
        'bank_project.settings',
    )

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django could not be imported. Make sure it is installed "
            "and that the virtual environment is activated."
        ) from exc

    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()