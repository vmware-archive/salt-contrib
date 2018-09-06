# -*- coding: utf-8 -*-
"""
Get some grains information that is only available in Amazon AWS
Author: Erik Günther, J C Lawrence <claw@kanga.nu>, Mark McGuire
"""
from __future__ import absolute_import

import logging
import socket
import json
try:
    from http.client import HTTPConnection, BadStatusLine
except ImportError:
    from salt.ext.six.moves.http_client import HTTPConnection, BadStatusLine


# Set up logging
LOG = logging.getLogger(__name__)


def _call_aws(url):
    """
    Call AWS via httplib. Require correct path.
    Host: 169.254.169.254
    """
    conn = HTTPConnection("169.254.169.254", 80, timeout=1)
    conn.request('GET', url)
    return conn.getresponse()


def _get_ec2_hostinfo(path=""):
    """
    Recursive function that walks the EC2 metadata available to each minion.
    :param path: URI fragment to append to /latest/meta-data/
    Returns a nested dictionary containing all the EC2 metadata. All keys
    are converted from dash case to snake case.
    """
    resp = _call_aws("/latest/meta-data/{0}".format(path))
    resp_data = resp.read().decode('utf-8').strip()
    d = {}
    for line in resp_data.split("\n"):
        if path == "public-keys/":
            line = line.split("=")[0] + "/"
        if path == "instance-id/":
            return {'instance-id': line}
        if len(line) == 0:
            continue
        if line[-1] != "/":
            call_response = _call_aws("/latest/meta-data/{0}".format(path + line))
            call_response_data = call_response.read().decode('utf-8')
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
                    if "\n" in call_response_data:
                        d[line] = []
                        for dline in call_response_data.split("\n"):
                            d[line].append(dline)
                    else:
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
        try:
            data = json.loads(response_data.decode('utf-8'))
        except ValueError as e:
            data = {}
        data = _snake_caseify_dict(data)
        data.update({'instance_identity': {'document': response_data}})
        return data
    else:
        raise BadStatusLine("Could not read EC2 metadata")


def _get_ec2_user_data():
    """
    Recursive call in _get_ec2_hostinfo() does not retrieve user-data.
    """
    response = _call_aws("/latest/user-data")
    # _call_aws returns None for all non '200' reponses,
    # catching that here would rule out AWS resource
    if response.status == 200:
        response_data = response.read().decode('utf-8')
        try:
            return json.loads(response_data)
        except ValueError:
            return response_data
    elif response.status == 404:
        return ''
    else:
        raise BadStatusLine("Could not read EC2 user-data")


def _get_instance_identity():
    """
    Fill in the details from the instance identity info.
    """
    result = {}
    response = _call_aws('/latest/dynamic/instance-identity/')
    data = response.read().decode('utf-8')
    for i in data.split('\n'):
        if not i or i == 'document':  # document saved in _get_ec2_additional
            continue

        response = _call_aws('/latest/dynamic/instance-identity/{0}'.format(i))
        result[i] = response.read()

    return result


def ec2_info():
    """
    Collect all ec2 grains into the 'ec2' key.
    """
    try:
        grains = _get_ec2_additional()
        grains.update({'user-data': _get_ec2_user_data()})
        grains.update(_get_ec2_hostinfo())
        grains['instance_identity'].update(_get_instance_identity())
        return {'ec2': grains}

    except BadStatusLine as error:
        LOG.debug(error)
        return {}

    except socket.timeout as serr:
        LOG.info("Could not read EC2 data (timeout): {0}".format(serr))
        return {}

    except socket.error as serr:
        LOG.info("Could not read EC2 data (error): {0}".format(serr))
        return {}

    except IOError as serr:
        LOG.info("Could not read EC2 data (IOError): {0}".format(serr))
        return {}


def ec2_instance_id():
    """
    Set the top-level grain 'instance-id' per the grain expected
    by pillar-ec2.
    """
    try:
        instance_id = list(_get_ec2_hostinfo("instance-id/").values())[0]
        return {'instance-id': instance_id}

    except BadStatusLine as error:
        LOG.debug(error)
        return {}

    except socket.timeout as serr:
        LOG.info("Could not read EC2 data (timeout): {0}".format(serr))
        return {}

    except socket.error as serr:
        LOG.info("Could not read EC2 data (error): {0}".format(serr))
        return {}

    except IOError as serr:
        LOG.info("Could not read EC2 data (IOError): {0}".format(serr))
        return {}
