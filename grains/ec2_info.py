# -*- coding: utf-8 -*-
"""
Get some grains information that is only available in Amazon AWS

Author: Erik Günther

"""
import ast
import logging
import httplib
import socket
import os

# Set up logging
LOG = logging.getLogger(__name__)

# Initialize grain variable
grains = {}

def _call_aws(url):
    """
    Call AWS via httplib. require correct path to data will
    Host: 169.254.169.254

    """

    conn = httplib.HTTPConnection("169.254.169.254", 80, timeout=1)
    conn.request('GET', url)
    response = conn.getresponse()
    if response.status != 200:
        return ""

    return response.read()


def _get_ec2_hostinfo(path=""):
    """
    Will return grain information about this host that is EC2 specific

    "kernelId" : "aki-12345678",
    "ramdiskId" : None,
    "instanceId" : "i-12345678",
    "instanceType" : "c1.medium",
    "billingProducts" : None,
    "architecture" : "i386",
    "version" : "2010-08-31",
    "accountId" : "123456789012",
    "imageId" : "ami-12345678",
    "availabilityZone" : "eu-west-1a",
    "pendingTime" : "2012-07-10T03:54:24Z",
    "devpayProductCodes" : None,
    "privateIp" : "10.XX.YY.ZZ",
    "region" : "eu-west-1",
    "local-ipv4" : "10.XX.YY.ZZ",
    "local-hostname" : "ip-10-XX-YY-ZZ.eu-west-1.compute.internal",
    "public-ipv4" : "AA.BB.CC.DD",
    "public-hostname" : "ec2-AA-BB-CC-DD.eu-west-1.compute.amazonaws.com"
    """


    for line in read_uri("latest/meta-data/%s" % path).split("\n"):
        if line[-1] != "/":
            grains["ec2_" + line] = read_uri("latest/meta-data/%s" % (path + line))
            #grains.append(read_uri("latest/meta-data/%s") % (path + line))
        else:
            _walk(path + line)


def ec2_info():
    """
    Collect some extra host information
    """
    try:
        #First do a quick check if AWS magic URL work. If so we guessing that
        # we are running in AWS and will try to get more data.
        _call_aws('/')
    except (socket.timeout, socket.error, IOError):
        return {}

    try:
        _get_ec2_hostinfo()
        return grains
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
