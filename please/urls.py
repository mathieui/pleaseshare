from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import direct_to_template
from django.views.generic import list_detail
from django.views.static import serve
from pleaseshare.models import Upload

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', direct_to_template, {'template': 'home.html'}, name='home'),
    url(r'^upload/$', 'pleaseshare.views.upload_file', name='upload'),
    url(r'^delete/$', 'pleaseshare.views.delete_file', name='delete'),
    url(r'^view/(?P<object_id>[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})/$', list_detail.object_detail, {'queryset': Upload.objects.all(), 'template_name': 'single.html'},  name='single'),

    # static files
    url(r'^contact$', direct_to_template, {'template': 'contact.html'}, name='Contact'),
    url(r'^about$', direct_to_template, {'template': 'about.html'}, name='About'),
    url(r'^tos$', direct_to_template, {'template': 'tos.html'}, name='ToS'),
    url(r'^help$', direct_to_template, {'template': 'help.html'}, name='Help'),

    url(r'^admin/', include(admin.site.urls)),
)

# In order to follow the good practices, comment this and use a real file server for the static files
urlpatterns += patterns('',
        (r'^upload/(.*)$', serve, {'document_root': 'uploads'}),
        (r'^static/(.*)$', serve, {'document_root': 'static'}),
)
