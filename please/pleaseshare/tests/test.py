# coding: utf-8

from django.utils import unittest
from django.test.client import Client
from pleaseshare.views import format_trackers, remove_empty_str,\
        select_extract_func, extract_tar, extract_zip, parse_args
from os.path import dirname, realpath, join
from django.conf import settings

# Change the settings to be sure they won’t affect the tests
settings.LOG_FILE = ''
settings.MAX_SIZE = 42
settings.OPTION_DECOMPRESS = True
settings.OPTION_DDL = False
settings.OPTION_TRACKERS = True
settings.OPTION_WEBSEEDS = True
settings.OPTION_MULTIFILE = True
settings.OPTION_PRIVATE = False
settings.DEFAULT_TRACKERS = ['udp://tracker.openbittorent.com:80']
settings.MANDATORY_TRACKERS = []
settings.TORRENT_POOL = ''

class request(object):
    def __init__(self, d):
        self.POST = d

class TorrentCreationTest(unittest.TestCase):
    def setUp(self):
        pass

    def test_normal_request(self):
        """
        Test file upload, download, and deletion with a normal file
        """
        c = Client()

        filename = 'répondeur_linkmauve.wav'
        filepath = join(realpath(dirname(__file__)), 'data', filename)
        print(filepath)

        import sys
        sys.stderr.write(repr(filename) + '\n')

        # Upload a file
        with open(filepath, 'rb') as fp:
            response = c.post('/upload', {
                'please': fp,
                'trackers': 'udp://share.example.com:80',
                'delete': 'totopassword'
                }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.redirect_chain, [('http://testserver/0', 302)],
                msg="The file was not uploaded successfully.")

        # Get the file ID
        url = response.redirect_chain[0][0]
        _id = url[23:]
        if _id.endswith('/'):
            _id = _id[:-1]

        # Check if the file is accessible and the same
        with open(filepath, 'rb') as fp:
            f = fp.read()
        response = c.get(join('/uploads', _id, filename))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(f, response.content,
                msg="The uploaded file differs from the original.")

        # Check that a torrent has been generated
        response = c.get(join('/uploads', _id, filename + '.torrent'))
        self.assertEqual(response.status_code, 200,
                msg="Cannot access the torrent file.")

        # Try to delete the file with the wrong password
        response = c.post('/delete/', {
            'delete': 'koinpassword',
            'id': _id,
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.redirect_chain, [('http://testserver/1', 302)],
                msg="The wrong error message was shown.")

        # Try to delete the file with the right password
        response = c.post('/delete/', {
            'delete': 'totopassword',
            'id': _id,
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.redirect_chain, [('http://testserver/2', 302)],
                "The file was not deleted, or the redirection was wrong.")


class FunctionsTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def test_remove_empty_str(self):
        """
        Check that the remove_empty_str function works properly
        """
        tab = ['', 'qsd', '', 'sdf', 'koin', '']
        remove_empty_str(tab)
        self.assertEqual(tab, ['qsd', 'sdf', 'koin'])

        tab = ['', '', '', '']
        remove_empty_str(tab)
        self.assertEqual(tab, [])

        tab = ['', 'a', 'b', '']
        remove_empty_str(tab)
        self.assertEqual(tab, ['a', 'b'])

    def test_format_trackers(self):
        """
        Check that the format_trackers function works properly
        """
        tab = ['udp://toto', 'koin://test', 'test://ex']
        new_tab = format_trackers(tab)
        needed = [['udp://toto'], ['koin://test'], ['test://ex']]
        self.assertEqual(new_tab, needed)

        tab = []
        new_tab = format_trackers(tab)
        self.assertEqual(new_tab, tab)

    def test_select_extract_func(self):
        """
        Check that the select_extract_func function works properly
        """
        name = "example_file."
        for i in ('tar.gz', 'tar.bz2', 'tar.bz', 'tar', 'tbz', 'tbz2', 'tgz'):
            func = select_extract_func(name + i)
            self.assertEqual(func, extract_tar)

        for i in ('toto', 'zip', 'odt', 'banana'):
            func = select_extract_func(name + i)
            self.assertEqual(func, extract_zip)

    def test_parse_args(self):
        """
        Test the parse_args function with various input values
        """
        values1 = {
                'extract': 'on',
                'trackers': 'udp://toto\ntcp://koin',
                'webseeds': '',
                'private': 'off',
                'delete': '',
                'description': 'coucou',
        }
        values2 = {
                'extract': 'on',
                'trackers': 'udp://toto',
                'webseeds': 'http://example.com/file.tar',
                'private': 'on',
                'delete': 'test',
                'description': 'coucou coucou',
        }

        # First test
        extract, trackers, webseeds, private, uploader, password, description =\
                parse_args(request(values1))
        self.assertEqual(extract, True)
        self.assertEqual(trackers, [['udp://toto'], ['tcp://koin']])
        self.assertEqual(webseeds, [])
        self.assertEqual(private, False)
        self.assertEqual(uploader, 'Anonymous')
        self.assertEqual(password, '')
        self.assertEqual(description, 'coucou')

        # Second test
        extract, trackers, webseeds, private, uploader, password, description =\
                parse_args(request(values2))
        self.assertEqual(extract, True)
        self.assertEqual(trackers, [['udp://toto']])
        self.assertEqual(webseeds, ['http://example.com/file.tar'])
        self.assertEqual(private, False,
            'Private torrents are disable in the settings, it should not work')
        self.assertEqual(uploader, 'Anonymous')
        self.assertEqual(password, 'test')
        self.assertEqual(description, 'coucou coucou')

        # disable additional webseeds, and enable private torrents

        settings.OPTION_WEBSEEDS = False
        settings.OPTION_PRIVATE = True

        # Third test
        extract, trackers, webseeds, private, uploader, password, description =\
                parse_args(request(values2))
        self.assertEqual(extract, True)
        self.assertEqual(trackers, [['udp://toto']])
        self.assertEqual(webseeds, [])
        self.assertEqual(private, True)
        self.assertEqual(uploader, 'Anonymous')
        self.assertEqual(password, 'test')
        self.assertEqual(description, 'coucou coucou')


