PleaseShare
===========

PleaseShare is a file-sharing website that aims to decentralize
file-sharing through the use of bittorrent, DHT, and webseeds.

A demo instance is available at share.jeproteste.info_.

Get started
-----------

Retrieve the project from gitorious_, github_, or `my own git server`_:

::

    $ git clone git://gitorious.org/pleaseshare/pleaseshare.git

Then install the dependencies (assuming you are using a virtualenv):

::

    $ cd pleaseshare
    $ pip install -r requirements.txt

You also need **Python 3.4**.

After this, you can start coding, testing, translating (see the bottom section of this page for details), etc.

Install
-------

(do the Get started thing before that)

First, copy the ``pleaseshare/default_settings.py`` file to ``pleaseshare/local_settings.cfg``
and edit it to fit your needs. Alternatively, you can set the ``$PLEASESHARE_CONFIG``
environment variable to the absolute path of your config file (if a ``local_settings.cfg`` file
is present, it will still override it, though). Every option is commented and has a purpose,
and you MUST consider changing the following:

- ``SECRET_KEY`` and ``WTF_CSRF_SECRET_KEY``, both set to the value of a local ``key`` variable
- ``SQLALCHEMY_DATABASE_URI`` for database connection settings
- ``MAX_CONTENT_LENGTH`` for the maximal upload file size

Once everything is set, you only have to create the database:

::

    $ ./make_db.py

In order to deploy PleaseShare, you can follow the flask `deployment guide`_.

.. _deployment guide: http://flask.pocoo.org/docs/deploying/

My favourite deployment option is uwsgi with nginx or lighttpd.

Example uwsgi+nginx deployment
------------------------------

``uwsgi.ini`` file:

::

    [uwsgi]
    socket = 127.0.0.1:4444
    master = true
    plugin = python3
    chdir = /home/flask/pleaseshare/
    module = pleaseshare:app
    processes = 4

Nginx configuration section:

::

    server {
        listen                  80;
        server_name             share.example.com;
        client_max_body_size    50m;

        location / {
            include             uwsgi_params;
            uwsgi_pass          127.0.0.1:4444;
        }
    }

    server {
        listen                  80;
        server_name             files.example.com;

        location / {
            root                /home/flask/pleaseshare/uploads/;
            autoindex           off;
        }
    }

(assuming ``UPLOAD_FOLDER`` is set to ``"uploads"``, and ``UPLOADED_FILES_URL``
to ``"http://files.example.com/"``)


I also usually use supervisord_ to manage my python web applications:

::

    [program:share]
    command=uwsgi uwsgi.ini
    directory=/home/flask/pleaseshare/
    user=flask
    redirect_stderr=true
    autostart=true
    autorestart=true

But manually running ``uwsgi uwsgi.ini`` works fine too.

Misc
----

Some indications about how webseeds work might be in order.

- When the torrent has a single file, then it’s easy: the webseed is the complete url of the file.
- When the torrent is multifile, then the webseed url is the url of the parent directory (I’m talking about the torrents in PleaseShare, which are always contained in a parent directory named after the archive name).

For example, you upload a toto.tar.gz archive, you will have a url like /view/48a3-[…]/,
containing a 'toto' directory, which will contain the files inside the archive.

The webseed url should **not** contain the 'toto' directory, but the parent
level; and, of course, file indexing should be disabled, or the file generated
by the webserver might cause problems to some torrent clients.

So let’s say you want to add a source to the torrent using your personal
webserver (again for the toto.tar.gz torrent), you will have to put something
like that as a webseed: http://my.example.com/uploads/ which will contain a ``toto``
directory.

Reporting bugs
--------------

As of now, no public bug tracker is available, but you can come report bugs or say a nice thing or
two on the XMPP chatroom `share@chat.jeproteste.info`_. You can also send me emails to
`pleaseshare@mathieui.net`_.

License
-------

PleaseShare is released under the terms of the `GNU Affero General
Public License v3`_.

PleaseShare also contains some files from the `Deluge torrent client`_,
which is licenced under the `GNU General Public Licence v3`_.

