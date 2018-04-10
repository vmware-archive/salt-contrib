# -*- coding: utf-8 -*-
'''
Module for managing Octopus Deploy Tentacle service settings on Windows servers.

:platform:      Windows

'''

# Import python libs
from __future__ import absolute_import
from distutils.version import LooseVersion  # pylint: disable=import-error,no-name-in-module
import ast
import json
import logging
import os
import platform
import re

# Import salt libs
from salt.exceptions import SaltException, SaltInvocationError
from salt._compat import ElementTree
import salt.utils

_COMMS_STYLES = {'TentacleActive': True, 'TentaclePassive': False}
_DEFAULT_COMMS = 'TentaclePassive'
_DEFAULT_INSTANCE = 'Tentacle'
_HKEY = 'HKLM'
_LOG = logging.getLogger(__name__)

# Define the module's virtual name
__virtualname__ = 'octopus_tentacle'


def __virtual__():
    '''
    Only works on Windows systems.
    '''
    if salt.utils.is_windows():
        return __virtualname__
    return False


def _get_exe_path():
    '''
    Determine the Tentacle executable path.
    '''
    return os.path.join(_get_install_path(), 'Tentacle.exe')


def _get_install_path():
    '''
    Determine the installation path from the relevant registry value.
    '''
    base_key = r'SOFTWARE\Octopus\Tentacle'
    vname = 'InstallLocation'

    value = (__salt__['reg.read_value'](_HKEY, base_key, vname))
    if value.get('vdata', None):
        return value['vdata']

    message = r"Value data for '{0}' not found in {1}\{2}.".format(vname, _HKEY, base_key)
    raise SaltException(message)


def _get_version():
    '''
    Determine the version of the Tentacle executable.
    '''
    cmd = [_get_exe_path(), 'help', '--console']
    cmd_ret = __salt__['cmd.run_all'](cmd)

    if cmd_ret['retcode'] != 0:
        _LOG.error('Unable to execute command: %s\nError: %s', cmd, cmd_ret['stderr'])
        return None

    help_text = [x.rstrip() for x in cmd_ret['stdout'].splitlines() if x.strip()]
    match = re.search(r'version\s+(?P<version>[\d\.]+)\b', help_text[0])

    if match:
        _LOG.debug('Version found: %s', match.group('version'))
        return match.group('version')
    _LOG.error('Unable to parse line: %s', help_text[0])
    return None


def _parse_config(tree):
    '''
    Parse the ElementTree object. Tentacle config elements are formatted as follows:

    .. code-block:: xml

        <set key="KeyName">Value</set>
    '''
    ret = dict()
    booleans = (False, True)

    for child in tree:
        if 'key' in child.attrib:
            try:
                # Some values are Json data.
                value = json.loads(child.text)
            except ValueError:
                # If the value can be an integer or boolean, then make it so.
                try:
                    value = int(child.text)
                except ValueError:
                    text_capitalized = child.text.capitalize()
                    if text_capitalized in booleans:
                        try:
                            value = ast.literal_eval(text_capitalized)
                        except AttributeError:
                            pass
                    else:
                        value = child.text
            ret[child.attrib['key']] = value

    return ret


def _validate_comms(comms):
    '''
    Validate the communications style provided.
    '''
    if comms not in get_comms_styles():
        message = ("Invalid communications style '{0}' specified. Valid comms:"
                   ' {1}').format(comms, get_comms_styles())
        raise SaltInvocationError(message)


def version_is_3_or_newer():
    '''
    Determine if the Tentacle executable version is 3.0 or newer.

    :return: A boolean indicating if the executable version is 3.0 or newer.
    :rtype: bool

    CLI Example:

    .. code-block:: bash

        salt '*' octopus_tentacle.version_is_3_or_newer
    '''
    version = str(_get_version())
    if LooseVersion(version) >= LooseVersion('3.0'):
        return True
    return False


def get_comms_styles():
    '''
    Determine the available communication styles.

    :return: A list of the communication styles.
    :rtype: list

    CLI Example:

    .. code-block:: bash

        salt '*' octopus_tentacle.get_comms_styles
    '''
    return _COMMS_STYLES.keys()


