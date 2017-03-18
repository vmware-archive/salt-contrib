# -*- coding: utf-8 -*-
'''
_modules.win_smtp_server
~~~~~~~~~~~~~~~~~
Description
    Manage IIS SMTP server on Windows servers.
Dependencies
    Windows features:
        SMTP-Server, Web-WMI
References
    IIS metabase configuration settings:
        https://goo.gl/XCt1uO
    IIS logging options:
        https://goo.gl/RL8ki9
        https://goo.gl/iwnDow
    MicrosoftIISv2 namespace in Windows 2008r2 and later:
        http://goo.gl/O4m48T
    Connection and relay IPs in PowerShell:
        https://goo.gl/aBMZ9K
        http://goo.gl/MrybFq
'''
# For reference purposes, a typical relay ip list looks like this:
#   ['24.0.0.128', '32.0.0.128', '60.0.0.128', '68.0.0.128', '1.0.0.0', '76.0.0.0',
#    '0.0.0.0', '0.0.0.0', '1.0.0.0', '1.0.0.0', '2.0.0.0', '2.0.0.0', '4.0.0.0',
#    '0.0.0.0', '76.0.0.128', '0.0.0.0', '0.0.0.0', '0.0.0.0', '0.0.0.0',
#    '255.255.255.255', '0.0.0.0']

# Import python libs
from __future__ import absolute_import
import logging
import re
# Import salt libs
from salt.exceptions import SaltInvocationError
import salt.utils

try:
    import wmi
    import salt.utils.winapi
    _HAS_MODULE_DEPENDENCIES = True
except ImportError:
    _HAS_MODULE_DEPENDENCIES = False

_DEFAULT_SERVER = 'SmtpSvc/1'
_WMI_NAMESPACE = 'MicrosoftIISv2'
_LOG = logging.getLogger(__name__)

# Define the module's virtual name
__virtualname__ = 'win_smtp_server'

def __virtual__():
    '''
    Only works on Windows systems with SMTP and IIS6 WMI support installed
    '''
    def _wmi_class_available():
        '''
        Determine if SMTP + Web-WMI are installed.
        '''
        with salt.utils.winapi.Com():
            try:
                connection = wmi.WMI(namespace=_WMI_NAMESPACE)
                connection.IIsSmtpServerSetting()
                return True
            except wmi.x_wmi as error:
                _LOG.debug('Encountered WMI error: %s', error.com_error)
            except (AttributeError, IndexError) as error:
                _LOG.debug('Error getting IIsSmtpServerSetting: %s', error)
        return False

    if salt.utils.is_windows():
        if _HAS_MODULE_DEPENDENCIES and _wmi_class_available():
            return __virtualname__
        else:
            _LOG.debug(('Unable to find IIsSmtpServerSetting. Please ensure that the'
                        ' SMTP-Server and Web-WMI features are installed.'))
    return False

def _get_wmi_setting(wmi_class_name, setting, server):
    '''
    Get the value of the setting for the provided class.
    '''
    with salt.utils.winapi.Com():
        try:
            connection = wmi.WMI(namespace=_WMI_NAMESPACE)
            wmi_class = getattr(connection, wmi_class_name)

            settings = wmi_class([setting], Name=server)[0]
            ret = getattr(settings, setting)
        except wmi.x_wmi as error:
            _LOG.error('Encountered WMI error: %s', error.com_error)
        except (AttributeError, IndexError) as error:
            _LOG.error('Error getting %s: %s', wmi_class_name, error)
    return ret

def _set_wmi_setting(wmi_class_name, setting, value, server):
    '''
    Set the value of the setting for the provided class.
    '''
    with salt.utils.winapi.Com():
        try:
            connection = wmi.WMI(namespace=_WMI_NAMESPACE)
            wmi_class = getattr(connection, wmi_class_name)

            settings = wmi_class(Name=server)[0]
        except wmi.x_wmi as error:
            _LOG.error('Encountered WMI error: %s', error.com_error)
        except (AttributeError, IndexError) as error:
            _LOG.error('Error getting %s: %s', wmi_class_name, error)

        try:
            setattr(settings, setting, value)
            return True
        except wmi.x_wmi as error:
            _LOG.error('Encountered WMI error: %s', error.com_error)
        except AttributeError as error:
            _LOG.error('Error setting %s: %s', setting, error)
    return False

def _normalize_connection_ips(*args):
    '''
    Fix connection address formatting.

    Consolidate extra spaces and convert to a standard string.
    '''
    ret = list()
    reg_separator = r',\s*'

    for arg in args:
        if not re.search(reg_separator, arg):
            message = ("Connection IP '{}' is not in a valid format. Address should"
                       " be formatted like: 'ip_address, subnet'").format(arg)
            raise SaltInvocationError(message)

        ip_address, subnet = re.split(reg_separator, arg)
        ret.append('{}, {}'.format(ip_address, subnet))
    return ret

