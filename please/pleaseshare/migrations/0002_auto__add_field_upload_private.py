# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'Upload.private'
        db.add_column('pleaseshare_upload', 'private', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'Upload.private'
        db.delete_column('pleaseshare_upload', 'private')


    models = {
        'pleaseshare.upload': {
            'Meta': {'object_name': 'Upload'},
            'date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '400', 'blank': 'True'}),
            'magnet': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'multifile': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'password': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '32', 'blank': 'True'}),
            'private': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'size': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            'uploader': ('django.db.models.fields.CharField', [], {'default': "'Anonymous'", 'max_length': '32'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'primary_key': 'True'})
        }
    }

    complete_apps = ['pleaseshare']