def get_config_path(instance=_DEFAULT_INSTANCE):
    '''
    Determine the configuration file used for the provided instance.

    :param str instance: The name of the Tentacle instance.

    :return: A string containing the configuration file path.
    :rtype: str

    CLI Example:

    .. code-block:: bash

        salt '*' octopus_tentacle.get_config_path instance='Tentacle'
    '''
    ret = str()
    instance_key = r'SOFTWARE\Octopus\Tentacle\{0}'.format(instance)

    value = (__salt__['reg.read_value'](_HKEY, instance_key, 'ConfigurationFilePath'))

    if value.get('vdata', None):
        ret = value['vdata']
    else:
        _LOG.warn('Unable to get configuration path for instance: %s', instance)

    return ret


def set_config_path(path=r'C:\Octopus\Tentacle\Tentacle.config', instance=_DEFAULT_INSTANCE):
    '''
    Manage the configuration file for the provided instance.

    :param str path: The path to the configuration file.
    :param str instance: The name of the Tentacle instance.

    :return: A boolean representing whether the change succeeded.
    :rtype: bool

    CLI Example:

    .. code-block:: bash

        salt '*' octopus_tentacle.set_config path='C:\\Octopus\\Tentacle.config' instance='Tentacle'
    '''
    current_path = get_config_path(instance)

    if (path == current_path) and os.path.isfile(path):
        _LOG.debug("Config file already present: %s", path)
        return True

    cmd = [_get_exe_path(), 'create-instance', '--instance', instance, '--config', path]
    cmd.append('--console')

    cmd_ret = __salt__['cmd.run_all'](cmd)

    if cmd_ret['retcode'] == 0:
        _LOG.debug('Config file created successfully: %s', path)
        return True
    _LOG.error('Unable to execute command: %s\nError: %s', cmd, cmd_ret['stderr'])
    return False


def get_config(instance=_DEFAULT_INSTANCE):
    '''
    Determine the configuration of the provided instance.

    :param str instance: The name of the Tentacle instance.

    :return: A dictionary containing the configuration data.
    :rtype: dict

    CLI Example:

    .. code-block:: bash

        salt '*' octopus_tentacle.get_config instance='Tentacle'
    '''
    ret = dict()
    name_mapping = {'Octopus.Home': 'home_path',
                    'Octopus.Communications.Squid': 'squid',
                    'Tentacle.CertificateThumbprint': 'thumbprint',
                    'Tentacle.Communication.TrustedOctopusServers': 'servers',
                    'Tentacle.Deployment.ApplicationDirectory': 'app_path',
                    'Tentacle.Services.NoListen': 'comms',
                    'Tentacle.Services.PortNumber': 'port'}

    config_path = get_config_path(instance)

    if not os.path.isfile(config_path):
        _LOG.error('Unable to get configuration file for instance: %s', instance)
        return ret

    with salt.utils.fopen(config_path, 'r') as fh_:
        config = _parse_config(ElementTree.fromstring(fh_.read()))

    for item in config:
        # Skip keys that we aren't specifically looking for.
        if item in name_mapping:
            # Convert the NoListen value to a friendly value.
            if name_mapping[item] == 'comms':
                for comms_style in _COMMS_STYLES:
                    if config[item] == _COMMS_STYLES[comms_style]:
                        ret[name_mapping[item]] = comms_style
                        break
            else:
                ret[name_mapping[item]] = config[item]

    return ret


