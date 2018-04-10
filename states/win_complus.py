# -*- coding: utf-8 -*-
'''
_states.win_complus
~~~~~~~~~~~~~~~~~
Description
    Manage Microsoft Component Services.
'''


def __virtual__():
    '''
    Load only on minions that have the win_complus module.
    '''
    if 'win_complus.list_apps' in __salt__:
        return True
    return False


def test(name):
    ret = {'name': name,
           'changes': {},
           'comment': str(),
           'result': None}
    return ret


def present(name, description='', accesscheck=True, accesslevel='ApplicationLevel', authentication='Default', impersonationlevel='Anonymous', identity=None, password=None):
    '''
    Ensure the specified application exists.

    .. note:

        This function only validates against the application name, and will return True even
        if the site already exists with a different configuration. It will not modify
        the configuration of an existing site. #TODO: complete configuration check

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

    Example of usage with only the required arguments.

    .. code-block:: yaml

        App0-present:
            win_complus.present:
                - name: App0

    Example of usage specifying all available arguments:

    .. code-block:: yaml

        App0-present:
            win_complus.present:
                - name: App0
                - description: some information
                - accesscheck: True
                - accesslevel: ApplicationLevel
                - authentication: Default
                - impersonationlevel: Identify
                - identity: user
                - password: secret

    '''
    ret = {'name': name,
           'changes': {},
           'comment': str(),
           'result': None}

    current_apps = __salt__['win_complus.list_apps']()

    if name in current_apps:
        ret['comment'] = 'Application already present: {0}'.format(name)
        ret['result'] = True
    elif __opts__['test']:
        ret['comment'] = 'Application will be created: {0}'.format(name)
        ret['changes'] = {'old': None,
                          'new': name}
    else:
        ret['comment'] = 'Created Application: {0}'.format(name)
        ret['changes'] = {'old': None,
                          'new': name}
        ret['result'] = __salt__['win_complus.create_app'](name, description, accesscheck, accesslevel,
                                                           authentication, impersonationlevel,
                                                           identity, password)
    return ret


def absent(name):
    '''
    Ensure the specified Application does not exist.

    name: The Application display name.
    '''
    ret = {'name': name,
           'changes': {},
           'comment': str(),
           'result': None}
    current_apps = __salt__['win_complus.list_apps']()

    if name not in current_apps:
        ret['comment'] = 'Application has already been removed: {0}'.format(name)
        ret['result'] = True
    elif __opts__['test']:
        ret['comment'] = 'Application will be removed: {0}'.format(name)
        ret['changes'] = {'old': name,
                          'new': None}
    else:
        ret['comment'] = 'Removed application: {0}'.format(name)
        ret['changes'] = {'old': name,
                          'new': None}
        ret['result'] = __salt__['win_complus.remove_app'](name)
    return ret
