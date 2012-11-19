# -*- coding: utf-8 -*-

'''
RabbitMQ plugins module
'''

import logging
import re

from salt import exceptions, utils

log = logging.getLogger(__name__)

def __virtual__():
    '''
    Verify RabbitMQ is installed.
    '''
    name = 'rabbitmq_plugins'
    try:
        utils.check_or_die('rabbitmq-plugins')
    except exceptions.CommandNotFoundError:
        name = False
    return name

def _convert_env(env):
    output = {}
    for var in env.split():
        k, v = var.split('=')
        output[k] = v
    return output

def _rabbitmq_plugins(command, runas=None, env=()):
    cmdline = 'rabbitmq-plugins {command}'.format(command=command)
    ret = __salt__['cmd.run_all'](
        cmdline,
        runas=runas,
        env=_convert_env(env)
    )
    if ret['retcode'] == 0:
        return ret['stdout']
    else:
        return False

def list(runas=None, env=()):
    '''
    Return list of plugins: name, state and version
    '''
    regex = re.compile(
        r'^\[(?P<state>[a-zA-Z ])\] (?P<name>[^ ]+) +(?P<version>[^ ]+)$')
    plugins = {}
    res = __salt__['cmd.run']('rabbitmq-plugins list', runas=runas,
                              env=_convert_env(env))
    for line in res.splitlines():
        match = regex.match(line)
        if match:
            plugins[match.group('name')] = {
                'version': match.group('version'),
                'state': match.group('state'),
                }
        else:
            log.warning("line '%s' is invalid", line)
    return plugins

def enable(name, runas=None, env=()):
    '''
    Turn on a rabbitmq plugin
    '''
    return _rabbitmq_plugins('enable %s' % name, runas=runas, env=env)

def disable(name, runas=None, env=()):
    '''
    Turn off a rabbitmq plugin
    '''
    return _rabbitmq_plugins('disable %s' % name, runas=runas, env=env)
