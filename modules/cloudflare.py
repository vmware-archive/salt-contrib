# -*- coding: utf-8 -*-
'''
Module for interacting with Cloudflare's API

:depends:  - pyflare Python Module
             requests Python Module
:configuration:  - Specify your Cloudflare credentials in Pillar at cloudflare:email
                   and cloudflare:apikey
'''

import logging
import salt.utils

try:
    from pyflare import Pyflare
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False

def __virtual__():
    if not HAS_DEPS:
        return False
    return 'cloudflare'

def _pyflare_obj():
    '''
    Return a new Pyflare object given API credentials provided via pillar
    '''
    return Pyflare(__salt__['pillar.get']('cloudflare:email',''), __salt__['pillar.get']('cloudflare:apikey',''))

def _get_ip_by_iface(iface, rec_type):
    '''
    Returns the IPv4 or IPv6 address of a given network interface.
    '''
    if iface not in __salt__['network.interfaces']():
        return None

    if rec_type == 'A':
        iface_type = 'inet'
    elif rec_type == 'AAAA':
        iface_type = 'inet6'
    else:
        return None

    return __salt__['network.interfaces']()[iface][iface_type][0]['address']

def _existing_record(zone, rec_name, type):
    '''
    Searches for (and returns) an existing record of given zone, record name, and type.
    '''
    for rec in _pyflare_obj().rec_load_all(zone):
        if ".".join([rec_name, zone]) == rec['name'] and rec['type'] == type:
            return rec
    return None

def _interpret_name(rec_name):
    '''
    Returns a "host" section for a DNS record by substituting values for any 
    supported 
    '''
    if '%M' in rec_name:
        return rec_name.replace('%M', __salt__['grains.get']('id', ''))
    else:
        if '%H' in rec_name:
            return rec_name.replace('%H', __salt__['grains.get']('host',''))
        else:
            return __salt__['grains.get']('host', '')

def add_record(zone=None, iface=None, rec_name='%H', type='A', ttl=1, edit_if_exists=False):
    '''
    Add A or AAAA records to a zone on your account which point to the IP address(es)
    of given network interfaces.

    CLI Examples:

    .. code-block:: bash

        salt '*' cloudflare.add_record example.com eth0

    By default, the minion's 'host' grain will be used for the host portion. However,
    you may modify this by using '%H' within a string passed as rec_name:

    .. code-block:: bash

        salt '*' cloudflare.add_record example.com eth0 rec_name='%H-app'

    If your nodes' hostnames are web1, web2, etc, the above command will add records like
    web1-app.example.com, web2-app.example.com, etc.

    You may also use '%M' in rec_name and minion_id will be substituted instead of hostname.

    By default, this function will add A records. However you may also add AAAA records:

    .. code-block:: bash

        salt '*' cloudflare.add_record example.com eth0 type='AAAA'

    Specify edit_if_exists=True if you would like to overwrite any existing records matching
    zone, rec_name, and type. The default is false (i.e. existing records will not be overwritten)
    '''
    cf = _pyflare_obj()
    if not zone or not iface:
        return 'ERROR: must provide both zone and iface whose IP address to add.'
    if type not in ['A','AAAA']:
        return 'ERROR: record type must be A or AAAA.'
    
    # TODO: provide ways to retrieve IP by inputs other than interface (e.g. CIDR block)
    content = _get_ip_by_iface(iface, type)
    if not content:
        return 'ERROR: unable to get IP address; bad interface or DNS record type provided.'

    name = _interpret_name(rec_name)        
    record = _existing_record(zone, name, type)
    if record:
        msgs = ["record %s.%s (%s) already exists" % (name, zone, type)]
        if edit_if_exists:
            # add log msg about current value and what we're writing?
            cf.rec_edit(zone, type, record['rec_id'], name, content, ttl=ttl)
            msgs.append("edited record; now points to %s" % content)
        else:
            # add some log message about not editing the file?
            msgs.append("not editing because edit_if_exists=False")
    else:
        cf.rec_new(zone, type, name, content, ttl=ttl)
        msgs = ["added %s record: %s.%s => %s" % (type, name, zone, content)]
    return msgs

def del_record(zone=None, rec_name='%H', type='A'):
    '''
    Delete an A or AAAA record in the given zone with given record name.
    As with ``add_record``, you may use %H and %M in rec_name.

    .. code-block:: bash

        salt '*' cloudflare.del_record example.com s

    '''
    if not zone:
        return 'ERROR: you must provide a zone to search for records to delete.'
    name = _interpret_name(rec_name)
    record = _existing_record(zone, name, type)
    if record:
        _pyflare_obj().rec_delete(zone, record['rec_id'])
        return "Deleted record %s (%s)" % (record['name'], type)
    else:
        return "ERROR: Unable to find existing record for '%s' in zone '%s'." % (name, zone)
