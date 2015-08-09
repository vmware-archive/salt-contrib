#!/usr/bin/env python
"""
ec2_tags_rolecreds_crossplatform.py
 - Uses role credentials for authentication.
 - Works on Windows where Salt Python does not include Boto.
 - Exports all EC2 tags in an 'ec2_tags' grain.
 - Splits 'Role' tag into a list on 'ec2_roles' grain.
 - Tested with Python 2.6.9 and 2.7.6. 

To use it:
  1. Place ec2_rolecreds_crossplatform.py in <salt_root>/_grains/
  2. Test it
    $ salt '*' saltutil.sync_grains
    $ salt '*' grains.get ec2_tags
    $ salt '*' grains.get ec2_roles
Author: Jay Jakosky <jay.jakosky@gmail.com>
Licensed under Apache License (https://raw.github.com/saltstack/salt/develop/LICENSE)
(Inspired by https://github.com/saltstack/salt-contrib/blob/master/grains/ec2_tags.py)
"""

# See: http://docs.aws.amazon.com/general/latest/gr/sigv4_signing.html
# This version makes a GET request and passes the signature
# in the Authorization header.
import sys, os, base64, datetime, hashlib, hmac 
import urllib2
import urllib
import json
import xml.etree.cElementTree as etree
import logging

## If we're running outside of Salt, continue without error.
try:
    import salt.log
except ImportError:
  pass

def _get_region():
  az = urllib2.urlopen("http://169.254.169.254/2014-11-05/meta-data/placement/availability-zone/").readline()
  return az[:-1]

def _get_role_credentials():
  firstrole = urllib2.urlopen("http://169.254.169.254/2014-11-05/meta-data/iam/security-credentials/").readline()
  cred_json = urllib2.urlopen("http://169.254.169.254/2014-11-05/meta-data/iam/security-credentials/"+firstrole).read()
  cred_dict = json.loads(cred_json)
  return cred_dict

def _get_instance_id():
  instanceid = urllib2.urlopen("http://169.254.169.254/2014-11-05/meta-data/instance-id").readline()
  return instanceid

# Key derivation functions. See:
# http://docs.aws.amazon.com/general/latest/gr/signature-v4-examples.html#signature-v4-examples-python
def _sign(key, msg):
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

def _getSignatureKey(key, dateStamp, regionName, serviceName):
    kDate = _sign(('AWS4' + key).encode('utf-8'), dateStamp)
    kRegion = _sign(kDate, regionName)
    kService = _sign(kRegion, serviceName)
    kSigning = _sign(kService, 'aws4_request')
    return kSigning

def ec2_tags():
  log = logging.getLogger(__name__)

  # ************* REQUEST VALUES *************
  instanceid = _get_instance_id()
  method = 'GET'
  service = 'ec2'
  region = _get_region()
  host = 'ec2.'+region+'.amazonaws.com'
  endpoint = 'https://ec2.'+region+'.amazonaws.com'
  params = [('Action','DescribeTags')]
  params.append( ('Filter.1.Name','resource-id') )
  params.append( ('Filter.1.Value.1',instanceid) )
  params.append( ('Version','2015-04-15') )
  request_parameters = urllib.urlencode(params)

  creds = _get_role_credentials()

  access_key = creds['AccessKeyId']
  secret_key = creds['SecretAccessKey']
  token = creds['Token']

  if access_key is None or secret_key is None or token is None:
      log.error('No role credentials found.')
      return None

  # Create a date for headers and the credential string
  t = datetime.datetime.utcnow()
  amzdate = t.strftime('%Y%m%dT%H%M%SZ')
  datestamp = t.strftime('%Y%m%d') # Date w/o time, used in credential scope

  # Calculate AWS Signature V4
  canonical_uri = '/' 
  canonical_querystring = request_parameters
  canonical_headers = 'host:' + host + '\n' + 'x-amz-date:' + amzdate + '\n' + 'x-amz-security-token:' + token + '\n'
  signed_headers = 'host;x-amz-date;x-amz-security-token'
  payload_hash = hashlib.sha256('').hexdigest()
  canonical_request = method + '\n' + canonical_uri + '\n' + canonical_querystring + '\n' + canonical_headers + '\n' + signed_headers + '\n' + payload_hash

  algorithm = 'AWS4-HMAC-SHA256'
  credential_scope = datestamp + '/' + region + '/' + service + '/' + 'aws4_request'
  string_to_sign = algorithm + '\n' +  amzdate + '\n' +  credential_scope + '\n' +  hashlib.sha256(canonical_request).hexdigest()

  signing_key = _getSignatureKey(secret_key, datestamp, region, service)
  signature = hmac.new(signing_key, (string_to_sign).encode('utf-8'), hashlib.sha256).hexdigest()

  authorization_header = algorithm + ' ' + 'Credential=' + access_key + '/' + credential_scope + ', ' +  'SignedHeaders=' + signed_headers + ', ' + 'Signature=' + signature

  request_url = endpoint + '?' + canonical_querystring

  r = urllib2.Request(request_url)
  r.add_header('x-amz-date',amzdate)
  r.add_header('Authorization',authorization_header)
  r.add_header('x-amz-security-token',token)
  try:
    result = urllib2.urlopen(r)
  except Exception, e:
      log.error('Could not complete EC2 API request.')
      return None

  xml = result.read()
  xmlchop = '\n'.join(xml.split('\n')[1:]) 
  element = etree.fromstring( xmlchop )
  tree = etree.ElementTree(element)
  tagSet = tree.find("{http://ec2.amazonaws.com/doc/2015-04-15/}tagSet")
  items = tagSet.getiterator("{http://ec2.amazonaws.com/doc/2015-04-15/}item")

  ec2_tags = {}
  for i in items:
    key = i.find("{http://ec2.amazonaws.com/doc/2015-04-15/}key").text
    value = i.find("{http://ec2.amazonaws.com/doc/2015-04-15/}value").text
    ec2_tags[key] = value

  ret = dict(ec2_tags=ec2_tags)
  if 'Roles' in ec2_tags:
    ret['ec2_roles'] = ec2_tags['Roles'].split(',')

  return ret

if __name__ == '__main__':
  print ec2_tags()

