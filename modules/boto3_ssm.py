# -*- coding: utf-8 -*-
"""
Execution module for Amazon Web Services Systems Manager using boto3
====================================================================

:configuration: This module accepts explicit EC2 credentials but can also
    utilize IAM roles assigned to the instance through Instance Profiles.
    Dynamic credentials are then automatically obtained from AWS API and no
    further configuration is necessary. More Information available here__.

.. __: http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/iam-roles-for-amazon-ec2.html

If IAM roles are not used you need to specify them either in a pillar or
in the minion's config file:

.. code-block:: yaml

    ssm.keyid: GKTADJGHEIQSXMKKRBJ08H
    ssm.key: askdjghsdfjkghWupUjasdflkdfklgjsdfjajkghs

A region may also be specified in the configuration:

.. code-block:: yaml

    ssm.region: us-east-1

If a region is not specified, the default is us-east-1.

It's also possible to specify key, keyid, and region via a profile, either
as a passed in dict, or as a string to pull from pillars or minion config:

.. code-block:: yaml

    myprofile:
      keyid: GKTADJGHEIQSXMKKRBJ08H
      key: askdjghsdfjkghWupUjasdflkdfklgjsdfjajkghs
      region: us-east-1

:depends: boto3
"""


from __future__ import absolute_import, print_function, unicode_literals
import logging
import salt.utils.compat
import salt.utils.versions


log = logging.getLogger(__name__)

# Import third party libs
try:
    import botocore
    import boto3
    logging.getLogger('boto3').setLevel(logging.CRITICAL)
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


def __virtual__():
    '''
    Only load if boto libraries exist and if boto libraries are greater than
    a given version.
    '''
    return salt.utils.versions.check_boto_reqs()


def __init__(opts):
    salt.utils.compat.pack_dunder(__name__)
    if HAS_BOTO3:
        __utils__['boto3.assign_funcs'](__name__, 'ssm',
                  get_conn_funcname='_get_conn',
                  cache_id_funcname='_cache_id',
                  exactly_one_funcname=None)


def get_parameter(name, with_decryption=True, region=None, key=None, keyid=None, profile=None):
    """
    Get a parameter from AWS Systems Manager Parameter Store. Name must begin with a / and point to the parameter you
    wish to access.

    example usage:
    `salt-call boto3_ssm.get_parameter "/path/to/my/parameter"`

    https://docs.aws.amazon.com/systems-manager/latest/APIReference/API_GetParameter.html

    :param name: The name of the parameter you want to query.
    :param with_decryption: If True, SecureString will return its decrypted value. If False, Secure String will return
                            the value still-encrypted. Has no effect on String or StringList types.
    :return: If the parameter type is a String or SecureString, returns a string. If the parameter type is StringList,
             returns a List of strings.
    """
    conn = _get_conn(region=region, key=key, keyid=keyid, profile=profile)
    try:
        response = conn.get_parameter(Name=name, WithDecryption=with_decryption)
        param_type = response['Parameter']['Type']
        if param_type == "StringList":
            param_value = response['Parameter']['Value'].split(',')
        else:
            param_value = response['Parameter']['Value']
        return param_value
    except botocore.exceptions.ClientError as e:
        try:
            response_code = e.response['Error']['Code']
        except (AttributeError, KeyError, TypeError):
            response_code = None

        log.error('Failed to retrieve parameter %s: %s', name, e)
        if response_code == 'ParameterNotFound':
            log.error("Does parameter '%s' exist in region '%s'?", name, conn.meta.region_name)
        return ""
