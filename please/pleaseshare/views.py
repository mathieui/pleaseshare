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
import zipfile
import logging

if settings.LOG:
    logging.basicConfig(filename=settings.LOG_FILE, level=logging.INFO)

log = logging.getLogger(__name__)

# local imports
from models import Upload
from torrent import maketorrent

options = {
        'multifile': settings.OPTION_MULTIFILE,
        'trackers': settings.OPTION_TRACKERS,
        'webseeds': settings.OPTION_WEBSEEDS,
        'ddl': settings.OPTION_DDL,
}
messages = {
        '0': '<p class="info-important">Error</p>',
        '1': '<p class="info-important">Failed to delete the file, please retry later or contact the admin.</p>',
        '2': '<p class="info-ok">Your file has been successfully deleted</p>',
    }

def err_msg(request, msg):
    di = locals()
    di.update(csrf(request))
    di['msg'] = messages.get(msg, 'Error.')
    di.update(options)
    log.info('Showing error message: %s' % di['msg'])
    return render_to_response('home.html', di)

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

        if settings.OPTION_MULTIFILE:
            extract = request.POST.get('extract', 'off')
            extract = (extract == 'on')
        else:
            extract = False

        if settings.OPTION_TRACKERS:
            trackers = request.POST.get('trackers', '').split('\n')[:50]
            remove_empty_str(trackers)
            format_trackers(trackers)
        else:
            trackers = []

        if settings.OPTION_WEBSEEDS:
            webseeds = request.POST.get('webseeds', '').split('\n')[:50]
            remove_empty_str(webseeds)
        else:
            webseeds = []

        obj = handle_uploaded_file(request.FILES[u'please'], extract, trackers, webseeds)
        if obj:
            obj.uploader = request.POST.get('user', 'Anonymous')
            obj.description = request.POST.get('description', '')
            obj.password = request.POST.get('delete', '')
            obj.save()
            log.info('Torrent %s successfully created' % obj.name)
            return HttpResponseRedirect(obj.get_absolute_url())
        log.info(u'Torrent creation failed, redirecting.')
    return HttpResponseRedirect('/0')

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
            err = 2
            log.info('File successfully deleted')
        else:
            err = 1
            log.info('File intact: wrong password')
    else:
        err = 0
    return HttpResponseRedirect('/%s' % err)

def handle_uploaded_file(f, extract=False, trackers=[], webseeds=[]):
    """
    Write a file to the disk, and in the database

    returns: the Upload object, or False
    """
    id = str(uuid4())
    folder = path.join(settings.MEDIA_ROOT, id)
    mkdir(folder)
    if extract:
        fun = select_extract_func(f.name)
        _file, ok = fun(f, folder)
        # Everything went fine
        if ok:
            size = get_dir_size(folder)
            multifile = True
        # Could not extract the file (too big?)
        elif _file:
            size = get_dir_size(folder)
            multifile = False
        # Could not save the file
        else:
            return False
    else:
        _file = save_file(f, folder)
        # Everything went fine
        if _file:
            size = get_dir_size(folder)
            multifile = False
        # Could not save the file
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

    returns: the path of the uploaded file, or False on failure
    """
    if f.size > (settings.MAX_SIZE * 1024 * 1024):
        log.info('Could not save file (file too big): %s' % f.name)
        return False
    file = path.join(folder, f.name)
    destination = open(file, 'wb+')
    for chunk in f.chunks():
        destination.write(chunk)
    destination.close()
    log.info('File saved: %s, %s MiB' % (file, round(f.size/(1024*1024.0), 2)))
    return file

def extract_tar(f, folder):
    """
    Extracts a tar file

    returns: (file, state), where file is the filepath or None, and
                state is a boolean whether or not the extraction succeeded
    """
    try:
        _file = save_file(f, folder)
        if settings.OPTION_DECOMPRESS:
            o = tarfile.open(_file)
        else:
            o = tarfile.open(_file, mode='r:')
    except:
        log.info('Error opening tarfile: %s' % f.name)
        return (_file, False)
    else:
        if not _file:
            return (False, False)
    sum = 0
    for member in o:
        sum += member.size
        if sum > (settings.MAX_SIZE * 1024 * 1024):
            return (_file, False)
    name = f.name.split('.')[0]
    rep = path.join(folder, name)
    mkdir(rep)
    try:
        proceed_tar_extraction(o, rep)
    except: # extraction failed, remove leftover files
        log.info('Extraction of %s failed, falling back to single-file upload' % f.name)
        rmtree(rep)
        return (_file, False)
    # remove old tar file
    remove(path.join(folder, f.name))
    f.name = name
    log.info('Successfully extracted tarfile %s into %s (%s MiB)' % (
        f.name, rep, round(sum / (1024*1024.0), 2)))
    return (rep, True)

def proceed_tar_extraction(tar, dir):
    """Extract the tar"""
    for member in tar:
        # test against files named by stupid people
        if not member.name.startswith('/') and not \
                '..' in member.name:
            tar.extract(member, dir)
            try:
                # python has no option to use umask while extracting, so…
                chmod(path.join(dir, member.name), 0755)
            except:
                log.info('Error chmoding %s' % member.name)
                pass

def extract_zip(f, folder):
    """
    Extracts a zip file

    returns: (file, state), where file is the filepath or None, and
                state is a boolean whether or not the extraction succeeded
    """
    try:
        _file = save_file(f, folder)
        if settings.OPTION_DECOMPRESS:
            o = zipfile.ZipFile(_file, mode='r', compression=zipfile.ZIP_DEFLATED)
        else:
            o = zipfile.ZipFile(_file, mode='r', compression=zipfile.ZIP_STORED)
    except:
        log.info('Error opening zipfile: %s' % f.name)
        return (_file, False)
    else:
        if not _file:
            return (False, False)
    sum = 0
    for member in o.infolist():
        sum += member.file_size
        if sum > (settings.MAX_SIZE * 1024 * 1024):
            return (_file, False)
    name = f.name.split('.')[0]
    rep = path.join(folder, name)
    mkdir(rep)
    try:
        proceed_zip_extraction(o, rep)
    except: # extraction failed, remove leftover files
        log.info('Extraction of %s failed, falling back to single-file upload' % f.name)
        rmtree(rep)
        return (_file, False)
    # remove old zip file
    remove(path.join(folder, f.name))
    f.name = name
    log.info('Successfully extracted zipfile %s into %s (%s MiB)' % (
        f.name, rep, round(sum / (1024*1024.0), 2)))
    return (rep, True)

def proceed_zip_extraction(zip, dir):
    """Extract the zip"""
    for member in zip.infolist():
        # test against files named by stupid people
        if not member.filename.startswith('/') and not \
                '..' in member.filename:
            zip.extract(member, dir)
            try:
                # python has no option to use umask while extracting, so…
                chmod(path.join(dir, member.filename), 0755)
            except:
                log.info('Error chmoding %s' % member.filename)
                pass

def select_extract_func(name):
    """Return the appropriate extract function based on the extension"""
    for i in ('tar.gz', 'tar.bz2', 'tar.bz', 'tar', 'tbz', 'tbz2', 'tgz'):
        if name.lower().endswith(i):
            log.info('Detecting tar file format')
            return extract_tar
    log.info('Did not detect tar, defaulting to zip file format')
    return extract_zip
