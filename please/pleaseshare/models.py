#coding: utf-8
from django.db import models

class Upload(models.Model):
    uploader = models.CharField(max_length=32, default="Anonymous")
    name = models.CharField(max_length=128)
    uuid = models.CharField(max_length=36, primary_key=True)
    date = models.DateField(auto_now_add = True)
    password = models.CharField(max_length=32, default="", blank=True)
    description = models.CharField(max_length=400, default="", blank=True)
    size = models.CharField(max_length=8)
    magnet = models.TextField(default="")

    def __unicode__(self):
        return '%s - %s/%s - %s' % (self.uploader, self.uuid, self.name, self.date)
    def get_absolute_url(self):
        return '/view/%s/' % self.uuid

    def get_torrent_file(self):
        return '/upload/%s/%s.torrent' % (self.uuid, self.name)

    def get_file(self):
        return '/upload/%s/%s' % (self.uuid, self.name)
