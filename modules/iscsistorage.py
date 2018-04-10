# -*- coding: utf-8 -*-
'''
A module to push the configuration for iSCSI shares to front end servers using
storage pools manged by libvirt.

:maintainer: Brent Lambert <brent@enpraxis.net>
:maturity: new
:depends: libvirt python API
:platform: all
:configuration: Default minion configuration is specified as follows::

    iscsistorage.iqn_base: 2000-01.com.mydomain
    iscsistorage.sip: <IP of your SAN>
    iscsistorage.sport: 3260

'''

import libvirt


# libvirt pool definintion

POOL = '''<pool type="iscsi">
  <name>{0}</name>
  <source>
    <host name="{1}" port="{2}" />
    <device path="{3}" />
  </source>
  <target>
    <path>/dev/disk/by-path</path>
  </target>
</pool>'''

CONNECT = 'qemu:///system'


# Helper functions

def _get_option(opt, kwargs):
    '''
    Return config options for iscsistorage
    '''
    if opt in kwargs:
        return kwargs[opt]
    return __salt__['config.option']('iscsistorage.{0}'.format(opt))


def add(name, **kwargs):
    '''
    Add an iSCSI share to a front end server's storage pool for use
    as a storage volume for a virtual server. The iSCSI target should
    already be created on the SAN and be ready to go.

    You can (and probably should) mount the target as a storage pool on
    all front end servers to facilitate live migration of virtual machines
    using the volume on your SAN. Note that you should never launch multipe
    virtual machines on different front end servers for the same target on
    the SAN, or very bad things will happen.

    name
      Name of the iSCSI target minus the IQN Base (required)

    iqn_base
      Override the iqn_base parameter specified in the minion config
      file (optional)

    sip
      Override the sip parameter specified in the minion config file
      (optional)

    sport
      Override the sport parameter specified in the minion config file
      (optional)

    CLI example::

        salt front* iscsistorage.add mytarget

        salt front* iscsistorage.add mytarget iqn_base=iqn.2000.01.com.altdomain

        salt front* iscsistorage.add mytarget sip=192.168.2.1 sport=43260

    '''
    iqn_base = _get_option('iqn_base', kwargs)
    niqn = '{0}:{1}'.format(iqn_base, name)
    sip = _get_option('sip', kwargs)
    sport = _get_option('sport', kwargs)

    pool_def = POOL.format(name, sip, sport, niqn)
    conn = libvirt.open(CONNECT)
    if conn:
        npool = conn.storagePoolDefineXML(pool_def, 0)
        if npool:
            npool.create(0)
            msg = {'Success': 'Created storage pool'}
        else:
            msg = {'Error': '(libvirt) could not create storage pool'}
    else:
        msg = {'Error': '(libvirt) could not connect'}

    return msg


def delete(name):
    '''
    Delete a storage pool from a front end server using libvirt.
    This will unmount the iSCSI Target from the front end server, but
    will not delete the iSCSI share from the SAN.

    name
      Name of iSCSI target derived from the IQN minus the IQN Base
      (required)


    CLI Example::

        salt front* iscsistorage.delete mytarget

    '''
    conn = libvirt.open(CONNECT)
    if conn:
        pool = conn.storagePoolLookupByName(name)
        if pool:
            if pool.isActive():
                pool.destroy()
            pool.undefine()
            msg = {'Success': 'Storage pool deleted'}
        else:
            msg = {'Error': '(libvirt) Could not delete storage pool'}
    else:
        msg = {'Error': '(libvirt) could not connect'}

    return msg
