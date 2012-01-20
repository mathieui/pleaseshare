#coding: utf-8
from django.db import models
from django.conf import settings
import subprocess
from os import path

class Upload(models.Model):
    """
    uploader: the name of the uploader (optional)
    name: name of the file, or the root folder, for a multi-file torrent
    uuid: unique identifier of the torrent
    date: date of the upload
    password: a password to delete the torrent (optional)
    description: a short description of the torrent
    size: size of the file/folder
    multifile: whether the torrent contains several files or not
    magnet: magnet link of the torrent
    """
    uploader = models.CharField(max_length=32, default="Anonymous")
    name = models.CharField(max_length=128)
    uuid = models.CharField(max_length=36, primary_key=True)
    date = models.DateField(auto_now_add = True)
    password = models.CharField(max_length=32, default="", blank=True)
    description = models.CharField(max_length=400, default="", blank=True)
    size = models.CharField(max_length=8)
    multifile = models.BooleanField(default=False, blank=True)
    magnet = models.TextField(default="")

    def __unicode__(self):
        return '%s - %s/%s - %s' % (self.uploader, self.uuid, self.name, self.date)
    def get_absolute_url(self):
        return '/view/%s/' % self.uuid

    def get_torrent_file(self):
        return '/upload/%s/%s.torrent' % (self.uuid, self.name)

    def get_file(self):
        return '/upload/%s/%s' % (self.uuid, self.name if self.multifile else "")

    def get_files(self):
        dir = path.join(settings.MEDIA_ROOT, self.uuid, self.name)
        try:
            proc = subprocess.Popen(['tree', '-ah', dir], stdout=subprocess.PIPE)
            res = proc.communicate()[0]
        except OSError:
            res = ''
            print('Call to `tree` failed.')
        tb = res.split('\n')
        if self.multifile:
            suffix = '/'
        else:
            suffix = ''
        tb[0] = str(self.name + suffix)
        return '\n'.join(tb)
