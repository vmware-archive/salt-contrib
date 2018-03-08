# -*- coding: utf-8 -*-
'''
Module for managing Octopus Deploy Tentacle service settings on Windows servers.

:platform:      Windows

'''

# Import python libs
from __future__ import absolute_import

_DEFAULT_COMMS = 'TentaclePassive'
_DEFAULT_INSTANCE = 'Tentacle'

# Define the module's virtual name
__virtualname__ = 'octopus_tentacle'


def __virtual__():
    '''
    Load only on minions that have the octopus_tentacle module.
    '''
    if 'octopus_tentacle.get_config' in __salt__:
        return __virtualname__
    return False


def config_path(name, path=r'C:\Octopus\Tentacle\Tentacle.config', instance=_DEFAULT_INSTANCE):
    '''
    Manage the configuration file for the provided instance.

    :param str path: The path to the configuration file.
    :param str instance: The name of the Tentacle instance.

    Example of usage:

    .. code-block:: yaml

        tentacle-config-path:
            octopus_tentacle.config_path:
                - path: C:\\Octopus\\Tentacle\\Tentacle.config

    '''
    ret = {'name': name,
           'changes': dict(),
           'comment': str(),
           'result': None}
    current_path = __salt__['octopus_tentacle.get_config_path'](instance)

    if path == current_path:
        ret['comment'] = 'Config file already present: {0}'.format(path)
        ret['result'] = True
    elif __opts__['test']:
        ret['comment'] = 'Config file will be created: {0}'.format(path)
        ret['changes'] = {'old': current_path,
                          'new': path}
    else:
        ret['changes'] = {'old': current_path,
                          'new': path}
        ret['result'] = __salt__['octopus_tentacle.set_config_path'](path, instance)

        if ret['result']:
            ret['comment'] = 'Config file created successfully: {0}'.format(path)
        else:
            ret['comment'] = 'Config file failed to be created: {0}'.format(path)
    return ret


