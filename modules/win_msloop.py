# -*- coding: utf-8 -*-
'''
_modules.win_msloop
~~~~~~~~~~~~~~~~~~~
Description
    Manage Microsoft Loopback Adapters on Windows servers.
Dependencies
    DevCon is required, and should be installed in the System Path.
References
    https://goo.gl/3LBp1V
    https://goo.gl/49taoW
    http://goo.gl/3O7ICp
'''

# Import python libs
from __future__ import absolute_import
import logging
import os
import re
import time
# Import salt libs
from salt.exceptions import SaltInvocationError
import salt.utils

try:
    import wmi
    import salt.utils.winapi
    _HAS_MODULE_DEPENDENCIES = True
except ImportError:
    _HAS_MODULE_DEPENDENCIES = False

_LOG = logging.getLogger(__name__)

# Define the module's virtual name
__virtualname__ = 'win_msloop'


def __virtual__():
    '''
    Only works on Windows systems that have WMI and DevCon.
    '''
    if salt.utils.is_windows():
        if _HAS_MODULE_DEPENDENCIES:
            if salt.utils.which('devcon.exe'):
                return __virtualname__
            else:
                _LOG.debug('Unable to find executable: devcon.exe')
        else:
            _LOG.debug('Unable to load dependencies.')
    return False


def _get_address_family_as_int(name):
    '''
    Get the uint16 representation of the address family, which is needed by WMI.
    '''
    name = name.lower()
    address_family_mapping = {'ipv4': 2,
                              'ipv6': 23}

    if name not in address_family_mapping:
        raise SaltInvocationError(("Address family '{}' not in valid family list:"
                                   ' {}').format(name, address_family_mapping.keys()))

    _LOG.debug('Address family int: %s', address_family_mapping[name])
    return address_family_mapping[name]


def _interface_name_is_valid(name):
    '''
    Determine whether the interface name specified is valid.
    '''
    max_length = 256
    reg_valid_chars = r'^[^\t\\/:?*"<>|]*$'

    if len(name) <= max_length:
        if re.match(reg_valid_chars, name):
            _LOG.debug('Interface name is valid: %s', name)
            return True
        else:
            raise SaltInvocationError('Interface name contains invalid characters.')
    else:
        raise SaltInvocationError(('Interface name exceeded maximum length of {}'
                                   ' characters.').format(max_length))
    return False


def _list_interfaces(name=None, as_instance_id=False):
    '''
    Get the display names or instance ids for all valid interfaces,
    or for the provided interface.
    '''
    ret = list()

    # The wql query is different depending on whether we
    # want the Name or ID returned.
    id_type = 'NetConnectionID'
    if as_instance_id:
        id_type = 'PNPDeviceID'

    # NetConnectionID field contains the display name, which
    # is the unique name used most often by users/admins.
    wql_suffix = 'NetConnectionStatus=2'
    if name:
        wql_suffix = "NetConnectionID='{}'".format(name)

    wql = 'Select {} from Win32_NetworkAdapter where {}'.format(id_type, wql_suffix)
    with salt.utils.winapi.Com():
        try:
            connection = wmi.WMI()
            wmi_ret = connection.query(wql)
        except wmi.x_wmi as error:
            _LOG.error('Encountered WMI error: %s', error.com_error)
        except (AttributeError, IndexError) as error:
            _LOG.error('Error getting Win32_NetworkAdapter: %s', error)

        for interface in wmi_ret:
            interface_id = getattr(interface, id_type)
            ret.append(interface_id)
            _LOG.debug('Interface from WMI: %s', interface_id)

    if not ret:
        _LOG.debug('No valid interfaces found.')
    return ret


def get_interface(name, as_instance_id=False):
    '''
    Get the display name or instance id for the provided interface.

    name: The interface display name.
    as_instance_id: Return the interface as an instance id.

    Returns a string containg the interface display name or instance id.

    CLI Example:

    .. code-block:: bash

        salt '*' win_msloop.get_interface name

        salt '*' win_msloop.get_interface 'loop1' as_instance_id=True
    '''
    ret = str()
    interfaces = _list_interfaces(name, as_instance_id)

    if interfaces:
        if len(interfaces) > 1:
            _LOG.error(('Found multiple matching interfaces, but only expected one: %s'),
                       interfaces)
        else:
            _LOG.debug('Found interface: %s', interfaces[0])
            ret = interfaces[0]
    return ret


