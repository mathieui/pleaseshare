PleasShare
=================

PleaseShare is a file-sharing website that aims to decentralize file-sharing through the use of torrent, DHT, and webseeds.


License
-------

PleaseShare is released under the terms of the `GNU Affero General
Public License v3`_.

PleaseShare also contains some files from the `Deluge torrent client`_, which is licenced under the `GNU General Public Licence v3`_.

.. _GNU Affero General Public License v3 : http://www.gnu.org/licenses/agpl-3.0.html
.. _Deluge torrent client : http://deluge-torrent.org/
.. _GNU General Public Licence v3 : https://www.gnu.org/licenses/gpl-3.0.html


Get started
-----------

Retrieve the project from gitorious_:

.. _gitorious : https://git.gitorious.org/pleaseshare/pleaseshare.git

::

  $ git clone git://gitorious.org/pleaseshare/pleaseshare.git

Then install the dependencies:

::

  $ cd pleaseshare
  $ pip install -r requirements.txt

And manage it as you would do with any other django application.
Also, do not forget to use a REAL web server to handle the uploaded files, else the webseeds won’t work, since the built-in file server do not support resuming.
