"""
Tasks module:
archive extraction, introspection, POST parameters parsing,
torrent creation.
"""
from os import mkdir, remove, chmod
from os.path import abspath, basename, dirname, isdir, join as joinpath, realpath
from shutil import rmtree
import tarfile
import zipfile
import logging
from functools import singledispatch

log = logging.getLogger(__name__)

from collections import namedtuple
PostParams = namedtuple('PostParams',
                        'extract trackers webseeds private '
                        'uploader password description')

from pleaseshare.torrent import maketorrent

class BadArchive(Exception):
    """
    Raised when an archive tries to make a symlink or a relative
    path outside of its directory.
    """

class Archive(object):
    """
    Wrapper around an archive File type (currently tarfile or zipfile)
    """

    def __init__(self, location: str, allow_compressed=False):

        self._archive_name = basename(location)
        self._extracted_name = self._archive_name.split('.')[0]
        self._dirname = dirname(location)

        if not allow_compressed:
            self._file = tarfile.TarFile.open(location, mode='r:')
        else:
            for ext in ('.tar', '.tar.gz', '.tar.bz2', '.tar.lzma', '.tar.xz'):
                if self._archive_name.endswith(ext):
                    self._file = tarfile.TarFile.open(location, mode='r')
                    break
            else:
                self._file = zipfile.ZipFile(location, mode='r')

    def extract(self) -> bool:
        """
        Extract the archive
        returns True if it succeeded, False otherwise
        """
        return extract(self._file, joinpath(self._dirname, self._archive_name), self.extracted_location())

    def extracted_name(self) -> str:
        """Name of the extracted directory"""
        return self._extracted_name

    def extracted_location(self) -> str:
        """Path of the extracted directory"""
        return joinpath(self._dirname, self._extracted_name)

    def archive_location(self) -> str:
        """Path to the archive"""
        return joinpath(self._dirname, self._archive_name)

    def size(self) -> int:
        """Total size of the uncompressed archive"""
        return size(self._file)

@singledispatch
def extract(archivefile, name, rep):
    """To override"""
    raise NotImplementedError()

@extract.register(tarfile.TarFile)
def _extract_tar(archivefile: tarfile.TarFile, name: str, rep: str) -> bool:
    """Extract a tar archive """
    mkdir(rep, mode=0o711)
    if not check_archive(archivefile):
        raise BadArchive("malicious archive")
    try:
        for member in archivefile:
            archivefile.extract(member, rep, set_attrs=False)
            member_location = joinpath(rep, member.name)
            # python has no option to use umask while extracting, so…
            if isdir(member_location):
                chmod(member_location, 0o711)
            else:
                chmod(member_location, 0o644)
    except: # extraction failed, remove leftover files
        log.info('Extraction of %s failed, falling back to single-file upload', name, exc_info=True)
        rmtree(rep)
        return False
    else: # remove old tar file
        remove(name)
        log.info('Successfully extracted tarfile %s into %s', name, rep)
        return True

@extract.register(zipfile.ZipFile)
def _extract_zip(archivefile: zipfile.ZipFile, name: str, rep: str) -> bool:
    """Extracts a zip file"""
    mkdir(rep, mode=0o711)
    try:
        for member in archivefile.infolist():
            # zipfile member names are sanitized
            archivefile.extract(member, rep)
            member_location = joinpath(rep, member.filename)
            # python has no option to use umask while extracting, so…
            if isdir(member_location):
                chmod(member_location, 0o711)
            else:
                chmod(member_location, 0o644)
    except: # extraction failed, remove leftover files
        import traceback
        traceback.print_exc()
        log.info('Extraction of %s failed, falling back to single-file upload',
                 name, exc_info=True)
        rmtree(rep)
        return False
    else:
        remove(name)
        log.info('Successfully extracted zipfile %s into %s', name, rep)
        return True


@singledispatch
def size(archivefile):
    """To override"""
    raise NotImplementedError()

@size.register(zipfile.ZipFile)
def _size_zip(archivefile: zipfile.ZipFile) -> int:
    """Get the size of the uncompressed zip"""
    size_sum = 0
    for member in archivefile.infolist():
        size_sum += member.file_size
    return size_sum

@size.register(tarfile.TarFile)
def _size_tar(archivefile: tarfile.TarFile) -> int:
    """Get the size of the uncompressed tar"""
    size_sum = 0
    for member in archivefile:
        size_sum += member.size
    return size_sum

def resolved(path_: str) -> str:
    """Returns the absolute path"""
    return realpath(abspath(path_))

def badpath(path: str, base: str) -> bool:
    """Returns True if a path is outside of the base directory"""
    return not resolved(joinpath(base, path)).startswith(base)

def badlink(info: tarfile.TarInfo, base: str) -> bool:
    """Resolve sym/hardlinks and perform a badpath check"""
    tip = resolved(joinpath(base, dirname(info.name)))
    return badpath(info.linkname, base=tip)

def check_archive(tar_archive: tarfile.TarFile) -> bool:
    """Check a tar archive to make sure it is not malicious"""
    base = dirname(tar_archive)

    for file_info in tar_archive:
        if badpath(file_info.name, base):
            log.error('illegal path for file %s', file_info.name)
            return False
        elif file_info.issym() and badlink(file_info, base):
            log.error('File %s is a hard link to %s', file_info.name,
                      file_info.linkname)
            return False
        elif file_info.islnk() and badlink(file_info, base):
            log.error('File %s is a symlink to %s', file_info.name,
                      file_info.linkname)
            return False
    return True

def create_torrent(data_path, comment='', webseeds=None, trackers=None, private=False):
    """Create a new torrent object"""
    torrent = maketorrent.TorrentMetadata()
    torrent.piece_size = 256
    torrent.data_path = data_path
    torrent.comment = comment
    torrent.webseeds = webseeds
    if trackers:
        torrent.trackers = trackers
        if private:
            torrent.private = private
    return torrent

def remove_empty_str(list_: list) -> list:
    """remove empty strings from a list"""
    return [x for x in list_ if x.strip()]

def format_trackers(tab: list) -> list:
    """create a list of lists of trackers, for use with the torrent API"""
    trackers = []
    for i in tab:
        trackers.append([i])
    return trackers

def parse_form(form, config) -> PostParams:
    """
    Create an object summarizing the options for the torrent
    creation.
    """
    if config['ALLOW_MULTIFILE']:
        extract_ = form.extract.data
    else:
        extract_ = False

    if config['ALLOW_TRACKERS']:
        trackers = form.trackers.data.split('\n')[:50]
        trackers = remove_empty_str(trackers)
        trackers.extend(config['MANDATORY_TRACKERS'])
        trackers = format_trackers(trackers)
    else:
        if not config['MANDATORY_TRACKERS']:
            trackers = []
        else:
            trackers = format_trackers(config['MANDATORY_TRACKERS'])

    if config['ALLOW_WEBSEEDS']:
        webseeds = form.webseeds.data.split('\n')[:50]
        webseeds = remove_empty_str(webseeds)
    else:
        webseeds = []

    if config['ALLOW_PRIVATE']:
        private = form.private.data
        if private and trackers:
            private = True
        else:
            private = False
    else:
        private = False

    uploader = form.uploader_name.data
    password = form.deletion_password.data
    description = form.description.data

    return PostParams(extract_, trackers, webseeds, private,
                      uploader, password, description)