def get_interfaces():
    '''
    Get the display names for all valid interfaces.

    Returns a list containg interface display names.

    CLI Example:

    .. code-block:: bash

        salt '*' win_msloop.get_interfaces
    '''

    return _list_interfaces()


def get_interface_setting(interface, address_family, *args):
    '''
    Determine the value of the setting for the provided interface.

    interface: The interface display name.
    address_family: The internet address family (ipv4, ipv6).
    args: The names of the interface settings. A list of valid setting names
          can be found at https://goo.gl/49taoW

    Returns a dictionary of the setting names and values.

    CLI Example:

    .. code-block:: bash

        salt '*' win_msloop.get_interface_setting interface address_family setting_name

        salt '*' win_msloop.get_interface_setting 'loop1' 'ipv4' 'NlMtu' 'WeakHostSend'
    '''
    ret = dict()
    address_family_int = _get_address_family_as_int(address_family)

    if not args:
        _LOG.warning('No settings provided.')
        return ret

    with salt.utils.winapi.Com():
        try:
            connection = wmi.WMI(namespace='StandardCimv2')
            settings = connection.MSFT_NetIPInterface(AddressFamily=address_family_int,
                                                      InterfaceAlias=interface)[0]
            for arg in args:
                ret[arg] = str(getattr(settings, arg))
        except wmi.x_wmi as error:
            _LOG.error('Encountered WMI error: %s', error.com_error)
        except (AttributeError, IndexError) as error:
            _LOG.error('Error getting MSFT_NetIPInterface: %s', error)
    return ret


def set_interface_setting(interface, address_family, **kwargs):
    '''
    Manage the value of the setting for the provided interface.

    interface: The interface display name.
    address_family: The internet address family (ipv4, ipv6).
    kwargs: The setting names and their desired values. A list of valid setting names
            can be found at https://goo.gl/49taoW

    Returns a boolean representing whether all settings succeeded.

    CLI Example:

    .. code-block:: bash

        salt '*' win_msloop.set_interface_setting interface address_family setting_name=value

        salt '*' win_msloop.set_interface_setting 'loop1' 'ipv4' 'WeakHostReceive'='1'
    '''
    kwargs = salt.utils.clean_kwargs(**kwargs)
    address_family_int = _get_address_family_as_int(address_family)
    failed_settings = dict()

    if not kwargs:
        _LOG.warning('No settings provided.')
        return False

    current_settings = get_interface_setting(interface, address_family, *kwargs.keys())

    if kwargs == current_settings:
        _LOG.debug('Settings already contain the provided values.')
        return True

    # Note that we must fetch all properties of MSFT_NetIPInterface below, since
    # filtering for specific properties and then attempting to set them will cause
    # an error like: wmi.x_wmi Unexpected COM Error -2147352567
    with salt.utils.winapi.Com():
        try:
            connection = wmi.WMI(namespace='StandardCimv2')
            settings = connection.MSFT_NetIPInterface(AddressFamily=address_family_int,
                                                      InterfaceAlias=interface)[0]
        except wmi.x_wmi as error:
            _LOG.error('Encountered WMI error: %s', error.com_error)
        except (AttributeError, IndexError) as error:
            _LOG.error('Error getting MSFT_NetIPInterface: %s', error)

        for key in kwargs:
            if str(kwargs[key]) != str(current_settings[key]):
                try:
                    setattr(settings, key, kwargs[key])
                except wmi.x_wmi as error:
                    _LOG.error('Encountered WMI error: %s', error.com_error)
                except AttributeError as error:
                    _LOG.error('Error setting %s: %s', key, error)

    # Get the settings post-change so that we can verify that all properties
    # were modified successfully. Track the ones that weren't.
    new_settings = get_interface_setting(interface, address_family, *kwargs.keys())

    for key in kwargs:
        if str(kwargs[key]) != str(new_settings[key]):
            failed_settings[key] = kwargs[key]

    if failed_settings:
        _LOG.error('Failed to change settings: %s', failed_settings)
    else:
        _LOG.debug('Settings changed successfully: %s', kwargs.keys())
        return True
    return False


