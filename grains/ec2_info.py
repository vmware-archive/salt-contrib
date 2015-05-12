#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Get some grains information that is only available in Amazon AWS

Author: Erik Günther, J C Lawrence <claw@kanga.nu>, Mark McGuire

"""
import logging
import httplib
import socket
import json

# Set up logging
LOG = logging.getLogger(__name__)


def _call_aws(url):
    """
    Call AWS via httplib. Require correct path.
    Host: 169.254.169.254

    """
    conn = httplib.HTTPConnection("169.254.169.254", 80, timeout=1)
    conn.request('GET', url)
    return conn.getresponse()


def _get_ec2_hostinfo(path=""):
    """
    Recursive function that walks the EC2 metadata available to each minion.
    :param path: URI fragment to append to /latest/meta-data/

    Returns a nested dictionary containing all the EC2 metadata. All keys
    are converted from dash case to snake case.
    """
    resp = _call_aws("/latest/meta-data/%s" % path)
    resp_data = resp.read().strip()
    d = {}
    for line in resp_data.split("\n"):
        if line[-1] != "/":
            call_response = _call_aws("/latest/meta-data/%s" % (path + line))
            call_response_data = call_response.read()
            # avoid setting empty grain
            if call_response_data == '':
                d[line] = None
            elif call_response_data is not None:
                line = _dash_to_snake_case(line)
                try:
                    data = json.loads(call_response_data)
                    if isinstance(data, dict):
                        data = _snake_caseify_dict(data)
                    d[line] = data
                except ValueError:
                    d[line] = call_response_data
            else:
                return line
        else:
            d[_dash_to_snake_case(line[:-1])] = _get_ec2_hostinfo(path + line)
    return d


def _camel_to_snake_case(s):
    return s[0].lower() + "".join((("_" + x.lower()) if x.isupper() else x) for x in s[1:])


def _dash_to_snake_case(s):
    return s.replace("-", "_")


def _snake_caseify_dict(d):
    nd = {}
    for k, v in d.items():
        nd[_camel_to_snake_case(k)] = v
    return nd


def _get_ec2_additional():
    """
    Recursive call in _get_ec2_hostinfo() does not retrieve some of
    the hosts information like region, availability zone or
    architecture.

    """
    response = _call_aws("/latest/dynamic/instance-identity/document")
    # _call_aws returns None for all non '200' reponses,
    # catching that here would rule out AWS resource
    if response.status == 200:
        response_data = response.read()
        data = json.loads(response_data)
        return _snake_caseify_dict(data)
    else:
       raise httplib.BadStatusLine("Could not read EC2 metadata")


def _get_ec2_user_data():
    """
    Recursive call in _get_ec2_hostinfo() does not retrieve user-data.

    """
    response = _call_aws("/latest/user-data")
    # _call_aws returns None for all non '200' reponses,
    # catching that here would rule out AWS resource
    if response.status == 200:
        response_data = response.read()
        try:
            return json.loads(response_data)
        except ValueError as e:
            return response_data
    elif response.status == 404:
        return ''
    else:
       raise httplib.BadStatusLine("Could not read EC2 user-data")


def ec2_info():
    """
    Collect all ec2 grains into the 'ec2' key.
    """
    try:
        grains = _get_ec2_additional()
        grains.update({'user-data': _get_ec2_user_data()})
        grains.update(_get_ec2_hostinfo())
        return {'ec2' : grains}

    except httplib.BadStatusLine, error:
        LOG.debug(error)
        return {}

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
