# -*- coding: utf-8 -*-
"""
ec2_tags.py - exports all EC2 tags in an 'ec2_tags' grain and splits 'Role' tag
              into a list on 'ec2_roles' grain.

To use it:

  1. Place ec2_tags.py in <salt_root>/_grains/
  2. Make sure boto version >= 2.8.0
  3. There are four ways of supplying AWS credentials used to fetch instance tags:

    i. Define them in AWS_CREDENTIALS below
    ii. Define AWS_ACCESS_KEY and AWS_SECRET_KEY environment variables
    iii. Provide them in the minion config like this:

        ec2_tags:
          aws:
            access_key: ABC123
            secret_key: abc123
    iv. Use IAM instance roles, the following policy will work:
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "Stmt1429127179000",
                    "Effect": "Allow",
                    "Action": [
                        "ec2:DescribeTags"
                    ],
                    "Resource": [
                        "*"
                    ]
                }
            ]
        }

  4. Test it

    $ salt '*' saltutil.sync_grains
    $ salt '*' grains.get ec2_tags
    $ salt '*' grains.get ec2_roles

Author: Emil Stenqvist <emsten@gmail.com>
Licensed under Apache License (https://raw.github.com/saltstack/salt/develop/LICENSE)

(Inspired by https://github.com/dginther/ec2-tags-salt-grain)
"""
from __future__ import absolute_import

import os
import logging
from salt.utils.versions import StrictVersion

import boto.ec2
import boto.utils

log = logging.getLogger(__name__)

AWS_CREDENTIALS = {
    'access_key': None,
    'secret_key': None,
}


def _get_instance_info():
    identity = boto.utils.get_instance_identity()['document']
    return identity['instanceId'], identity['region']


def _on_ec2():
    m = boto.utils.get_instance_metadata(timeout=0.1, num_retries=1)
    return bool(m)


def _get_credentials():
    creds = AWS_CREDENTIALS.copy()

    # Minion config
    if '__opts__' in globals():
        conf = __opts__.get('ec2_tags', {})
        aws = conf.get('aws', {})
        if aws.get('access_key') and aws.get('secret_key'):
            creds.update(aws)

    # 3. Get from environment
    access_key = os.environ.get('AWS_ACCESS_KEY') or os.environ.get('AWS_ACCESS_KEY_ID')
    secret_key = os.environ.get('AWS_SECRET_KEY') or os.environ.get('AWS_SECRET_ACCESS_KEY')
    if access_key and secret_key:
        creds.update(dict(access_key=access_key, secret_key=secret_key))

    return creds


def ec2_tags():
    boto_version = StrictVersion(boto.__version__)
    required_boto_version = StrictVersion('2.8.0')
    if boto_version < required_boto_version:
        log.error("Installed boto version %s < %s, can't find ec2_tags",
                  boto_version, required_boto_version)
        return None

    if not _on_ec2():
        log.info("Not an EC2 instance, skipping")
        return None

    instance_id, region = _get_instance_info()
    credentials = _get_credentials()

    # Connect to EC2 and parse the Roles tags for this instance
    try:
        conn = boto.ec2.connect_to_region(
            region,
            aws_access_key_id=credentials['access_key'],
            aws_secret_access_key=credentials['secret_key'],
        )
    except Exception as e:
        log.error("Could not get AWS connection: %s", e)
        return None

    ec2_tags = {}
    try:
        tags = conn.get_all_tags(filters={'resource-type': 'instance',
                                          'resource-id': instance_id})
        for tag in tags:
            ec2_tags[tag.name] = tag.value
    except Exception as e:
        log.error("Couldn't retrieve instance tags: %s", e)
        return None

    ret = dict(ec2_tags=ec2_tags)

    # Provide ec2_tags_roles functionality
    if 'Roles' in ec2_tags:
        ret['ec2_roles'] = ec2_tags['Roles'].split(',')

    return ret
