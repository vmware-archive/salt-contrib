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
    rsp = http.getresponse().read()
    return rsp


def gce_ext_ip():
    """
    Fetch the public IP address for this instance from Google's metadata
    servers.
    """
    try:
        rsp = _metadata_request(
            '/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip'
        )
        return {'pub_fqdn_ipv4': rsp}
    except gaierror:
        return {}


def gce_tags():
    """
    Fetch the instance's tags from Google's metadata servers.

    It fills in tags and roles in the dictionary to allow interoperation with
    formulas that key off of the roles grain.
    """
    try:
        rsp = _metadata_request('/computeMetadata/v1/instance/tags')
        tags = json.loads(rsp)
        return {'tags': tags, 'roles': tags}
    except gaierror:
        return {}


def gce_zone():
    """
    Fetch the instance's zone.
    """
    try:
        rsp = _metadata_request('computeMetadata/v1/instance/zone')
        zone = re.search('/([^/]+)$', rsp).groups()[0]
        return {'zone': zone}
    except gaierror:
        return {}