def set_config(home_path=r'C:\Octopus', app_path=r'C:\Octopus\Applications', port=10933,
               comms=_DEFAULT_COMMS, generate_cert=True, generate_squid=True,
               instance=_DEFAULT_INSTANCE):
    '''
    Manage the application configuration of the provided instance.

    :param str home_path: The path that will serve as the Tentacle home.
    :param str app_path: The directory for the installation of application packages.
    :param int port: The TCP port for the instance.
    :param str comms: The communication style for the instance. Valid values can be found by
    running octopus_tentacle.get_comms_styles.
    :param bool generate_cert: Whether to generate a certificate.
    :param bool generate_squid: Whether to generate a SQUID.
    :param str instance: The name of the Tentacle instance.

    :return: A boolean representing whether the change succeeded.
    :rtype: bool

    CLI Example:

    .. code-block:: bash

        salt '*' octopus_tentacle.set_app home_path='C:\\Octopus' app_path='C:\\Apps' port=10933
    '''
    kwarg_names = ['home_path', 'app_path', 'port']
    version = version_is_3_or_newer()

    # The noListen parameter is only used with version 3.0 or newer.
    if version:
        kwarg_names.append('comms')

    config = dict([(name, locals()[name]) for name in kwarg_names])

    _validate_comms(comms)

    current_config_full = get_config(instance)
    current_config = dict()

    if current_config_full:
        current_config = dict([(name, current_config_full[name]) for name in kwarg_names])
    else:
        if not get_config_path():
            _LOG.error('Unable to get configuration path for instance: %s', instance)
            return False

    # If required, generate a certificate if one is not already present.
    if generate_cert:
        if not set_cert(instance=instance):
            _LOG.error('Unable to generate certificate successfully for instance: %s', instance)
            return False

    # If required, generate a SQUID if one is not already present.
    if generate_squid:
        if not set_squid(instance=instance):
            _LOG.error('Unable to generate SQUID successfully for instance: %s', instance)
            return False

    if config == current_config:
        _LOG.debug('Config already contains the provided values.')
        return True

    cmd = [_get_exe_path(), 'configure', '--instance', instance, '--home', home_path]
    cmd.extend(['--app', app_path, '--port', port])

    if version:
        cmd.extend(['--noListen', str(_COMMS_STYLES[comms])])

    cmd.append('--console')
    cmd_ret = __salt__['cmd.run_all'](cmd)

    if cmd_ret['retcode'] == 0:
        _LOG.debug('Configured instance successfully: %s', instance)
        return True
    _LOG.error('Unable to execute command: %s\nError: %s', cmd, cmd_ret['stderr'])
    return False


def set_cert(force=False, instance=_DEFAULT_INSTANCE):
    '''
    Generate a tentacle certificate for the provided instance.

    :param bool force: Whether to generate a certificate even if one already exists.
    :param str instance: The name of the Tentacle instance.

    :return: A boolean representing whether the change succeeded.
    :rtype: bool

    CLI Example:

    .. code-block:: bash

        salt '*' octopus_tentacle.set_cert force='False' instance='Tentacle'
    '''
    current_config = get_config(instance)

    if 'thumbprint' in current_config and not force:
        _LOG.debug('Certificate already exists for instance: %s', instance)
        return True

    cmd = [_get_exe_path(), 'new-certificate', '--instance', instance]

    if 'thumbprint' not in current_config or not force:
        cmd.append('--if-blank')
    cmd.append('--console')

    cmd_ret = __salt__['cmd.run_all'](cmd)

    if cmd_ret['retcode'] == 0:
        _LOG.debug('Configured certificate successfully for instance: %s', instance)
        return True
    _LOG.error('Unable to execute command: %s\nError: %s', cmd, cmd_ret['stderr'])
    return False


def set_squid(instance=_DEFAULT_INSTANCE):
    '''
    Manage the SQUID of the provided instance.

    :return: A boolean representing whether the change succeeded.
    :rtype: bool

    CLI Example:

    .. code-block:: bash

        salt '*' octopus_tentacle.set_squid instance='Tentacle'
    '''
    if version_is_3_or_newer():
        _LOG.debug('SQUID not required for version 3.0 or later.')
        return True

    current_config = get_config(instance)

    if 'squid' in current_config and current_config['squid']:
        _LOG.debug('Config already contains SQUID: %s', current_config['squid'])
        return True

    cmd = [_get_exe_path(), 'new-squid', '--instance', instance, '--console']
    cmd_ret = __salt__['cmd.run_all'](cmd)

    if cmd_ret['retcode'] == 0:
        _LOG.debug('Configured SQUID successfully for instance: %s', instance)
        return True
    _LOG.error('Unable to execute command: %s\nError: %s', cmd, cmd_ret['stderr'])
    return False