def configured(name, home_path=r'C:\Octopus', app_path=r'C:\Octopus\Applications', port=10933,
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

    Example of usage:

    .. code-block:: yaml

        tentacle-configured:
            octopus_tentacle.configured:
                - home_path: C:\\Octopus
                - app_path: C:\\Octopus\\Applications
                - port: 10933
                - comms: TentaclePassive
                - generate_cert: True
                - generate_squid: True
    '''
    ret = {'name': name,
           'changes': dict(),
           'comment': str(),
           'result': None}

    kwarg_names = ['home_path', 'app_path', 'port']

    # The noListen parameter is only used with version 3.0 or newer.
    if __salt__['octopus_tentacle.version_is_3_or_newer']():
        kwarg_names.append('comms')

    config = dict([(name, locals()[name]) for name in kwarg_names])

    current_config_full = __salt__['octopus_tentacle.get_config'](instance)
    current_config = dict()

    if current_config_full:
        current_config = dict([(name, current_config_full[name]) for name in kwarg_names])

    if config == current_config:
        ret['comment'] = 'Config already contains provided values.'
        ret['result'] = True
    elif __opts__['test']:
        ret['comment'] = 'Config will be changed to include provided values.'
        ret['changes'] = {'old': current_config,
                          'new': config}
    else:
        ret['changes'] = {'old': current_config,
                          'new': config}
        ret['result'] = __salt__['octopus_tentacle.set_config'](home_path, app_path, port, comms,
                                                                generate_cert, generate_squid,
                                                                instance)
        if ret['result']:
            ret['comment'] = 'Config changed to include provided values.'
        else:
            ret['comment'] = 'Config failed to include provided values.'
    return ret


def trusted(name, thumbprint, reset=False, instance=_DEFAULT_INSTANCE):
    '''
    Manage the server thumbprint trust of the provided instance.

    :param str thumbprint: The thumbprint of the Octopus Deploy server.
    :param bool reset: Whether to reset the trust relationship if the thumbprint is not already trusted.
    :param str instance: The name of the Tentacle instance.

    Example of usage:

    .. code-block:: yaml

        tentacle-trusted:
            octopus_tentacle.trusted:
                - thumbprint: 9988776655443322111000AAABBBCCCDDDEEEFFF
                - reset: False
    '''
    ret = {'name': name,
           'changes': dict(),
           'comment': str(),
           'result': None}

    thumbprint_present = False
    current_config = __salt__['octopus_tentacle.get_config'](instance)

    if 'servers' in current_config:
        for server in current_config['servers']:
            if thumbprint == server['Thumbprint']:
                thumbprint_present = True

    if thumbprint_present:
        ret['comment'] = 'Config already contains server thumbprint: {0}'.format(thumbprint)
        ret['result'] = True
    elif __opts__['test']:
        ret['comment'] = 'Config will be changed to include the server thumbprint: {0}'.format(thumbprint)
        ret['changes'] = {'old': None,
                          'new': thumbprint}
    else:
        ret['changes'] = {'old': None,
                          'new': thumbprint}
        ret['result'] = __salt__['octopus_tentacle.set_trust'](thumbprint, reset, instance)

        if ret['result']:
            ret['comment'] = 'Config changed to include server thumbprint: {0}'.format(thumbprint)
        else:
            ret['comment'] = 'Config failed to include server thumbprint: {0}'.format(thumbprint)
    return ret


def registered(name, server, envs, roles, api_key, user=None, password=None, port=10943,
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

    Example of usage with only the required arguments:

    .. code-block:: yaml

        tentacle-registered:
            octopus_tentacle.registered:
                - server: http://server:8080
                - envs:
                    - Dev
                - roles:
                    - Web
                - api_key: API-AAAAABBBBBCCCCCDDDDDEEEEFFFF

    Example of usage specifying the user and password parameters for a polling Tentacle:

    .. code-block:: yaml

        tentacle-registered:
            octopus_tentacle.registered:
                - server: http://server:8080
                - envs:
                    - Dev
                - roles:
                    - Web
                - api_key: API-AAAAABBBBBCCCCCDDDDDEEEEFFFF
                - user: TestUser
                - password: TestPassword
                - port: 10943
                - comms: TentacleActive
    '''
    ret = {'name': name,
           'changes': dict(),
           'comment': str(),
           'result': None}
    kwarg_names = ('envs', 'roles')
    registration = dict([(name, sorted(locals()[name])) for name in kwarg_names])

    current_registration = __salt__['octopus_tentacle.get_registration'](server, api_key)

    if registration == current_registration:
        ret['comment'] = 'Registration already present for server: {0}'.format(server)
        ret['result'] = True
    elif __opts__['test']:
        ret['comment'] = 'Registration will be created for server: {0}'.format(server)
        ret['changes'] = {'old': None,
                          'new': server}
    else:
        ret['changes'] = {'old': None,
                          'new': server}
        ret['result'] = __salt__['octopus_tentacle.set_registration'](server, envs, roles,
                                                                      api_key, user, password,
                                                                      port, comms, instance)
        if ret['result']:
            ret['comment'] = 'Registration successful for server: {0}'.format(server)
        else:
            ret['comment'] = 'Registration failed for server: {0}'.format(server)

    return ret


def deregistered(name, server, api_key, user=None, password=None, instance=_DEFAULT_INSTANCE):
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

     Example of usage with only the required arguments:

    .. code-block:: yaml

        tentacle-deregistered:
            octopus_tentacle.deregistered:
                - server: http://server:8080
                - api_key: API-AAAAABBBBBCCCCCDDDDDEEEEFFFF

    Example of usage specifying the user and password parameters for a polling Tentacle:

    .. code-block:: yaml

        tentacle-deregistered:
            octopus_tentacle.deregistered:
                - server: http://server:8080
                - api_key: API-AAAAABBBBBCCCCCDDDDDEEEEFFFF
                - user: TestUser
                - password: TestPassword
    '''
    ret = {'name': name,
           'changes': dict(),
           'comment': str(),
           'result': None}

    current_registration = __salt__['octopus_tentacle.get_registration'](server, api_key)

    if 'envs' not in current_registration or not current_registration['envs']:
        ret['comment'] = 'Registration already revoked for server: {0}'.format(server)
        ret['result'] = True
    elif __opts__['test']:
        ret['comment'] = 'Registration will be revoked for server:{0}'.format(server)
        ret['changes'] = {'old': server,
                          'new': None}
    else:
        ret['changes'] = {'old': server,
                          'new': None}
        ret['result'] = __salt__['octopus_tentacle.set_registration'](server, api_key,
                                                                      user, password,
                                                                      instance)
        if ret['result']:
            ret['comment'] = 'Registration revoked for server: {0}'.format(server)
        else:
            ret['comment'] = 'Registration failed to revoke for server: {0}'.format(server)

    return ret
