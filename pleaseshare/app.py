"""
PleaseShare main application file

Mostly contains functions that require the app/db and
therefore couldn’t be split up in another module.
"""
import flask
import logging
import werkzeug
import subprocess

log = logging.getLogger(__name__)

from flask import flash
from flask_wtf.csrf import CsrfProtect
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.babel import Babel, gettext as _

from uuid import uuid4
from os import makedirs
from shutil import rmtree
from hashlib import sha256
from urllib.parse import quote
from os.path import basename, getsize, exists, join as joinpath, realpath, abspath

from pleaseshare.tasks import Archive, create_torrent, parse_form
from pleaseshare.forms import UploadForm, DeleteForm
from pleaseshare.static_routes import static_pages


app = flask.Flask(__name__)
app.config.from_pyfile('settings.cfg')
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
    return flask.render_template("view.html", object=upload_obj, form=form)

@dynamic_pages.route('/delete', methods=['POST'])
def delete():
    """
    Delete an upload (requires a password that matches the one stored)
    """
    form = DeleteForm()
    if not form.validate_on_submit():
        flash(_('Missing field in deletion form.'), 'error')
        return flask.redirect(flask.url_for("dynamic.home"))
    upload_obj = db.session.query(Upload).get(form.object_id.data)

    if not upload_obj:
        flash(_('Uploaded file %s not found.') % form.object_id.data, 'error')
        return flask.redirect(flask.url_for("dynamic.home"))
    if not upload_obj.password:
        flash(_('Uploaded file %s cannot be deleted (no deletion password exists).') % form.object_id.data, 'error')
        return flask.redirect(flask.url_for("dynamic.view", filename=form.object_id.data))

    passwd = sha256(form.deletion_password.data.encode('utf-8', errors='ignore')).hexdigest()

    if passwd == upload_obj.password:
        db.session.delete(upload_obj)
        db.session.commit()
        rmtree(joinpath(app.config['UPLOAD_FOLDER'], upload_obj.uuid))
        flash(_('Upload deleted successfully.'), 'success')
    else:
        flash(_('Wrong password'), 'error')
        return flask.redirect(flask.url_for("dynamic.view", filename=upload_obj.uuid))

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
    uploaded = Upload(uuid=uuid, name=filename, size=size, private=params.private)
    uploaded.multifile = multifile
    relative_url = quote(uploaded.get_file())
    webseeds = [webseed + relative_url for webseed in  app.config['OTHER_WEBSEEDS']]
    webseeds.append(app.config['UPLOADED_FILES_URL'] + relative_url)
    webseeds.extend(params.webseeds)

    torrent = create_torrent(data_path, "Created with pleaseshare", webseeds,
                             params.trackers, params.private)
    uploaded.magnet = torrent.save(joinpath(folder, "%s.torrent" % filename))
    uploaded.description = params.description

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
            with open(filelist, 'r') as fd:
                return fd.read()
        else:
            try:
                proc = subprocess.Popen(['tree', '--noreport', '-ah', folder], stdout=subprocess.PIPE)
                res = proc.communicate()[0]
            except OSError:
                res = b''
                log.error('Call to `tree` failed.')
            output = res.decode('utf-8').split('\n')
            output[0] = str(self.name)
            files = '\n'.join(output)
            with open(filelist, 'w') as fdes:
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

