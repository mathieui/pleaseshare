"""
Individual non-expensive functions
"""
from collections import namedtuple
PostParams = namedtuple('PostParams',
                        'extract trackers webseeds private '
                        'uploader password description')

import flask


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

def can_delete(uuid: str) -> bool:
    """
    Check if the user has the uuid in his session.
    If he has, return true to enable passwordless deletion.
    """
    if not 'uploads' in flask.session:
        return False
    for stored_upload in flask.session['uploads']:
        if stored_upload[1] == uuid:
            return True
    return False

def remove_uuid_from_session(uuid: str):
    """
    Remove a stored file from the session, after it has been deleted in
    the database and on disk.
    """
    for idx, stored_upload in enumerate(flask.session['uploads'][:]):
        if stored_upload[1] == uuid:
            del flask.session['uploads'][idx]
            break

