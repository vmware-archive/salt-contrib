# -*- coding: utf-8 -*-
"""
Get info from gce metadata and put it into grains store
Requires Python 2.6 or higher or the standalone json module
"""

from __future__ import absolute_import

try:
    from http.client import HTTPConnection
except ImportError:
    from salt.ext.six.moves.http_client import HTTPConnection
from socket import gaierror
import json
import re


def _metadata_request(path):
    http = HTTPConnection('metadata')
    http.request('GET',
                 path,
                 ' ',
                 {'X-Google-Metadata-Request': 'True'})
    rsp = http.getresponse().read().decode('utf-8')
    return rsp

def gce_instance_metadata():
    try:
        rsp = _metadata_request('/computeMetadata/v1/instance/?recursive=true')
        metadata = json.loads(rsp)
        return {'gce_instance_metadata': metadata}
    except gaierror:
        return {}

def gce_project_metadata():
    try:
        rsp = _metadata_request('/computeMetadata/v1/project/?recursive=true')
        metadata = json.loads(rsp)
        return {'gce_project_metadata': metadata}
    except gaierror:
        return {}
