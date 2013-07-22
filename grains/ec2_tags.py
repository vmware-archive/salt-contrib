"""
ec2_tags.py - exports all EC2 tags in an 'ec2_tags' grain

To use it:

  1. Place ec2_tags.py in roots/_grains/
  2. There are three ways of supplying AWS credentials used to fetch instance tags:

    i. Define them in AWS_CREDENTIALS below
    ii. Define AWS_ACCESS_KEY and AWS_SECRET_KEY environment variables
    iii. Provide them in the minion config like this:

        ec2_tags:
          aws:
            access_key: ABC123
            secret_key: abc123

  3. Test it

    $ salt '*' saltutil.sync_grains
    $ salt '*' grains.get tags

Author: Emil Stenqvist <emsten@gmail.com>
(Inspired by https://github.com/dginther/ec2-tags-salt-grain)
"""

import os
import boto.ec2
import boto.utils
import logging
import salt.log

log = logging.getLogger(__name__)

AWS_CREDENTIALS = {
  'access_key': None,
  'secret_key': None,
}

def _get_instance_info():
  identity = boto.utils.get_instance_identity()['document']
  return (identity['instanceId'], identity['region'])

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

  (instance_id, region) = _get_instance_info()
  credentials = _get_credentials()
  if not credentials:
    log.info("ec2_tags: no AWS credentials found, see documentation for how to provide them.")
    return None

  # Connect to EC2 and parse the Roles tags for this instance
  conn = boto.ec2.connect_to_region(region,
      aws_access_key_id=credentials['access_key'],
      aws_secret_access_key=credentials['secret_key'])

  tags = {}
  try:
    reservation = conn.get_all_instances(instance_ids=[ instance_id ])[0]
    instance = reservation.instances[0]
    tags = instance.tags
  except IndexError, e:
    log.error("Couldn't retrieve instance information: %s", e)
    return None

  return { 'ec2_tags': tags }

if __name__ == '__main__':
  print ec2_tags()
