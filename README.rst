PleaseShare
===========

PleaseShare is a file-sharing website that aims to decentralize
file-sharing through the use of bittorrent, DHT, and webseeds.


Get started
-----------

Retrieve the project from gitorious_ or github_:

.. _gitorious: https://git.gitorious.org/pleaseshare/pleaseshare.git
.. _github: https://github.com/mathieui/pleaseshare.git

::

    $ git clone git://gitorious.org/pleaseshare/pleaseshare.git

Then install the dependencies (assuming you are using a virtualenv):

::

    $ cd pleaseshare
    $ pip install -r requirements.txt
    $ mkdir -p pleaseshare/uploads

Now you can start coding, testing, etc.

Install
-------

(do the Get started thing before that)

First, edit the variables in ``pleaseshare/settings.cfg`` to fit your needs,
everything is properly documented inside the file. If a ``local_settings.py``
is available in the same directory, it will be used to override those defaults.
You MUST consider changing the following:

- ``SECRET_KEY`` and ``WTF_CSRF_SECRET_KEY``, both set to the value of a local ``key`` variable
- ``SQLALCHEMY_DATABASE_URI`` for database connection settings
- ``MAX_CONTENT_LENGTH`` for the maximal upload file size

Once everything is set, you only have to create the database:

::

    $ ./make_db.py


In order to deploy PleaseShare, you can follow the flask `deployment guide`_.

.. _deployment guide: http://flask.pocoo.org/docs/deploying/

My favourite deployment option is uwsgi + nginx/lighttpd

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
        client_max_body_size    200k;

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


.. _supervisord: http://supervisord.org/

But manually running ``uwsgi uwsgi.ini`` works too.


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

License
-------

PleaseShare is released under the terms of the `GNU Affero General
Public License v3`_.

PleaseShare also contains some files from the `Deluge torrent client`_,
which is licenced under the `GNU General Public Licence v3`_.

.. _GNU Affero General Public License v3 : http://www.gnu.org/licenses/agpl-3.0.html
.. _Deluge torrent client : http://deluge-torrent.org/
.. _GNU General Public Licence v3 : https://www.gnu.org/licenses/gpl-3.0.html