def normalize_server_settings(**kwargs):
    '''
    Convert setting values that has been improperly converted to a dict back to a string.

    kwargs: The setting names and their values.

    Returns a dictionary of the setting names and their normalized values.

    CLI Example:

    .. code-block:: bash

        salt '*' win_smtp_server.normalize_server_settings first_setting=value second_setting=value
    '''
    ret = dict()
    kwargs = salt.utils.clean_kwargs(**kwargs)

    for key in kwargs:
        if isinstance(kwargs[key], dict):
            _LOG.debug('Fixing value: %s', kwargs[key])
            ret[key] = "{{{}}}".format(kwargs[key].iterkeys().next())
        else:
            _LOG.debug('No fix necessary for value: %s', kwargs[key])
            ret[key] = kwargs[key]
    return ret

def get_log_format_types():
    '''
    Get the log format names and ids.

    Returns a dictionary of the log format names and ids.

    CLI Example:

    .. code-block:: bash

        salt '*' win_smtp_server.get_log_format_types
    '''
    ret = dict()
    prefix = 'logging/'

    with salt.utils.winapi.Com():
        try:
            connection = wmi.WMI(namespace=_WMI_NAMESPACE)
            settings = connection.IISLogModuleSetting()

            # Remove the prefix from the name.
            for setting in settings:
                name = str(setting.Name).replace(prefix, '', 1)
                ret[name] = str(setting.LogModuleId)
        except wmi.x_wmi as error:
            _LOG.error('Encountered WMI error: %s', error.com_error)
        except (AttributeError, IndexError) as error:
            _LOG.error('Error getting IISLogModuleSetting: %s', error)

    if not ret:
        _LOG.error('Unable to get log format types.')
    return ret

def get_servers():
    '''
    Get the SMTP virtual server names.

    Returns a list of the SMTP virtual servers.

    CLI Example:

    .. code-block:: bash

        salt '*' win_smtp_server.get_servers
    '''
    ret = list()

    with salt.utils.winapi.Com():
        try:
            connection = wmi.WMI(namespace=_WMI_NAMESPACE)
            settings = connection.IIsSmtpServerSetting()

            for server in settings:
                ret.append(str(server.Name))
        except wmi.x_wmi as error:
            _LOG.error('Encountered WMI error: %s', error.com_error)
        except (AttributeError, IndexError) as error:
            _LOG.error('Error getting IIsSmtpServerSetting: %s', error)

    _LOG.debug('Found SMTP servers: %s', ret)
    return ret

def get_server_setting(*args, **kwargs):
    '''
    Get the value of the setting for the SMTP virtual server.

    args: The setting names.
    server: The SMTP server name.

    Returns a dictionary of the provided settings and their values.

    CLI Example:

    .. code-block:: bash

        salt '*' win_smtp_server.get_server_setting setting_name

        salt '*' win_smtp_server.get_server_setting 'MaxRecipients'
    '''
    ret = dict()
    server = kwargs.pop('server', _DEFAULT_SERVER)

    if not args:
        _LOG.warning('No settings provided.')
        return ret

    with salt.utils.winapi.Com():
        try:
            connection = wmi.WMI(namespace=_WMI_NAMESPACE)
            settings = connection.IIsSmtpServerSetting(args, Name=server)[0]

            for arg in args:
                ret[arg] = str(getattr(settings, arg))
        except wmi.x_wmi as error:
            _LOG.error('Encountered WMI error: %s', error.com_error)
        except (AttributeError, IndexError) as error:
            _LOG.error('Error getting IIsSmtpServerSetting: %s', error)
    return ret

