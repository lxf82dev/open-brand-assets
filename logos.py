#!/usr/bin/env python3
"""Repository entrypoint; the installable skill contains the standalone CLI."""
from pathlib import Path
import runpy

if __name__ == '__main__':
    runpy.run_path(str(Path(__file__).resolve().parent / 'skills/find-brand-logo/scripts/logos.py'), run_name='__main__')
