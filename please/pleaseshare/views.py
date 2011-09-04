# django imports
from django.http import HttpResponseRedirect
from django.core.context_processors import csrf
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.sites.models import Site
from django.conf import settings
from urllib import quote

# system imports
from os import mkdir, path, stat
from shutil import rmtree
from uuid import uuid4

# local imports
from models import Upload
from torrent import maketorrent


def upload_file(request):
    """
    Get the file upload form
    """
    if request.method == 'POST':
        obj = handle_uploaded_file(request.FILES[u'please'])
        obj.uploader = request.POST.get('user', 'Anonymous')
        obj.description = request.POST.get('description', '')
        obj.password = request.POST.get('delete', '')
        obj.save()
        return HttpResponseRedirect(obj.get_absolute_url())
    return HttpResponseRedirect('/error/')

def delete_file(request):
    """
    Delete a file, and the associated database entries
    """
    if request.method == 'POST':
        id = request.POST.get('id', None)
        up = get_object_or_404(Upload, pk=id)
        password = request.POST.get('delete', None)
        if password and password == up.password:
            rmtree(path.join(settings.MEDIA_ROOT, id))
            up.delete()
            msg_ok = "Your file has successfully been deleted"
        else:
            msg_imp = 'Failed to delete the file, please retry later or contact one of the administrators'
    di = locals()
    di.update(csrf(request))
    return render_to_response('home.html', di)

def handle_uploaded_file(f):
    """
    Write a file to the disk, and in the database
    """
    id = str(uuid4())
    folder = path.join(settings.MEDIA_ROOT, id)
    file = path.join(folder, f.name)
    mkdir(folder)
    destination = open(file, 'wb+')
    for chunk in f.chunks():
        destination.write(chunk)
    destination.close()
    size = round(stat(file).st_size / (1024**2), 2)
    u = Upload(uuid=id, name=f.name, size=size)
    t = maketorrent.TorrentMetadata()
    t.data_path = file
    t.comment = "Created with pleaseshare" # self-advertisement
    t.webseeds = ['http://%s%s%s' % (Site.objects.get_current().domain, quote(u.get_file()))]
    t.save(path.join(folder, "%s.torrent" % f.name))
    u.save()
    return u
