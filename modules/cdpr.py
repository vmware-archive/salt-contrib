# -*- coding: utf-8 -*-
'''
This is a module which exposes the cdpr tool to salt, and returns
 the contents of cdpr's response.

Copyright 2014 eBay Software Foundation
 by Brandon Matthews <bramatthews@ebay.com> (thenewwazoo@github)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

'''

import logging

import salt.utils

from salt.exceptions import (
    CommandExecutionError,
    MinionError,
    SaltInvocationError,
    TimedProcTimeoutError
)

log = logging.getLogger(__name__)


def __virtual__():
    '''
    Only load the module if cdpr is installed
    '''
    cmd = 'cdpr'
    if salt.utils.which(cmd):
        return 'cdpr'
    return False


def _parse_output(cdpr_out):
    '''
    cdpr's output looks like:
        $ sudo cdpr -d eth0
        cdpr - Cisco Discovery Protocol Reporter
        Version 2.2.1
        Copyright (c) 2002-2006 - MonkeyMental.com

        Using Device: eth0
        Waiting for CDP advertisement:
        (default config is to transmit CDP packets every 60 seconds)
        Device ID
          value:  core1.example.com
        Addresses
          value:  10.1.1.2
        Port ID
          value:  GigabitEthernet8/26
        $
    '''

    outlines = cdpr_out.splitlines()
    ret = {}
    # I hope this isn't too brittle
    ret['device_id'] = outlines[-5].split()[-1:]
    ret['addresses'] = outlines[-3].split()[-1:]
    ret['port_id'] = outlines[-1].split()[-1:]
    return ret


# TODO verbosity not yet supported because we can't parse it yet
# def listen(device=None, timeout=61, verbosity=None):
def listen(device=None, timeout=61):
    '''
    Runs the CDPR tool, and returns its output in a dict, or
     raises an error.

    CLI Example:

    .. code-block: bash

        salt '*' cdpr.listen eth0 120
    '''

    if device is None or device == "":
        device = 'any'

    cmd = 'cdpr -d {0}'.format(device)
    cmd += ' -t {0}'.format(timeout)

#   if verbosity is not None:
#       cmd += ' -{0}'.format('v'*verbosity)

    try:
        out = __salt__['cmd.run_all'](cmd)
        if 'SIOCGIFHWADDR' in out['stdout']:
            err = out['stdout'].splitlines()[-1]
            raise SaltInvocationError(err)
        elif 'Aborting due to timeout' in out['stdout']:
            raise TimedProcTimeoutError('cdpr aborted due to timeout')
        elif out['retcode'] != 0:
            raise CommandExecutionError(out)

#       if verbosity is not None:
#           ret = _parse_verbose_output(out['stdout'])
        ret = _parse_output(out['stdout'])

    except CommandExecutionError as ce:
        raise ce

    return ret
