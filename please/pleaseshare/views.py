#coding: utf-8
# django imports
from django.http import HttpResponseRedirect
from django.core.context_processors import csrf
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.sites.models import Site
from django.conf import settings

# system imports
from os import mkdir, path, stat, walk, remove, chmod
from shutil import rmtree
from uuid import uuid4
from urllib import quote
import tarfile

# local imports
from models import Upload
from torrent import maketorrent


def get_dir_size(start_path = '.'):
    """
    Gets the total size of a directory
    """
    total_size = 0
    for dirpath, dirnames, filenames in walk(start_path):
        for f in filenames:
            fp = path.join(dirpath, f)
            total_size += path.getsize(fp)
    return total_size

def remove_empty_str(tab):
    for i in range(tab.count('')):
        tab.remove('')

def format_trackers(tab):
    for i, j in enumerate(tab[:]):
        tab[i] = [j]

def create_torrent(data_path, comment='', webseeds=[], trackers=[]):
    t = maketorrent.TorrentMetadata()
    t.data_path = data_path
    t.comment = comment
    t.webseeds = webseeds
    if trackers:
        t.trackers = trackers
    return t

def upload_file(request):
    """
    Get the file upload form
    """
    if request.method == 'POST':
        detar = request.POST.get('detar', 'off')
        detar = (detar == 'on')
        trackers = request.POST.get('trackers', '').split('\n')[:50]
        remove_empty_str(trackers)
        format_trackers(trackers)
        webseeds = request.POST.get('webseeds', '').split('\n')[:50]
        remove_empty_str(webseeds)
        obj = handle_uploaded_file(request.FILES[u'please'], detar, trackers, webseeds)
        if obj:
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
            msg_ok = "Your file has been successfully deleted"
        else:
            msg_imp = 'Failed to delete the file, please retry later or contact one of the administrators'
    di = locals()
    di.update(csrf(request))
    return render_to_response('home.html', di)

def handle_uploaded_file(f, detar=False, trackers=[], webseeds=[]):
    """
    Write a file to the disk, and in the database
    """
    id = str(uuid4())
    folder = path.join(settings.MEDIA_ROOT, id)
    mkdir(folder)
    if detar:
        _file = extract_tar(f, folder)
        if _file:
            size = get_dir_size(folder)
            multifile = True
        else:
            return False
    else:
        _file = save_file(f, folder)
        if _file:
            size = get_dir_size(folder)
            multifile = False
        else:
            return False
    size = round(size / (1024.0**2), 2)
    u = Upload(uuid=id, name=f.name, size=size)
    webseeds = webseeds + ['http://%s%s' % (Site.objects.get_current().domain, quote(u.get_file()))]
    t = create_torrent(_file, "Created with pleaseshare", webseeds, trackers)
    u.magnet = t.save(path.join(folder, "%s.torrent" % f.name))
    u.multifile = multifile
    u.save()
    return u

def save_file(f, folder):
    """
    Saves a file into a folder
    """
    file = path.join(folder, f.name)
    destination = open(file, 'wb+')
    for chunk in f.chunks():
        destination.write(chunk)
    destination.close()
    return file

def extract_tar(f, folder):
    """
    Extracts a tar file
    """
    try:
        o = tarfile.open(save_file(f, folder))
    except:
        return False
    name = '.'.join(f.name.split('.')[:-1])
    rep = path.join(folder, name)
    mkdir(rep)
    for member in o:
        # test against files named by stupid people
        if not member.name.startswith('/') and not \
                '..' in member.name:
            o.extract(member, rep)
            try:
                # python has no option to use umask while extracting, so…
                chmod(path.join(rep, member.name), 0755)
            except:
                pass
    # remove old tar file
    remove(path.join(folder, f.name))
    f.name = name
    return rep