def set_trust(thumbprint, reset=False, instance=_DEFAULT_INSTANCE):
    '''
    Manage the server thumbprint trust of the provided instance.

    :param str thumbprint: The thumbprint of the Octopus Deploy server.
    :param bool reset: Whether to reset the trust relationship if the thumbprint is not already trusted.
    :param str instance: The name of the Tentacle instance.

    :return: A boolean representing whether the change succeeded.
    :rtype: bool

    CLI Example:

    .. code-block:: bash

        salt '*' octopus_tentacle.set_trust thumbprint='AAA000' reset='False' instance='Tentacle'
    '''
    current_config = get_config(instance)

    if 'servers' in current_config and current_config['servers']:
        for server in current_config['servers']:
            if thumbprint == server['Thumbprint']:
                _LOG.debug('Config already contains server thumbprint: %s', thumbprint)
                return True
    else:
        # If there are no current trusts, then we should flag to run reset-trust anyway.
        reset = True

    cmd_ret = dict()

    # If reset has been passed in or if this is the first trust defined
    # for this instance then reset-trust should be performed.
    if reset:
        cmd = [_get_exe_path(), 'configure', '--instance', instance, '--reset-trust', '--console']
        cmd_ret = __salt__['cmd.run_all'](cmd)

        if cmd_ret['retcode'] != 0:
            _LOG.error('Unable to execute command: %s\nError: %s', cmd, cmd_ret['stderr'])
            return False

    cmd = [_get_exe_path(), 'configure', '--instance', instance, '--trust', thumbprint, '--console']

    cmd_ret = __salt__['cmd.run_all'](cmd)

    if cmd_ret['retcode'] == 0:
        _LOG.debug('Config changed to include server thumbprint: %s', thumbprint)
        return True
    _LOG.error('Unable to execute command: %s\nError: %s', cmd, cmd_ret['stderr'])
    return False


def get_registration(server, api_key):
    '''
    Determine the registration of the machine.

    :param str server: The URI of the Octopus Deploy server.
    :param str api_key: The API key for registration of the Tentacle.

    :return: A dictionary containing the configuration data.
    :rtype: dict

    CLI Example:

    .. code-block:: bash

        salt '*' octopus_tentacle.get_registration server='http://srvr' api_key='API-000'
    '''
    ret = dict()
    # We use the client DLL here instead of a salt.utils.http query because
    # we don't have a way of getting the unique machine ID, and /machines/all
    # would require checking potentially hundreds of entries.
    dll_path = os.path.join(_get_install_path(), 'Octopus.Client.dll')

    # Expressions will always collapse 0-1 length arrays, so we need to assign the
    # environments after the Select-Object has been performed so that the value is
    # a consistent type.
    cmd = ["Add-Type -Path '{0}'; $Endpoint =".format(dll_path)]
    cmd.append(" New-Object Octopus.Client.OctopusServerEndpoint '{0}', '{1}';".format(server, api_key))
    cmd.append(' $Repo = New-Object Octopus.Client.OctopusRepository $Endpoint;')
    cmd.append(' $Envs = @($Repo.Environments.FindAll() | Select-Object Id, Name)')
    cmd.append(r' | Foreach { @{ $_.Id = $_.Name } };')
    cmd.append(' $Machine = $Repo.Machines.FindByName($Env:ComputerName) | Select-Object')
    cmd.append(r" Roles, EnvironmentIds, @{ Name='Environments'; Expression={ @() } },")
    cmd.append(r" @{ Name='CommunicationStyle'; Expression={ ")
    cmd.append(' $_.EndPoint.CommunicationStyle.ToString() }};')
    cmd.append(r' if ($Machine) { $Machine.Environments = @($Machine.EnvironmentIds')
    cmd.append(r' | Foreach { $Envs[$_] }) };')
    cmd.append(" ConvertTo-Json -Compress -Depth 4 -InputObject @($Machine)")

    cmd_ret = __salt__['cmd.run_all'](str().join(cmd), shell='powershell', python_shell=True)

    if cmd_ret['retcode'] != 0:
        _LOG.error('Unable to execute command: %s\nError: %s', cmd, cmd_ret['stderr'])
        return ret

    try:
        items = json.loads(cmd_ret['stdout'], strict=False)
    except ValueError:
        _LOG.error('Unable to parse return data as Json.')

    # FindByName returns $Null if the name is not found.
    if len(items) == 1 and not items[0]:
        _LOG.debug("Machine registration not found.")
        return ret

    for item in items:
        ret = {
            'envs': list(),
            'roles': list(),
        }

        ret['envs'].extend(item['Environments'])
        ret['roles'].extend(item['Roles'])

    if not ret:
        _LOG.warning('No valid data found in output: %s', cmd_ret['stdout'])

    if 'envs' in ret:
        ret['envs'] = sorted(ret['envs'])
    if 'roles' in ret:
        ret['roles'] = sorted(ret['roles'])

    return ret


