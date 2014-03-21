"""
ec2_tags.py - exports all EC2 tags in an 'ec2_tags' grain

To use it:

  1. Place ec2_tags.py in <salt_root>/_grains/
  2. Make sure boto version >= 2.8.0
  3. There are three ways of supplying AWS credentials used to fetch instance tags:

    i. Define them in AWS_CREDENTIALS below
    ii. Define AWS_ACCESS_KEY and AWS_SECRET_KEY environment variables
    iii. Provide them in the minion config like this:

        ec2_tags:
          aws:
            access_key: ABC123
            secret_key: abc123

  4. Test it

    $ salt '*' saltutil.sync_grains
    $ salt '*' grains.get tags

Author: Emil Stenqvist <emsten@gmail.com>
Licensed under Apache License (https://raw.github.com/saltstack/salt/develop/LICENSE)

(Inspired by https://github.com/dginther/ec2-tags-salt-grain)
"""

import os
import logging
from distutils.version import StrictVersion

import boto.ec2
import boto.utils
import salt.log

log = logging.getLogger(__name__)

AWS_CREDENTIALS = {
    'access_key': None,
    'secret_key': None,
}

def _get_instance_info():
    identity = boto.utils.get_instance_identity()['document']
    return (identity['instanceId'], identity['region'])

def _on_ec2():
    m = boto.utils.get_instance_metadata(timeout=0.1, num_retries=1)
    return len(m.keys()) > 0

def _get_credentials():

    # 1. Get from static AWS_CREDENTIALS
    if AWS_CREDENTIALS['access_key'] and AWS_CREDENTIALS['secret_key']:
        return AWS_CREDENTIALS

    # 2. Get from minion config
    try:
        aws = __opts__.get['ec2_tags']['aws']
        return {
                'access_key': aws['access_key'],
                'secret_key': aws['secret_key'],}
    except (KeyError, NameError):
        pass

    # 3. Get from environment
    access_key = os.environ.get('AWS_ACCESS_KEY') or os.environ.get('AWS_ACCESS_KEY_ID')
    secret_key = os.environ.get('AWS_SECRET_KEY') or os.environ.get('AWS_SECRET_ACCESS_KEY')
    if access_key and secret_key:
        return {
                'access_key': aws['access_key'],
                'secret_key': aws['secret_key'],}

    return None

def ec2_tags():

    boto_version = StrictVersion(boto.__version__)
    required_boto_version = StrictVersion('2.8.0')
    if boto_version < required_boto_version:
        log.error("%s: installed boto version %s < %s, can't find ec2_tags",
                __name__, boto_version, required_boto_version)
        return None

    if not _on_ec2():
        log.info("%s: not an EC2 instance, skipping", __name__)
        return None

    (instance_id, region) = _get_instance_info()
    credentials = _get_credentials()
    if not credentials:
        log.error("%s: no AWS credentials found, see documentation for how to provide them.", __name__)
        return None

    # Connect to EC2 and parse the Roles tags for this instance
    conn = boto.ec2.connect_to_region(region,
            aws_access_key_id=credentials['access_key'],
            aws_secret_access_key=credentials['secret_key'])

    tags = {}
    try:
        _tags = conn.get_all_tags(filters={'resource-type': 'instance',
                'resource-id': instance_id})
        for tag in _tags:
            tags[tag.name] = tag.value
    except IndexError, e:
        log.error("Couldn't retrieve instance information: %s", e)
        return None

    return { 'ec2_tags': tags }

if __name__ == '__main__':
    print ec2_tags()
