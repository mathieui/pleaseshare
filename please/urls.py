from django.conf.urls import patterns, include, url
from django.conf import settings
from pleaseshare.views import direct_to_template
from django.views.generic import DetailView
from django.views.static import serve
from pleaseshare.models import Upload

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', direct_to_template('home.html'), name='home'),
    url(r'^(?P<msg>[0-9]+)$', 'pleaseshare.views.err_msg', name='err'),
    url(r'^upload/?$', 'pleaseshare.views.upload_file', name='upload'),
    url(r'^delete/?$', 'pleaseshare.views.delete_file', name='delete'),
    url(r'^view/(?P<pk>[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})/?$', DetailView.as_view(model=Upload, template_name="upload_detail.html"), name='single'),

    # static files
    url(r'^contact/?$', direct_to_template('contact.html'), name='Contact'),
    url(r'^about/?$', direct_to_template('about.html'), name='About'),
    url(r'^tos/?$', direct_to_template('tos.html'), name='ToS'),
    url(r'^help/?$', direct_to_template('help.html'), name='Help'),

    url(r'^admin/', include(admin.site.urls)),
)

# In order to follow the good practices, comment this and use a real file server for the static files
# (and it is mandatory to do that because the built-in server does feature HTTP ranges.)
urlpatterns += patterns('',
        (r'^%s(.*)$' % settings.MEDIA_URL[1:], serve, {'document_root': '%s' % settings.MEDIA_URL[1:-1]}),
        (r'^static/(.*)$', serve, {'document_root': 'static'}),
)
