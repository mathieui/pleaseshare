from os.path import abspath, dirname, join as joinpath, realpath
TEST_DIR = realpath(abspath(dirname(__file__)))

from sys import path
path.insert(0, dirname(TEST_DIR))

import pytest
import zipfile
import tarfile

from pleaseshare.tasks import Archive, check_archive


def test_big_archive():
    name = '15M-archive.tar.xz'
    data_path = joinpath(TEST_DIR, 'data', name)
    base = dirname(data_path)
    # test that allow_compressed= doesn’t work with uncompressed data
    with pytest.raises(tarfile.ReadError):
        Archive(data_path, allow_compressed=False)

    archive = Archive(data_path, allow_compressed=True)

    # test that archive introspection to get file size works
    assert archive.size() == 15000000

    # test that check_archive does not create false positives
    assert check_archive(archive._file, base) == True


def test_not_archive():
    """
    Verify that the Archive constructor raises the correct exceptions
    if fed a non-archive file.
    """
    name = 'répondeur_linkmauve.wav'
    data_path = joinpath(TEST_DIR, 'data', name)

    with pytest.raises(zipfile.BadZipFile):
        Archive(data_path, allow_compressed=True)

    with pytest.raises(tarfile.ReadError):
        Archive(data_path, allow_compressed=False)

def test_malicious_archive():
    """
    Check that the check_archive function reports bad archive
    """
    name = 'malicious-archive.tar'
    data_path = joinpath(TEST_DIR, 'data', name)
    base = dirname(data_path)

    archive = Archive(data_path)
    assert check_archive(archive._file, base) == False

