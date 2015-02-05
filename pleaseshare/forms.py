"""
Forms used by pleaseshare
"""
from flask_wtf import Form
from flask_wtf.file import FileField, FileRequired

from flask.ext.babel import lazy_gettext as _


from wtforms import TextField, TextAreaField, BooleanField, PasswordField, HiddenField
from wtforms.validators import DataRequired

class UploadForm(Form):
    """
    Form used to upload a new file
    """
    uploader_name = TextField(_('Uploader name'), [DataRequired()], default=_('Anonymous'))
    deletion_password = PasswordField(_('Password (used for deletion)'), default='')
    file = FileField(_('File to upload'), [FileRequired()])
    private = BooleanField(_('Private torrent?'), default=False)
    extract = BooleanField(_('Extract file'), default=False)
    trackers = TextAreaField(_('Trackers'), default='')
    webseeds = TextAreaField(_('Webseeds'), default='')
    description = TextAreaField(_('Short description'), default='')

class DeleteForm(Form):
    """
    Form use to delete a previously uploaded file
    """
    deletion_password = PasswordField(_('Password for deletion:'))
    object_id = HiddenField(validators=[DataRequired()])
