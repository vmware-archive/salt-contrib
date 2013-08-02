#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Get some grains information that is only available in Amazon AWS

Author: Erik Günther

"""
import logging
import httplib
import socket
import json

# Set up logging
LOG = logging.getLogger(__name__)


def _call_aws(url):
    """
    Call AWS via httplib. require correct path to data will
    Host: 169.254.169.254

    """
    conn = httplib.HTTPConnection("169.254.169.254", 80, timeout=1)
    conn.request('GET', url)
    response = conn.getresponse()
    if response.status == 200:
        return response.read()


def _get_ec2_hostinfo(path="", data={}):
    """
    Recursive function that walks the EC2 metadata that is available to each minion.
    :param path: URI fragment to append to /latest/meta-data/
    :param data: Dictionary containing the results from walking the AWS meta-data

    All EC2 variables are prefixed with "ec2_" so they are nicely grouped as grains and also avoids collisions with
    other grain names.
    """
    for line in _call_aws("/latest/meta-data/%s" % path).split("\n"):
        if line[-1] != "/":
            data["ec2_" + line] = _call_aws("/latest/meta-data/%s" % (path + line))
        else:
            _get_ec2_hostinfo(path + line, data=data)


def _get_ec2_region():
    """
    Recursive call in _get_ec2_hostinfo() does not retrieve a node's region
    """
    data = _call_aws("/latest/dynamic/instance-identity/document")
    return json.loads(data)['region']


def ec2_info():
    """
    Collect some extra host information
    """
    try:
        #First do a quick check if AWS magic URL work. If so we guessing that
        # we are running in AWS and will try to get more data.
        _call_aws('/')
    except (socket.timeout, socket.error, IOError):
        return {}

    try:
        grains = {}
        _get_ec2_hostinfo(data=grains)
        grains['ec2_region'] = _get_ec2_region()
        return grains
    except socket.timeout, serr:
        LOG.info("Could not read EC2 data (timeout): %s" % (serr))
        return {}
        
    except socket.error, serr:
        LOG.info("Could not read EC2 data (error): %s" % (serr))
        return {}
        
    except IOError, serr:
        LOG.info("Could not read EC2 data (IOError): %s" % (serr))
        return {}

if __name__ == "__main__":
    print ec2_info()
