# -*- coding: utf-8 -*-
'''
_states.win_msloop
~~~~~~~~~~~~~~~~~
Description
    Manage Microsoft Loopback Adapters on Windows servers.
'''


def __virtual__():
    '''
    Load only on minions that have the win_msloop module.
    '''
    if 'win_msloop.get_interface_setting' in __salt__:
        return True
    return False


def present(name):
    '''
    Ensure the specified interface exists.

    name: The interface display name.
    '''
    ret = {'name': name,
           'changes': {},
           'comment': str(),
           'result': None}
    current_name = __salt__['win_msloop.get_interface'](name)

    if str(name) == str(current_name):
        ret['comment'] = 'Interface "{}" already present.'.format(name)
        ret['result'] = True
    elif __opts__['test']:
        ret['comment'] = 'Interface "{}" will be created.'.format(name)
        ret['changes'] = {'old': current_name,
                          'new': name}
    else:
        ret['comment'] = 'Created interface "{}".'.format(name)
        ret['changes'] = {'old': current_name,
                          'new': name}
        ret['result'] = __salt__['win_msloop.new_interface'](name)
    return ret


def absent(name):
    '''
    Ensure the specified interface does not exist.

    name: The interface display name.
    '''
    ret = {'name': name,
           'changes': {},
           'comment': str(),
           'result': None}
    current_name = __salt__['win_msloop.get_interface'](name)

    if str(name) != str(current_name):
        ret['comment'] = 'Interface "{}" already absent.'.format(name)
        ret['result'] = True
    elif __opts__['test']:
        ret['comment'] = 'Interface "{}" will be removed.'.format(name)
        ret['changes'] = {'old': current_name,
                          'new': name}
    else:
        ret['comment'] = 'Deleted interface "{}".'.format(name)
        ret['changes'] = {'old': current_name,
                          'new': name}
        ret['result'] = __salt__['win_msloop.delete_interface'](name)
    return ret


def interface_setting(name, interface, address_family, settings=None):
    '''
    Ensure the value is set for the specified property.

    name: The state name.
    interface: The interface display name.
    address_family: The internet address family (ipv4, ipv6).
    settings: The setting names and their desired values. A list of valid setting names
              can be found at https://goo.gl/49taoW
    '''
    ret = {'name': name,
           'changes': {},
           'comment': str(),
           'result': None}

    if not settings:
        ret['comment'] = 'No settings to change provided.'
        ret['result'] = True
        return ret

    ret_settings = dict()
    ret_settings['changes'] = {}
    ret_settings['failures'] = {}

    current_settings = __salt__['win_msloop.get_interface_setting'](interface,
                                                                    address_family,
                                                                    *settings.keys())
    for key in settings:
        if str(settings[key]) != str(current_settings[key]):
            ret_settings['changes'][key] = {'old': current_settings[key],
                                            'new': settings[key]}
    if not ret_settings['changes']:
        ret['comment'] = 'Settings already contain the provided values.'
        ret['result'] = True
        return ret
    elif __opts__['test']:
        ret['comment'] = 'Settings will be changed.'
        ret['changes'] = ret_settings
        return ret

    __salt__['win_msloop.set_interface_setting'](interface,
                                                 address_family,
                                                 **settings)
    new_settings = __salt__['win_msloop.get_interface_setting'](interface,
                                                                address_family,
                                                                *settings.keys())
    for key in settings:
        if str(new_settings[key]) != str(settings[key]):
            ret_settings['failures'][key] = {'old': current_settings[key],
                                             'new': new_settings[key]}
            ret_settings['changes'].pop(key, None)

    if ret_settings['failures']:
        ret['comment'] = 'Some settings failed to change.'
        ret['changes'] = ret_settings
        ret['result'] = False
    else:
        ret['comment'] = 'Set settings to contain the provided values.'
        ret['changes'] = ret_settings['changes']
        ret['result'] = True
    return ret
