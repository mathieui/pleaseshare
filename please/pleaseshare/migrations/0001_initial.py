# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Upload'
        db.create_table('pleaseshare_upload', (
            ('uploader', self.gf('django.db.models.fields.CharField')(default='Anonymous', max_length=32)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, primary_key=True)),
            ('date', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
            ('password', self.gf('django.db.models.fields.CharField')(default='', max_length=32, blank=True)),
            ('description', self.gf('django.db.models.fields.CharField')(default='', max_length=400, blank=True)),
            ('size', self.gf('django.db.models.fields.CharField')(max_length=8)),
            ('multifile', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('magnet', self.gf('django.db.models.fields.TextField')(default='')),
        ))
        db.send_create_signal('pleaseshare', ['Upload'])


    def backwards(self, orm):
        
        # Deleting model 'Upload'
        db.delete_table('pleaseshare_upload')


    models = {
        'pleaseshare.upload': {
            'Meta': {'object_name': 'Upload'},
            'date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '400', 'blank': 'True'}),
            'magnet': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'multifile': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'password': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '32', 'blank': 'True'}),
            'size': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            'uploader': ('django.db.models.fields.CharField', [], {'default': "'Anonymous'", 'max_length': '32'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'primary_key': 'True'})
        }
    }

    complete_apps = ['pleaseshare']
