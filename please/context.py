#coding: utf-8
from django.conf import settings

def processor(request):
    options = {
            'multifile': settings.OPTION_MULTIFILE,
            'trackers': settings.OPTION_TRACKERS,
            'webseeds': settings.OPTION_WEBSEEDS,
            'ddl': settings.OPTION_DDL,
    }
    return options