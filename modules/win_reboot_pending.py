# -*- coding: utf-8 -*-
'''
_modules.win_reboot_pending.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Description
    Determine the pending reboot status of a Windows minion.
References
    https://goo.gl/SXlwAA
ToDo
    Add support for SCCM Client via WMI.
'''

# Import python libs
from __future__ import absolute_import
import logging

# Import salt libs
import salt.utils

_HKEY = 'HKEY_LOCAL_MACHINE'
_LOG = logging.getLogger(__name__)

# Define the module's virtual name
__virtualname__ = 'win_reboot_pending'

def __virtual__():
    '''
    Only works on Windows systems.
    '''
    if salt.utils.is_windows():
        return __virtualname__
    return False

def _get_component_pending():
    '''
    Determine whether there are Component Based Servicing reboots pending.

    Returns a boolean representing whether reboots are pending.
    '''
    vname = '(Default)'
    key = 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Component Based Servicing\\RebootPending'

    reg_ret = __salt__['reg.read_value'](_HKEY, key, vname)

    # So long as the registry key exists, a reboot is pending.
    if reg_ret['success']:
        _LOG.debug('Found key: %s', key)
        return True
    else:
        _LOG.debug('Unable to access key: %s', key)
    return False

def _get_computer_rename_pending():
    '''
    Determine whether there is a computer rename pending.

    Returns a boolean representing whether a rename is pending.
    '''
    vname = 'ComputerName'
    base_key = 'SYSTEM\\CurrentControlSet\\Control\\ComputerName\\'
    active_key = '{}ActiveComputerName'.format(base_key)
    pending_key = '{}ComputerName'.format(base_key)

    # Compare the values of the two ComputerName properties. If they do not
    # match, then there is a reboot pending. Also notable is that unlike the
    # other reboot checking functions, if the keys do not exist, then we should
    # log it as an error.

    active_reg_ret = __salt__['reg.read_value'](_HKEY, active_key, vname)

    if active_reg_ret['success']:
        _LOG.debug('Found key: %s', active_key)
    else:
        _LOG.error('Unable to access key: %s', active_key)
        return False

    pending_reg_ret = __salt__['reg.read_value'](_HKEY, pending_key, vname)

    if pending_reg_ret['success']:
        _LOG.debug('Found key: %s', pending_key)
    else:
        _LOG.error('Unable to access key: %s', pending_key)
        return False

    if str(active_reg_ret['vdata']).lower() != str(pending_reg_ret['vdata']).lower():
        return True
    return False

def _get_domain_join_pending():
    '''
    Determine whether there is a domain join pending.

    Returns a boolean representing whether reboots are pending.
    '''
    vname = '(Default)'
    base_key = 'SYSTEM\\CurrentControlSet\\Services\\Netlogon\\'
    avoid_key = '{}AvoidSpnSet'.format(base_key)
    join_key = '{}JoinDomain'.format(base_key)

    # If either the avoid_key or join_key is present,
    # then there is a reboot pending.

    avoid_reg_ret = __salt__['reg.read_value'](_HKEY, avoid_key, vname)

    if avoid_reg_ret['success']:
        _LOG.debug('Found key: %s', avoid_key)
        return True
    else:
        _LOG.debug('Unable to access key: %s', avoid_key)

    join_reg_ret = __salt__['reg.read_value'](_HKEY, join_key, vname)

    if join_reg_ret['success']:
        _LOG.debug('Found key: %s', join_key)
        return True
    else:
        _LOG.debug('Unable to access key: %s', join_key)
    return False

def _get_file_rename_pending():
    '''
    Determine whether there are file renames pending.

    Returns a boolean representing whether a rename is pending.
    '''
    vnames = ['PendingFileRenameOperations', 'PendingFileRenameOperations2']
    key = 'SYSTEM\\CurrentControlSet\\Control\\Session Manager'

    # If any of the value names exist and have value data set,
    # then a reboot is pending.

    for vname in vnames:
        reg_ret = __salt__['reg.read_value'](_HKEY, key, vname)

        if reg_ret['success']:
            _LOG.debug('Found key: %s', key)

            if reg_ret['vdata'] and (reg_ret['vdata'] != '(value not set)'):
                return True
        else:
            _LOG.debug('Unable to access key: %s', key)
    return False

def _get_server_manager_pending():
    '''
    Determine whether there are reboot attempts pending.

    Returns a boolean representing whether reboot attempts are pending.
    '''
    vname = 'CurrentRebootAttempts'
    key = 'SOFTWARE\\Microsoft\\ServerManager'

    # There are situations where it's possible to have '(value not set)' as
    # the value data, and since an actual reboot wont be pending in that
    # instance, just catch instances where we try unsuccessfully to cast as int.

    reg_ret = __salt__['reg.read_value'](_HKEY, key, vname)

    if reg_ret['success']:
        _LOG.debug('Found key: %s', key)

        try:
            if int(reg_ret['vdata']) > 0:
                return True
        except ValueError:
            pass
    else:
        _LOG.debug('Unable to access key: %s', key)
    return False

def _get_update_pending():
    '''
    Determine whether there are post-update reboots pending.

    Returns a boolean representing whether reboots are pending.
    '''
    vname = '(Default)'
    key = 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\WindowsUpdate\\Auto Update\\RebootRequired'

    reg_ret = __salt__['reg.read_value'](_HKEY, key, vname)

    # So long as the registry key exists, a reboot is pending.
    if reg_ret['success']:
        _LOG.debug('Found key: %s', key)
        return True
    else:
        _LOG.debug('Unable to access key: %s', key)
    return False

def get_reboot_pending():
    '''
    Determine whether there is a reboot pending.

    Returns a boolean representing whether reboots are pending.

    CLI Example:

    .. code-block:: bash

        salt '*' win_reboot_pending.get_reboot_pending
    '''
    # Order the checks for reboot pending in most to least likely.
    checks = (_get_update_pending, _get_file_rename_pending, _get_server_manager_pending,
              _get_component_pending, _get_computer_rename_pending, _get_domain_join_pending)
    for check in checks:
        if check():
            return True
    return False

