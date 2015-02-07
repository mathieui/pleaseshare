"""
PleaseShare main application file

Mostly contains functions that require the app/db and
therefore couldn’t be split up in another module.
"""
import flask
import logging
import datetime
import werkzeug
import subprocess

log = logging.getLogger(__name__)

from flask import flash
from flask_wtf.csrf import CsrfProtect
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.babel import Babel, gettext as _

from uuid import uuid4
from os import makedirs, environ
from shutil import rmtree
from hashlib import sha256
from urllib.parse import quote
from os.path import basename, getsize, exists, join as joinpath, realpath, abspath

from pleaseshare.tasks import Archive, create_torrent
from pleaseshare.utils import parse_form, can_delete, remove_uuid_from_session
from pleaseshare.forms import UploadForm, DeleteForm
from pleaseshare.static_routes import static_pages


app = flask.Flask(__name__)
app.config.from_object('pleaseshare.default_settings')
app.config.from_envvar('PLEASESHARE_CONFIG', silent=True)
app.config.from_pyfile('local_settings.cfg', silent=True)
app.jinja_env.add_extension('jinja2.ext.i18n')

csrf = CsrfProtect(app)
babel = Babel(app, default_locale='en')
db = SQLAlchemy(app)

dynamic_pages = flask.Blueprint('dynamic', __name__, template_folder='templates')

@dynamic_pages.route("/view/<filename>")
def view(filename):
    """
    Show the page associated with an upload
    """
    upload_obj = db.session.query(Upload).get(filename)
    if not upload_obj:
        flash(_('Upload not found'), 'error')
        return flask.redirect(flask.url_for("dynamic.home"))
    form = DeleteForm()
    return flask.render_template("view.html", object=upload_obj,
                                 can_delete=can_delete(filename), form=form)

@dynamic_pages.route('/delete', methods=['POST'])
def delete():
    """
    Delete an upload (requires a password that matches the one stored)
    """
    form = DeleteForm()
    if not form.validate_on_submit():
        flash(_('Missing field in deletion form.'), 'error')
        return flask.redirect(flask.url_for("dynamic.home"))

    uuid = form.object_id.data

    upload_obj = db.session.query(Upload).get(uuid)

    if not upload_obj:
        flash(_('Uploaded file {} not found.').format(uuid), 'error')
        return flask.redirect(flask.url_for("dynamic.home"))

    name = upload_obj.name

    passwordless_deletion = can_delete(uuid)

    if not passwordless_deletion and not upload_obj.password:
        flash(_('Uploaded file {} cannot be deleted '
                '(no deletion password exists).').format(name),
              'error')
        return flask.redirect(flask.url_for("dynamic.view", filename=uuid))
    elif not passwordless_deletion:
        passwd = form.deletion_password.data
        passwd = sha256(passwd.encode('utf-8', errors='ignore')).hexdigest()
    else:
        passwd = ''

    if passwordless_deletion or passwd == upload_obj.password:
        db.session.delete(upload_obj)
        db.session.commit()
        rmtree(joinpath(app.config['UPLOAD_FOLDER'], uuid))
        if passwordless_deletion:
            remove_uuid_from_session(uuid)
        flash(_('Upload {} deleted successfully.').format(name), 'success')
    else:
        flash(_('Wrong password'), 'error')
        return flask.redirect(flask.url_for("dynamic.view", filename=uuid))

    return flask.redirect(flask.url_for("dynamic.home"))

@dynamic_pages.route('/', methods=['GET'])
def home():
    """Main page, with the upload form"""
    form = UploadForm()
    return flask.render_template("home.html", title="Index", form=form)

@dynamic_pages.route('/upload', methods=["POST"])
def upload():
    """Upload target"""
    form = UploadForm()
    if not form.validate_on_submit():
        flash(_('File required.'), 'error')
        return flask.redirect(flask.url_for("dynamic.home"))

    file = form.file.data
    params = parse_form(form, app.config)
    try:
        upload = handle_uploaded_file(file, params)
    except Exception:
        log.error('Unspecified error', exc_info=True)
        flash(_('Server error'), 'error')
        return flask.redirect(flask.url_for("dynamic.home"))
    else:
        if not 'uploads' in flask.session:
            flask.session['uploads'] = []
        flask.session['uploads'].append((datetime.datetime.now(), upload.uuid, upload.name))
    return flask.redirect(flask.url_for("dynamic.view", filename=upload.uuid))