Contributors
------------

- mathieui - main developer
- Cynddl - UI design magic
- kaliko - fixes

Notes on translating
--------------------

pybabel is currently `broken on python 3.4`_, so you will need to patch babel 1.3 with:

::

    diff --git a/babel/messages/frontend.py b/babel/messages/frontend.py
    index 144bc98..94e09e9 100755
    --- a/babel/messages/frontend.py
    +++ b/babel/messages/frontend.py
    @@ -128,7 +128,7 @@ class compile_catalog(Command):
     
             for idx, (locale, po_file) in enumerate(po_files):
                 mo_file = mo_files[idx]
    -            infile = open(po_file, 'r')
    +            infile = open(po_file, 'rb')
                 try:
                     catalog = read_po(infile, locale)
                 finally:
    @@ -439,7 +439,7 @@ class init_catalog(Command):
             log.info('creating catalog %r based on %r', self.output_file,
                      self.input_file)
     
    -        infile = open(self.input_file, 'r')
    +        infile = open(self.input_file, 'rb')
             try:
                 # Although reading from the catalog template, read_po must be fed
                 # the locale in order to correctly calculate plurals
    @@ -554,7 +554,7 @@ class update_catalog(Command):
             if not domain:
                 domain = os.path.splitext(os.path.basename(self.input_file))[0]
     
    -        infile = open(self.input_file, 'U')
    +        infile = open(self.input_file, 'rb')
             try:
                 template = read_po(infile)
             finally:
    @@ -566,7 +566,7 @@ class update_catalog(Command):
             for locale, filename in po_files:
                 log.info('updating catalog %r based on %r', filename,
                          self.input_file)
    -            infile = open(filename, 'U')
    +            infile = open(filename, 'rb')
                 try:
                     catalog = read_po(infile, locale=locale, domain=domain)
                 finally:
    @@ -577,7 +577,7 @@ class update_catalog(Command):
                 tmpname = os.path.join(os.path.dirname(filename),
                                        tempfile.gettempprefix() +
                                        os.path.basename(filename))
    -            tmpfile = open(tmpname, 'w')
    +            tmpfile = open(tmpname, 'wb')
                 try:
                     try:
                         write_po(tmpfile, catalog,
    @@ -760,7 +760,7 @@ class CommandLineInterface(object):
     
             for idx, (locale, po_file) in enumerate(po_files):
                 mo_file = mo_files[idx]
    -            infile = open(po_file, 'r')
    +            infile = open(po_file, 'rb')
                 try:
                     catalog = read_po(infile, locale)
                 finally:
    @@ -1121,7 +1121,7 @@ class CommandLineInterface(object):
                 tmpname = os.path.join(os.path.dirname(filename),
                                        tempfile.gettempprefix() +
                                        os.path.basename(filename))
    -            tmpfile = open(tmpname, 'w')
    +            tmpfile = open(tmpname, 'wb')
                 try:
                     try:
                         write_po(tmpfile, catalog,

After that, you should be able to run ``make trans`` to extract/update
translations, and ``make compiletrans`` to generate an up-to-date ``.mo`` file.

.. _GNU Affero General Public License v3 : http://www.gnu.org/licenses/agpl-3.0.html
.. _Deluge torrent client : http://deluge-torrent.org/
.. _GNU General Public Licence v3 : https://www.gnu.org/licenses/gpl-3.0.html
.. _share.jeproteste.info: http://share.jeproteste.info
.. _supervisord: http://supervisord.org/
.. _gitorious: https://git.gitorious.org/pleaseshare/pleaseshare.git
.. _github: https://github.com/mathieui/pleaseshare.git
.. _my own git server: http://git.jeproteste.info/pleaseshare
.. _broken on python 3.4: https://github.com/mitsuhiko/babel/issues/91
.. _share@chat.jeproteste.info: xmpp:share@chat.jeproteste.info?join
.. _pleaseshare@mathieui.net: mailto:pleaseshare@mathieui.net