def set_server_setting(**kwargs):
    '''
    Set the value of the setting for the SMTP virtual server.
    Please note that setting names are case-sensitive.

    kwargs: The setting names and their values.
    server: The SMTP server name.

    Returns a boolean representing whether all changes succeeded.

    CLI Example:

    .. code-block:: bash

        salt '*' win_smtp_server.set_server_setting setting_name=setting_value

        salt '*' win_smtp_server.set_server_setting 'MaxRecipients'='5000'
    '''
    kwargs = salt.utils.clean_kwargs(**kwargs)
    server = kwargs.pop('server', _DEFAULT_SERVER)

    if not kwargs:
        _LOG.warning('No settings provided')
        return False

    # Some fields are formatted like '{data}'. Salt tries to convert these to dicts
    # automatically on input, so convert them back to the proper format.
    kwargs = normalize_server_settings(**kwargs)

    current_settings = get_server_setting(*kwargs.keys(), **{'server': server})

    if kwargs == current_settings:
        _LOG.debug('Settings already contain the provided values.')
        return True

    # Note that we must fetch all properties of IIsSmtpServerSetting below, since
    # filtering for specific properties and then attempting to set them will cause
    # an error like: wmi.x_wmi Unexpected COM Error -2147352567
    with salt.utils.winapi.Com():
        try:
            connection = wmi.WMI(namespace=_WMI_NAMESPACE)
            settings = connection.IIsSmtpServerSetting(Name=server)[0]
        except wmi.x_wmi as error:
            _LOG.error('Encountered WMI error: %s', error.com_error)
        except (AttributeError, IndexError) as error:
            _LOG.error('Error getting IIsSmtpServerSetting: %s', error)

        for key in kwargs:
            if str(kwargs[key]) != str(current_settings[key]):
                try:
                    setattr(settings, key, kwargs[key])
                except wmi.x_wmi as error:
                    _LOG.error('Encountered WMI error: %s', error.com_error)
                except AttributeError as error:
                    _LOG.error('Error setting %s: %s', key, error)

    # Get the settings post-change so that we can verify tht all properties
    # were modified successfully. Track the ones that weren't.
    new_settings = get_server_setting(*kwargs.keys(), **{'server': server})
    failed_settings = dict()

    for key in kwargs:
        if str(kwargs[key]) != str(new_settings[key]):
            failed_settings[key] = kwargs[key]
    if failed_settings:
        _LOG.error('Failed to change settings: %s', failed_settings)
        return False

    _LOG.debug('Settings configured successfully: %s', kwargs.keys())
    return True

def get_log_format(server=_DEFAULT_SERVER):
    '''
    Get the active log format for the SMTP virtual server.

    server: The SMTP server name.

    Returns a string of the log format name.

    CLI Example:

    .. code-block:: bash

        salt '*' win_smtp_server.get_log_format
    '''
    log_format_types = get_log_format_types()
    format_id = _get_wmi_setting('IIsSmtpServerSetting', 'LogPluginClsid', server)

    # Since IIsSmtpServerSetting stores the log type as an id, we need
    # to get the mapping from IISLogModuleSetting and extract the name.
    for key in log_format_types:
        if str(format_id) == log_format_types[key]:
            return key
    _LOG.warning('Unable to determine log format.')
    return None

def set_log_format(log_format, server=_DEFAULT_SERVER):
    '''
    Set the active log format for the SMTP virtual server.

    log_format: The log format name.
    server: The SMTP server name.

    Returns a boolean representing whether the change succeeded.

    CLI Example:

    .. code-block:: bash

        salt '*' win_smtp_server.set_log_format log_format

        salt '*' win_smtp_server.set_log_format 'Microsoft IIS Log File Format'
    '''
    setting = 'LogPluginClsid'
    log_format_types = get_log_format_types()
    format_id = log_format_types.get(log_format, None)

    if not format_id:
        message = ("Invalid log format '{}' specified. Valid formats:"
                   ' {}').format(log_format, log_format_types.keys())
        raise SaltInvocationError(message)

    _LOG.debug("Id for '%s' found: %s", log_format, format_id)

    current_log_format = get_log_format(server)

    if log_format == current_log_format:
        _LOG.debug('%s already contains the provided format.', setting)
        return True

    _set_wmi_setting('IIsSmtpServerSetting', setting, format_id, server)

    new_log_format = get_log_format(server)
    ret = log_format == new_log_format

    if ret:
        _LOG.debug("Setting %s configured successfully: %s", setting, log_format)
    else:
        _LOG.error("Unable to configure %s with value: %s", setting, log_format)
    return ret

def get_connection_ip_list(server=_DEFAULT_SERVER):
    '''
    Get the IPGrant list for the SMTP virtual server.

    server: The SMTP server name.

    Returns a list of the IP and subnet pairs.

    CLI Example:

    .. code-block:: bash

        salt '*' win_smtp_server.get_connection_ip_list
    '''
    ret = list()
    setting = 'IPGrant'

    lines = _get_wmi_setting('IIsIPSecuritySetting', setting, server)

    # WMI returns the addresses as a tuple of unicode strings, each representing
    # an address/subnet pair. Remove extra spaces that may be present.
    ret = _normalize_connection_ips(*lines)

    if not ret:
        _LOG.debug('%s is empty.', setting)
    return ret

