# redefine the settings you want here
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'test.sqlite',                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

# Generate logs of errors/success
LOG = True
# Log file
LOG_FILE = 'data.log'
# Max file size (in MiB)
MAX_SIZE = 10
# Allow compressed archives to be decompressed or not
# (more CPU/RAM usage on upload), used only with OPTION_MULTIFILE
OPTION_DECOMPRESS = True
# Show a link to download the file directly or not
OPTION_DDL = False
# Show the "trackers" field when uploading
OPTION_TRACKERS = True
# Show the "webseeds" field when uploading
OPTION_WEBSEEDS = True
# Show the "untar" field when uploading
OPTION_MULTIFILE = True
