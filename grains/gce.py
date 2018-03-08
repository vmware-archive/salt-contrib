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
import json
import re


def gce_ext_ip():
    """
    Fetch the public IP address for this instance from Google's metadata
    servers.
    """
    http = HTTPConnection('metadata')
    http.request('GET',
                 '/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip',
                 ' ',
                 {'X-Google-Metadata-Request': 'True'})
    rsp = http.getresponse()
    return {'pub_fqdn_ipv4': rsp.read()}


def gce_tags():
    """
    Fetch the instance's tags from Google's metadata servers.

    It fills in tags and roles in the dictionary to allow interoperation with
    formulas that key off of the roles grain.
    """
    http = HTTPConnection('metadata')
    http.request('GET',
                 '/computeMetadata/v1/instance/tags',
                 ' ',
                 {'X-Google-Metadata-Request': 'True'})
    rsp = http.getresponse()
    tags = json.loads(rsp.read())
    return {'tags': tags, 'roles': tags}


def gce_zone():
    """
    Fetch the instance's zone.
    """
    http = HTTPConnection('metadata')
    http.request('GET',
                 'computeMetadata/v1/instance/zone',
                 ' ',
                 {'X-Google-Metadata-Request': 'True'})
    rsp = http.getresponse()
    zone = re.search('/([^/]+)$', rsp.read()).groups()[0]
    return {'zone': zone}