def rename_interface(current_name, name):
    '''
    Change the display name of the interface specified.

    current_name: The current interface display name.
    name: The new interface display name.

    Returns a boolean representing whether the change succeeded.

    CLI Example:

    .. code-block:: bash

        salt '*' win_msloop.rename_interface current_name name

        salt '*' win_msloop.rename_interface 'oldname0' 'loop0'
    '''
    _interface_name_is_valid(name)

    interfaces = get_interfaces()

    if name in interfaces:
        if current_name in interfaces:
            _LOG.error(("Interface '%s' cannot be renamed, '%s' already present."),
                       current_name, name)
        else:
            _LOG.debug('Interface already present: %s', name)
            return True
    elif current_name in interfaces:
        wql = ('Select * from Win32_NetworkAdapter where NetConnectionID'
               "='{}'").format(current_name)

        with salt.utils.winapi.Com():
            connection = wmi.WMI()
            wmi_ret = connection.query(wql)

            try:
                wmi_ret[0].NetConnectionID = name
            except wmi.x_wmi as error:
                _LOG.error('Encountered WMI error: %s', error.com_error)
                return False
            except (AttributeError, IndexError) as error:
                _LOG.error('Error getting NetConnectionID: %s', error)
                return False

        interface = get_interface(name)
        if interface:
            _LOG.debug("Interface renamed from '%s' to '%s'.", current_name, name)
            return True
        else:
            _LOG.error("Unable to rename interface '%s' to '%s'.", current_name, name)
    else:
        _LOG.error('Interface not present: %s', current_name)
    return False


def new_interface(name):
    '''
    Create an interface with the display name provided.

    name: The interface display name.

    Returns a boolean representing whether the creation succeeded.

    CLI Example:

    .. code-block:: bash

        salt '*' win_msloop.new_interface name

        salt '*' win_msloop.new_interface 'loop0'
    '''
    netloop_path = os.path.join(os.environ['SystemRoot'], 'inf', 'Netloop.inf')

    _interface_name_is_valid(name)

    # Double-quotes inside double-quotes is necessary when dealing with situations where
    # spaces may be in both the path and the parameter names/values. See: http://goo.gl/9Xx1XR
    command = 'cmd.exe /C ""devcon.exe" install "{}" *MSLOOP"'.format(netloop_path)

    # Devcon creates interfaces with a default/randomized name, so we need to take
    # stock of the existing names, then rename the newest interface after we create it.
    current_interfaces = get_interfaces()

    if name in current_interfaces:
        _LOG.debug('Interface already present: %s', name)
        return True
    else:
        cmd_ret = __salt__['cmd.run_all'](command, python_shell=True)

        if cmd_ret['retcode'] == 0:
            # Wait for a few seconds, since interface creation will periodically fail
            # to immediately register the existence of the new interface.
            time.sleep(10)

            # Get the interfaces that now exist after having run the install command,
            # and find only the interfaces that did not already exist.
            new_interfaces = get_interfaces()
            interfaces = list(set(new_interfaces) - set(current_interfaces))

            if interfaces:
                _LOG.debug('New interfaces: %s', interfaces)

                if len(interfaces) > 1:
                    _LOG.error(('Unable to rename interface. Found multiple new interfaces,'
                                ' but only expected one.'))
                else:
                    _LOG.debug('Default interface name is: %s', interfaces[0])
                    return rename_interface(interfaces[0], name)
            else:
                _LOG.error('No new interfaces found.')
        else:
            _LOG.error('Unable to execute command: %s', command)
    return False


def delete_interface(name):
    '''
    Remove an interface with the display name provided.

    name: The interface display name.

    Returns a boolean representing whether the deletion succeeded.

    CLI Example:

    .. code-block:: bash

        salt '*' win_msloop.delete_interface name

        salt '*' win_msloop.delete_interface 'loop0'
    '''
    interface = get_interface(name, as_instance_id=True)

    if interface:
        command = 'cmd.exe /C ""devcon.exe" remove @{}"'.format(interface)
        cmd_ret = __salt__['cmd.run_all'](command, python_shell=True)

        if cmd_ret['retcode'] == 0:
            if not get_interface(name):
                _LOG.debug('Interface has been removed: %s', name)
                return True
        else:
            _LOG.error('Unable to execute command: %s', command)
    else:
        _LOG.debug('Interface already absent: %s', name)
        return True
    return False
