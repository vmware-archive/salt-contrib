"""
ec2_tag_roles.py - imports tags for an instance and makes grains for that instance out of them

To use it:

                1: Copy ec2_tag_roles.py to <salt_Root>/_grains/
                2: Make sure boto is installed and version is >= 2.8.0
                3: Enter your AWS credentials in the variables below
                4: Test:
                        salt '*' saltutil.sync_grains
                        salt '*' grains.items

Author: Demian Ginther <st.siluted@gmail.com>
License: Apache License 2.0 (http://www.apache.org/licenses/LICENSE-2.0)
"""

#!/usr/bin/env python

import os
import socket
import pprint
import boto.ec2
from boto.utils import get_instance_metadata
import httplib

def ec2_roles():
                # Get meta-data from instance
                metadata = get_instance_metadata()

                # Chop off the AZ letter to get the region
                region = metadata['placement']['availability-zone'][:-1]

                # Connect to EC2 and get the instance information for this instance id
                conn = boto.ec2.connect_to_region(region,
                aws_access_key_id='XXXXXXXXXXXXXXXXXXXX',
                aws_secret_access_key='XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
                reservation = conn.get_all_reservations(filters={'instance-id': metadata['instance-id']})

                # Dump tags from instance. Feel free to add variables here to get other tags.
                # Use var = instance.tags['TAG NAME']
                instances = [i for r in reservation for i in r.instances]
                for instance in instances:
                        roles = instance.tags['Roles']

                # Initialize grains dict
                grains={}

                # Fill grains dict with tags
                # Don't forget to add any variables you added from above!
                grains['ec2_roles'] = roles.split(',')

                # Return our dict
                return grains
