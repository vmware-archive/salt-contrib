#!/usr/bin/env python

import os
import socket
import pprint
import boto.ec2
import httplib

def ec2_roles():
	# Get meta-data to determine which availability zone we are in
	httpconn = httplib.HTTPConnection("169.254.169.254", 80, 10 )
	httpconn.request('GET', "/latest/meta-data/placement/availability-zone")
	response = httpconn.getresponse()
	az = response.read()
	# Chop off the AZ letter to get the region
	region = az[:-1]
	# Get the hostname of the instance we're on
	hostname = socket.gethostname()
	# Connect to EC2 and parse the Roles tags for this instance
	conn = boto.ec2.connect_to_region(region, 
		aws_access_key_id='PUTACCESSKEYHERE',
		aws_secret_access_key='PUTSECRETACCESSKEYHERE')
	reservation = conn.get_all_instances(filters={"tag:Name": hostname})[0]
	instance = reservation.instances[0]
	tags = instance.tags.get('Roles','')
	# Initialize grains
	grains={}
	# Fill grains with tags
	grains['ec2_roles'] = tags.split(',')
	return grains
