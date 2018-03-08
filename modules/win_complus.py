# -*- coding: utf-8 -*-
'''
Microsoft Component Service management via powershell module

:platform:      Windows


'''

# Import python libs
from __future__ import absolute_import
from __future__ import unicode_literals
import json
import logging
import os

# Import salt libs
from salt.ext.six.moves import range
from salt.exceptions import SaltInvocationError
import salt.utils

_LOG = logging.getLogger(__name__)

_accesslevels = {
    'ApplicationLevel': 0,
    'ApplicationComponentLevel': 1
}

_authentications = {
    'Default': 0,
    'None': 1,
    'Connect': 2,
    'Call': 3,
    'Packet': 4,
    'Integrity': 5,
    'Privacy': 6
}

_impersonationlevels = {
    'Anonymous': 1,
    'Identify': 2,
    'Impersonate': 3,
    'Delegate': 4
}

# Define the module's virtual name
__virtualname__ = 'win_complus'


def __virtual__():
    '''
    Load only on Windows
    '''
    if not salt.utils.is_windows():
        return (False, 'Module win_complus: module only works on Windows systems')
    '''
    Check if PowerShell is installed
    '''
    powershell_info = __salt__['cmd.shell_info']('powershell')
    if not powershell_info['installed']:
        return False, 'PowerShell not available'

    return __virtualname__


def _runps(func, as_json=False):
    '''
    Execute a function from the WebAdministration PS module.
    '''
    command = ''

    if as_json:
        command = '{0} ConvertTo-Json -Compress -Depth 4 -InputObject @({1})'.format(command,
                                                                                     func)
    else:
        command = '{0} {1}'.format(command, func)

    cmd_ret = __salt__['cmd.run_all'](command, shell='powershell', python_shell=True)

    if cmd_ret['retcode'] != 0:
        _LOG.error('Unable to execute command: %s\nError: %s', command, cmd_ret['stderr'])
    return cmd_ret


def test():
    return True


def list_apps():
    '''
    Get all configured COM+ applications

    :return: A dictionary of the application names.
    :rtype: dict

    CLI Example:

    .. code-block:: bash

        salt '*' win_complus.list_apps
    '''

    ret = dict()
    pscmd = list()

    pscmd.append(r"$oCOMAdminCatalog = New-Object -com 'COMAdmin.COMAdminCatalog';")
    pscmd.append(r"$oCOMApplications = $oCOMAdminCatalog.GetCollection('Applications');")
    pscmd.append(r"$oCOMApplications.Populate();")
    pscmd.append(r"$oCOMApplications | Select-Object Name,  Key, Valid")

    cmd_ret = _runps(func=str().join(pscmd), as_json=True)

    try:
        items = json.loads(cmd_ret['stdout'], strict=False)
    except ValueError:
        _LOG.error('Unable to parse return data as Json.')

    for item in items:
        ret[item['Name']] = {'key': item['Key'], 'valid': item['Valid']}

    if not ret:
        _LOG.warning('No apps found in output: %s', cmd_ret)
    return ret