def set_registration(server, envs, roles, api_key, user=None, password=None, port=10943,
                     comms=_DEFAULT_COMMS, instance=_DEFAULT_INSTANCE):
    '''
    Manage the registration of the Tentacle with the Octopus Deploy server.

    :param str server: The URI of the Octopus Deploy server.
    :param str envs: The environments for the Tentacle.
    :param str roles: The roles defined for the Tentacle.
    :param str api_key: The API key for registration of the Tentacle.
    :param str user: The server username.
    :param str password: The server password.
    :param int port: The TCP communications port for the server.
    :param str comms: The communication style for the instance. Valid values can be found by
    running octopus_tentacle.get_comms_styles.
    :param str instance: The name of the Tentacle instance.

    .. note:

        The api_key parameter is required for the purpose of determining the current
        registration status, even when the user and password parameters are configured.

    :return: A boolean representing whether the change succeeded.
    :rtype: bool

    CLI Example:

    .. code-block:: bash

        salt '*' octopus_tentacle.registration server='http://srvr' envs="['Dev']" roles="['Web']" api_key='API-000'
    '''
    kwarg_names = ('envs', 'roles')
    registration = dict([(name, sorted(locals()[name])) for name in kwarg_names])

    current_registration = get_registration(server, api_key)

    if registration == current_registration:
        _LOG.debug('Registration already present for server: %s', server)
        return True

    _validate_comms(comms)
    exe_path = _get_exe_path()

    cmd = [exe_path, 'register-with', '--instance', instance, '--server', server]
    cmd.extend(['--comms-style', comms])

    if comms == 'TentaclePassive':
        cmd.extend(['--apiKey', api_key])
    else:
        if not user:
            raise SaltInvocationError('Value of user must be specified for comms: {0}'.format(comms))
        cmd.extend(['--name', platform.node()])
        cmd.extend(['--username', user, '--password', password, '--server-comms-port', port])

    for role in roles:
        cmd.extend(['--role', role])
    for env in envs:
        cmd.extend(['--environment', env])

    cmd.extend(['--force', '--console'])

    cmd_ret = __salt__['cmd.run_all'](cmd)

    if cmd_ret['retcode'] != 0:
        _LOG.error('Unable to execute command: %s\nError: %s', cmd, cmd_ret['stderr'])
        return False

    cmd = [exe_path, 'service', '--instance', instance, '--install', '--start']

    cmd_ret = __salt__['cmd.run_all'](cmd)

    if cmd_ret['retcode'] == 0:
        _LOG.debug('Registration successful for server: %s', server)
        return True
    _LOG.error('Unable to execute command: %s\nError: %s', cmd, cmd_ret['stderr'])
    return False


def set_deregistration(server, api_key, user=None, password=None, instance=_DEFAULT_INSTANCE):
    '''
    Revoke registration of the Tentacle with the Octopus Deploy server.

    :param str server: The URI of the Octopus Deploy server.
    :param str api_key: The API key for registration of the Tentacle.
    :param str user: The server username.
    :param str password: The server password.
    :param str instance: The name of the Tentacle instance.

    .. note:

        The api_key parameter is required for the purpose of determining the current
        registration status, even when the user and password parameters are configured.

    :return: A boolean representing whether the change succeeded.
    :rtype: bool

    CLI Example:

    .. code-block:: bash

    salt '*' octopus_tentacle.set_deregistration server='http://srvr' api-key='API-000' instance='default'

    '''
    current_registration = get_registration(server, api_key)

    if 'envs' not in current_registration or not current_registration['envs']:
        _LOG.debug('Registration already revoked for server: %s', server)
        return True

    cmd = [_get_exe_path(), 'deregister-from', '--instance', instance, '--server', server]

    if user:
        cmd.extend(['--username', user, '--password', password])
    else:
        cmd.extend(['--apiKey', api_key])

    cmd.append('--console')

    cmd_ret = __salt__['cmd.run_all'](cmd)

    if cmd_ret['retcode'] == 0:
        _LOG.debug('Registration revoked for server: %s', server)
        return True
    _LOG.error('Unable to execute command: %s\nError: %s', cmd, cmd_ret['stderr'])
    return False
