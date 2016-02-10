# -*- coding: utf-8 -*-
'''
_states.nuget
~~~~~~~~~~~~~~~~~
Description
    Manage Microsoft NuGet package installation on Windows servers.
'''
# Import python libs
import os

def __virtual__():
    '''
    Load only on minions that have the nuget module.
    '''
    if 'nuget.install' in __salt__:
        return True
    return False

def installed(name, version, target, sources, exclude_version=False):
    '''
    Ensure the specified package exists.
    '''
    ret = {'name': name,
           'changes': {},
           'comment': str(),
           'result': None}
    dir_name = name

    if not exclude_version:
        dir_name = '{}.{}'.format(dir_name, version)

    package_path = os.path.join(target, dir_name)

    if os.path.isdir(package_path):
        ret['comment'] = 'Package directory {} already present.'.format(dir_name)
        ret['result'] = True
    elif __opts__['test']:
        ret['comment'] = 'Package directory {} will be installed.'.format(dir_name)
        ret['changes'] = {'old': None,
                          'new': dir_name}
    else:
        kwargs = {'exclude_version': exclude_version}

        ret['comment'] = 'Installed package directory {}.'.format(dir_name)
        ret['changes'] = {'old': None,
                          'new': dir_name}
        ret['result'] = __salt__['nuget.install'](name, version, target, *sources, **kwargs)
    return ret