def handle_uploaded_file(file_storage, params):
    """
    Write a file to the disk, and in the database.

    returns the Upload object
    """
    uuid = str(uuid4())
    folder = joinpath(app.config['UPLOAD_FOLDER'], uuid)
    makedirs(folder)
    filepath = realpath(abspath(joinpath(folder, werkzeug.secure_filename(file_storage.filename))))
    filename = basename(filepath)
    file_storage.save(filepath)

    size = getsize(filepath)

    multifile = False
    data_path = filepath
    if params.extract:
        try:
            archive = Archive(filepath, allow_compressed=app.config['ALLOW_COMPRESSED'])
            archive_size = archive.size()
            if archive_size <= app.config['MAX_CONTENT_LENGTH'] and archive.extract():
                multifile = True
                data_path = archive.extracted_location()
                filename = archive.extracted_name()
                size = archive_size
            elif archive_size > app.config['MAX_CONTENT_LENGTH']:
                flash(_('Extracted archive too big, fallback to single-file upload.'), 'error')
        except Exception:
            flash(_('Invalid archive, fallback to single-file upload.'), 'error')
            log.error('Invalid archive', exc_info=True)

    size = round(size / (1024.0**2), 2)
    uploaded = Upload(uuid=uuid, name=filename, size=size, private=params.private,
                      multifile=multifile, description=params.description,
                      date=datetime.datetime.now())
    relative_url = quote(uploaded.get_file())
    webseeds = [app.config['UPLOADED_FILES_URL'] + relative_url]
    webseeds.extend([webseed + relative_url for webseed in  app.config['OTHER_WEBSEEDS']])
    webseeds.extend(params.webseeds)

    torrent = create_torrent(data_path, "Created with pleaseshare", webseeds,
                             params.trackers, params.private)
    uploaded.magnet = torrent.save(joinpath(folder, "%s.torrent" % filename))

    if params.uploader:
        uploaded.uploader = params.uploader
    if params.password:
        uploaded.password = sha256(params.password.encode('utf-8', errors='ignore')).hexdigest()
    db.session.add(uploaded)
    db.session.commit()
    return uploaded

class Upload(db.Model):
    """A database record describing a specific upload"""
    __tablename__ = "uploads"
    uuid = db.Column(db.String(36), primary_key=True)
    uploader = db.Column(db.String(32), default='Anonymous')
    name = db.Column(db.String(32))
    password = db.Column(db.String(64), default='')
    date = db.Column(db.Date)
    magnet = db.Column(db.Text(200))
    description = db.Column(db.Text(500))
    size = db.Column(db.String(8))
    private = db.Column(db.Boolean, default=False)
    multifile = db.Column(db.Boolean, default=False)

    def __str__(self):
        """Print out object details for debug purposes"""
        return '%s - %s | %s - %s' % (self.uploader, self.uuid, self.name, self.date)

    __repr__ = __str__

    def get_torrent_file(self):
        return '%s/%s.torrent' % (self.uuid, self.name)

    def get_direct_torrent_file(self, config):
        return "%s%s" %  (config['UPLOADED_FILES_URL'], self.get_torrent_file())

    def get_file(self):
        if self.multifile:
            return '%s' % (self.uuid)
        else:
            return '%s/%s' % (self.uuid, self.name)

    def get_direct_file(self, config):
        return "%s%s" % (config['UPLOADED_FILES_URL'], self.get_file())

    def get_files(self, config):
        """
        Return a pretty file tree, with file sizes, using `tree`.
        Store the result in a file to avoid frequent subprocess calls.
        """
        filelist = joinpath(config['UPLOAD_FOLDER'], self.uuid, 'file_list')
        folder = joinpath(config['UPLOAD_FOLDER'], self.uuid, self.name)
        if exists(filelist):
            with open(filelist, 'r', encoding='utf-8') as fdes:
                return fdes.read()
        else:
            try:
                env = {'LC_ALL': 'en_US.UTF-8', 'PATH': environ.get('PATH', '')}
                proc = subprocess.Popen(['tree', '--noreport', '-ah', folder],
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                        env=env)
                stdout, stderr = proc.communicate()
            except Exception:
                log.error('Call to `tree` failed.', exc_info=True)
                files = ''
            else:
                output = stdout.decode('utf-8').split('\n')
                output[0] = str(self.name)
                files = '\n'.join(output)
            finally:
                with open(filelist, 'w', encoding='utf-8') as fdes:
                    fdes.write(files)
            return files

@babel.localeselector
def get_locale():
    """Autodetect the locale of the user"""
    return flask.request.accept_languages.best_match(['fr', 'en'])

app.register_blueprint(static_pages, url_prefix=app.config['STATIC_PAGES_PREFIX'])
app.register_blueprint(dynamic_pages, url_prefix=app.config['DYNAMIC_PAGES_PREFIX'])

def run(*args, **kwargs):
    app.run(*args, **kwargs)

