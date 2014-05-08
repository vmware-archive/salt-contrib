"""
A module to configure iSCSI shares in iSCSI storage pools managed by
libvirt.

:maintainer: Brent Lambert <brent@enpraxis.net>
:maturity: new
:depends: libvirt python API
:platform: all
:configuration: Default configuration is specified as follows::
    
    iscsistorage.iqn_base: 2007-12.net.enpraxis
    iscsistorage.sip: 192.168.5.67
    iscsistorage.sport: 3260
    
"""

import libvirt


# libvirt pool definintion

pool = """<pool type="iscsi">
  <name>{0}</name>
  <source>
    <host name="{1}" port="{2}" />
    <device path="{3}" />
  </source>
  <target>
    <path>/dev/disk/by-path</path>
  </target>
</pool>"""

connect = 'qemu:///system'    


# Helper functions

def _get_option(opt, kwargs):
    """
    """
    if opt in kwargs:
        return kwargs[opt]
    return __salt__['config.option']('iscsistorage.{0}'.format(opt))


def add(name, **kwargs):
    """
    """
    iqn_base = _get_option('iqn_base', kwargs)
    niqn = '{0}:{1}'.format(iqn_base, name)
    sip = _get_option('sip', kwargs)
    sport = _get_option('sport', kwargs)
    
    pool_def = pool.format(name, sip, sport, niqn)
    conn = libvirt.open(connect)
    if conn:
        npool = conn.storagePoolDefineXML(pool_def, 0)
        if npool:
            npool.create(0)
            msg = 'Success'
        else:
            msg = 'Error: (libvirt) could not create stoage pool'
    else:
         msg = 'Error: (libvirt) could not connect'    

    return msg,


def delete(name, **kwargs):
    """
    """
    conn = libvirt.open(connect)
    if conn:
        pool = conn.storagePoolLookupByName(name)
        if pool:
            if pool.isActive():
                pool.destroy()
            pool.undefine()
            msg = 'Success'
        else:
            msg = 'Error: (libvirt) Could not delete storage pool'
    else:
         msg = 'Error: (libvirt) could not connect'    
    
    return msg,

