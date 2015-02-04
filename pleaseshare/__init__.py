"""
PleaseShare module.
"""

__package__ = "pleaseshare"

__all__ = ['__main__', 'tasks', 'torrent', 'app', 'forms',
           'static_routes', 'run', 'db']

from pleaseshare.app import run, db, app

__main__ = run
