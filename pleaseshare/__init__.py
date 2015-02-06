"""
PleaseShare module.
"""

__package__ = "pleaseshare"

__all__ = ['__main__', 'tasks', 'torrent', 'app', 'forms', 'default_config',
           'static_routes', 'utils', 'app', 'run', 'db']

from pleaseshare.app import run, db, app

__main__ = run
