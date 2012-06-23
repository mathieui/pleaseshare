# coding: utf-8

from django.utils import unittest
from django.test.client import Client
from pleaseshare.views import format_trackers, remove_empty_str,\
        select_extract_func, extract_tar, extract_zip
from os.path import dirname, realpath, join

class TorrentCreationTest(unittest.TestCase):
    def setUp(self):
        pass

    def test_normal_request(self):
        """
        Test file upload, download, and deletion with a normal file
        """
        c = Client()

        filename = u'répondeur_linkmauve.wav'
        filepath = join(realpath(dirname(__file__)), 'data', filename)

        # Upload a file
        with open(filepath, 'r') as fp:
            response = c.post('/upload', {
                'please': fp,
                'trackers': 'udp://share.example.com:80',
                'delete': 'totopassword'
                }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.redirect_chain, [('http://testserver/0', 302)])

        # Get the file ID
        url = response.redirect_chain[0][0]
        _id = url[23:]
        if _id.endswith('/'):
            _id = _id[:-1]

        # Check if the file is accessible and the same
        with open(filepath, 'rb') as fp:
            f = fp.read()
        response = c.get(join('/uploads', _id, filename))
        self.assertEqual(f, response.content)

        # Check that a torrent has been generated
        response = c.get(join('/uploads', _id, filename + '.torrent'))
        self.assertEqual(response.status_code, 200)

        # Try to delete the file with the wrong password
        response = c.post('/delete/', {
            'delete': 'koinpassword',
            'id': _id,
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.redirect_chain, [('http://testserver/1', 302)])

        # Try to delete the file with the right password
        response = c.post('/delete/', {
            'delete': 'totopassword',
            'id': _id,
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.redirect_chain, [('http://testserver/2', 302)])


class FunctionsTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def test_remove_empty_str(self):
        """
        Check that the remove_empty_str function works properly
        """
        tab = ['', 'qsd', '', 'sdf', 'koin', '']
        remove_empty_str(tab)
        self.assertEquals(tab, ['qsd', 'sdf', 'koin'])

        tab = ['', '', '', '']
        remove_empty_str(tab)
        self.assertEquals(tab, [])

        tab = ['', 'a', 'b', '']
        remove_empty_str(tab)
        self.assertEquals(tab, ['a', 'b'])

    def test_format_trackers(self):
        """
        Check that the format_trackers function works properly
        """
        tab = ['udp://toto', 'koin://test', 'test://ex']
        new_tab = format_trackers(tab)
        needed = [['udp://toto'], ['koin://test'], ['test://ex']]
        self.assertEquals(new_tab, needed)

        tab = []
        new_tab = format_trackers(tab)
        self.assertEquals(new_tab, tab)

    def test_select_extract_func(self):
        """
        Check that the select_extract_func function workrs properly
        """
        for i in ('tar.gz', 'tar.bz2', 'tar.bz', 'tar', 'tbz', 'tbz2', 'tgz'):
            func = select_extract_func(i)
            self.assertEqual(func, extract_tar)

        for i in ('toto', 'zip', 'odt', 'banana'):
            func = select_extract_func(i)
            self.assertEqual(func, extract_zip)

