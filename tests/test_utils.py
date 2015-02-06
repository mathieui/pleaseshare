from os.path import abspath, dirname, realpath
TEST_DIR = realpath(abspath(dirname(__file__)))

from sys import path
path.insert(0, dirname(TEST_DIR))


from pleaseshare.utils import parse_form, PostParams

def config(multi, trackers, mandat, webseeds, private):
    return {
        'ALLOW_MULTIFILE': multi,
        'ALLOW_TRACKERS': trackers,
        'MANDATORY_TRACKERS': mandat,
        'ALLOW_WEBSEEDS': webseeds,
        'ALLOW_PRIVATE': private
    }

class FormElement(object):
    def __init__(self, data):
        self.data = data
class FormStub(object):
    def __init__(self, kwargs):
        for i in kwargs:
            setattr(self, i, FormElement(kwargs[i]))

def test_parse_form():
    form = FormStub({'trackers': '', 'extract': False, 'webseeds': '',
                     'private': False, 'uploader_name': 'anon',
                     'deletion_password': '', 'description': ''})
    computed = parse_form(form, config(1, 1, [], 1, 1))
    expected = PostParams(False, [], [], False, 'anon', '', '')
    assert computed == expected

    form.private = FormElement(True)
    computed = parse_form(form, config(1, 1, [], 1, 1))
    expected = PostParams(False, [], [], False, 'anon', '', '')
    assert computed == expected

    form.trackers = FormElement("toto")
    computed = parse_form(form, config(1, 1, [], 1, 1))
    expected = PostParams(False, [['toto']], [], True, 'anon', '', '')
    assert computed == expected

    computed = parse_form(form, config(1, 1, [], 1, 0))
    expected = PostParams(False, [['toto']], [], False, 'anon', '', '')
    assert computed == expected

    computed = parse_form(form, config(1, 0, [], 1, 0))
    expected = PostParams(False, [], [], False, 'anon', '', '')
    assert computed == expected
    form.trackers = FormElement("")

    form.extract = FormElement(True)
    computed = parse_form(form, config(1, 1, [], 1, 1))
    expected = PostParams(True, [], [], False, 'anon', '', '')
    assert computed == expected

    computed = parse_form(form, config(0, 1, [], 1, 1))
    expected = PostParams(False, [], [], False, 'anon', '', '')
    assert computed == expected

    form.trackers = FormElement("toto")
    computed = parse_form(form, config(0, 0, ['test'], 0, 0))
    expected = PostParams(False, [['test']], [], False, 'anon', '', '')
    assert computed == expected