def create_app(name, description='', accesscheck=True, accesslevel='ApplicationLevel', authentication='Default', impersonationlevel='Anonymous', identity=None, password=None):
    '''
    Create an COM+ application.

    .. note:

        This function only validates against the application name, and will return True
        even if the application already exists with a different configuration. It will not
        modify the configuration of an existing application.

    :param str name: The application.
    :param str description: The application description.
    :param bool accesscheck: Application access check. True | False
    :param str accesslevel: Access Checks Level.
        ApplicationLevel = 0 (Default)
        ApplicationComponentLevel = 1
    :param str authentication:
        Default   = 0 (Default)
        None      = 1
        Connect   = 2
        Call      = 3
        Packet    = 4
        Integrity = 5
        Privacy   = 6
    :param str impersonationlevel:
        Anonymous   = 1 (Default)
        Identify    = 2
        Impersonate = 3
        Delegate    = 4
    :param str identity: Application identity. Optional
    :param str password: Application identity password. Optional

    :return: A boolean representing whether all changes succeeded.
    :rtype: bool

    CLI Example:

    .. code-block:: bash

        salt '*' win_complus.create_app name='app0' description='desc0' accesscheck=True accesslevel='ApplicationLevel'
    '''
    pscmd = list()
    current_apps = list_apps()

    if name in current_apps:
        _LOG.debug("Application already present: %s", name)
        return True

    # TODO:Parámetros...

    pscmd.append(r"$oCOMAdminCatalog = New-Object -com 'COMAdmin.COMAdminCatalog';")
    pscmd.append(r"$oCOMApplications = $oCOMAdminCatalog.GetCollection('Applications');")
    pscmd.append(r"$oCOMApplications.Populate();")
    pscmd.append(r"$oCOMApplication = $oCOMApplications.Add();")
    pscmd.append(r"$oCOMApplication.Value('Name') = '{0}';".format(name))
    pscmd.append(r"$oCOMApplication.Value('Description') = '{0}';".format(description))
    pscmd.append(r"$oCOMApplication.Value('ApplicationAccessChecksEnabled') = {0};".format(int(accesscheck)))
    pscmd.append(r"$oCOMApplication.Value('AccessChecksLevel') = {0};".format(_accesslevels[accesslevel]))
    pscmd.append(r"$oCOMApplication.Value('Authentication') = {0};".format(_authentications[authentication]))
    pscmd.append(r"$oCOMApplication.Value('ImpersonationLevel') = {0};".format(_impersonationlevels[impersonationlevel]))

    if identity:
        pscmd.append(r"$oCOMApplication.Value('Identity') = '{0}';".format(identity))
        pscmd.append(r"$oCOMApplication.Value('Password') = '{0}';".format(password))

    pscmd.append(r"$oCOMApplications.SaveChanges();")

    cmd_ret = _runps(str().join(pscmd))

    if cmd_ret['retcode'] == 0:
        new_apps = list_apps()

        if name in new_apps:
            _LOG.debug('Application created successfully: %s', name)
            return True
    _LOG.error('Unable to create application: %s', name)
    return False


def remove_app(name):
    '''
    Delete a application from COM+.

    :param str name: The IIS site name.

    :return: A boolean representing whether all changes succeeded.
    :rtype: bool

    CLI Example:

    .. code-block:: bash

        salt '*' win_complus.remove_app name='Myapp'

    '''
    pscmd = []
    current_apps = list_apps()

    if name not in current_apps:
        _LOG.debug('Application already absent: %s', name)
        return True

    pscmd.append(r"$oCOMAdminCatalog = New-Object -com 'COMAdmin.COMAdminCatalog';")
    pscmd.append(r"$oCOMAdminCatalog.ShutdownApplication('{0}');".format(name))
    pscmd.append(r"$oCOMApplications = $oCOMAdminCatalog.GetCollection('Applications');")
    pscmd.append(r"$oCOMApplications.Populate();")
    pscmd.append(r"$lIndex = 0;")
    pscmd.append(r"Foreach($oCOMApplication In $oCOMApplications){")
    pscmd.append(r"If($oCOMApplication.Value('Name') -eq '{0}'){{".format(name))
    pscmd.append(r"$oCOMApplications.Remove($lIndex);")
    pscmd.append(r"$oCOMApplications.SaveChanges();")
    pscmd.append("Exit;")
    pscmd.append(r"};")
    pscmd.append(r"$lIndex = $lIndex + 1;")
    pscmd.append(r"};")

    cmd_ret = _runps(str().join(pscmd))

    if cmd_ret['retcode'] == 0:
        _LOG.debug('Application removed successfully: %s', name)
        return True
    _LOG.error('Unable to remove application: %s', name)
    return False