def set_connection_ip_list(*args, **kwargs):
    '''
    Set the IPGrant list for the SMTP virtual server.

    args: The connect IP + subnet pairs.
    grant_by_default: Whether the args should be a blacklist or whitelist.
    server: The SMTP server name.

    Returns a boolean representing whether the change succeeded.

    CLI Example:

    .. code-block:: bash

        salt '*' win_smtp_server.set_connection_ip_list 'ip_address, netmask'

        salt '*' win_smtp_server.set_connection_ip_list '127.0.0.1, 255.255.255.255'
    '''
    setting = 'IPGrant'
    server = kwargs.pop('server', _DEFAULT_SERVER)
    grant_by_default = kwargs.pop('grant_by_default', False)

    # It's okay to accept an empty list for set_connection_ip_list,
    # since an empty list may be desirable.
    if not args:
        _LOG.debug('Empty %s specified.', setting)

    # Remove any extra spaces that may be present.
    addresses = _normalize_connection_ips(*args)

    current_addresses = get_connection_ip_list(server)

    # Order is not important, so compare to the current addresses as unordered sets.
    if set(addresses) == set(current_addresses):
        _LOG.debug('%s already contains the provided addresses.', setting)
        return True

    # First we should check GrantByDefault, and change it if necessary.
    current_grant_by_default = _get_wmi_setting('IIsIPSecuritySetting', 'GrantByDefault', server)

    if grant_by_default != current_grant_by_default:
        _LOG.debug('Setting GrantByDefault to: %s', grant_by_default)
        _set_wmi_setting('IIsIPSecuritySetting', 'GrantByDefault', grant_by_default, server)

    _set_wmi_setting('IIsIPSecuritySetting', setting, addresses, server)

    new_addresses = get_connection_ip_list(server)
    ret = set(addresses) == set(new_addresses)

    if ret:
        _LOG.debug('%s configured successfully: %s', setting, args)
        return ret
    _LOG.error('Unable to configure %s with value: %s', setting, args)
    return ret

def get_relay_ip_list(server=_DEFAULT_SERVER):
    '''
    Get the RelayIpList list for the SMTP virtual server.

    server: The SMTP server name.

    Returns a list of the relay IPs.

    CLI Example:

    .. code-block:: bash

        salt '*' win_smtp_server.get_relay_ip_list
    '''
    ret = list()
    setting = 'RelayIpList'

    lines = _get_wmi_setting('IIsSmtpServerSetting', setting, server)

    if not lines:
        # None corresponds to "Only the list below" with an empty access list,
        # and an empty tuple corresponds to "All except the list below".
        _LOG.debug('%s is empty: %s', setting, lines)
        if lines is None:
            lines = [None]
        return list(lines)

    # WMI returns the addresses as a tuple of individual octets, so we
    # need to group them and reassemble them into IP addresses.
    i = 0
    while i < len(lines):
        octets = [str(x) for x in lines[i: i + 4]]
        address = '.'.join(octets)
        ret.append(address)
        i += 4
    return ret

def set_relay_ip_list(*args, **kwargs):
    '''
    Set the RelayIpList list for the SMTP virtual server.

    args: The relay IPs.
    server: The SMTP server name.

    Returns a boolean representing whether the change succeeded.

    CLI Example:

    .. code-block:: bash

        salt '*' win_smtp_server.set_relay_ip_list ip_address

        salt '*' win_smtp_server.set_relay_ip_list '192.168.1.1' '172.16.1.1'
    '''
    setting = 'RelayIpList'
    server = kwargs.pop('server', _DEFAULT_SERVER)
    formatted_addresses = list()

    current_addresses = get_relay_ip_list(server)

    if list(args) == current_addresses:
        _LOG.debug('%s already contains the provided addresses.', setting)
        return True

    # Setting None for RelayIpList corresponds to the restrictive
    # "Only the list below" setting with an empty access list configured,
    # and setting an empty list/tuple for RelayIpList corresponds to the
    # more permissive "All except the list below" setting.

    if args:
        # The WMI input data needs to be in the format used by RelayIpList. Order
        # is also important due to the way RelayIpList orders the address list.

        if args[0] is None:
            formatted_addresses = None
        else:
            for arg in args:
                for octet in arg.split('.'):
                    formatted_addresses.append(octet)

    _LOG.debug('Formatted %s addresses: %s', setting, formatted_addresses)

    _set_wmi_setting('IIsSmtpServerSetting', setting, formatted_addresses, server)

    new_addresses = get_relay_ip_list(server)

    ret = list(args) == new_addresses

    if ret:
        _LOG.debug('%s configured successfully: %s', setting, args)
        return ret
    _LOG.error('Unable to configure %s with value: %s', setting, args)
    return ret

