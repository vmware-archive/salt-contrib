# -*- coding: utf-8 -*-
"""
ec2_tags.py - exports all EC2 tags in an 'ec2_tags' grain and splits 'Role' tag
              into a list on 'ec2_roles' grain.

To use it:

  1. Place ec2_tags.py in <salt_root>/_grains/
  2. Make sure boto3 and python3.6 or greater is installed on minions
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
(modified on 2020-12-01 by fred damstra to use boto3)
"""
import boto3
import os
import logging

import urllib.request


log = logging.getLogger(__name__)

AWS_CREDENTIALS = {
    'access_key': None,
    'secret_key': None,
}


def _get_instance_id():
    instance_id = urllib.request.urlopen('http://169.254.169.254/latest/meta-data/instance-id').read().decode()
    log.debug(f'instance id = {instance_id}')
    return instance_id


def _get_instance_region():
    availability_zone = urllib.request.urlopen('http://169.254.169.254/latest/meta-data/placement/availability-zone').read().decode()
    log.debug(f'availability zone = { availability_zone }')
    region = availability_zone[:-1] # Remove the last character. Does this work everywhere?
    return region


def _on_ec2():
    meta = 'http://169.254.169.254/latest/meta-data/ami-id'
    try:
        response = urllib.request.urlopen(meta).read().decode()
        log.debug(f'_on_ec2 response={response}')
        if 'ami' in response:
            return True
        else:
            return False
    except Exception as nometa:
        return False


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
    if not _on_ec2():
        log.info("Not an EC2 instance, skipping")
        return None

    credentials = _get_credentials()
    instance_id = _get_instance_id()
    region = _get_instance_region()

    # Connect to EC2 and parse the Roles tags for this instance
    client = boto3.client('ec2', region_name=region)
    response = client.describe_tags( Filters = [
      { 'Name': 'resource-id', 'Values': [ instance_id ] },
      { 'Name': 'resource-type', 'Values': [ 'instance' ] },
    ])

    ec2_tags = {}
    for tag in response['Tags']:
        ec2_tags[tag['Key']] = tag['Value']

    ret = dict(ec2_tags=ec2_tags)

    # Provide ec2_tags_roles functionality
    if 'Roles' in ec2_tags:
        ret['ec2_roles'] = ec2_tags['Roles'].split(',')

    return ret
