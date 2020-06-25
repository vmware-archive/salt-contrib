# -*- coding: utf-8 -*-
from __future__ import absolute_import

import salt.utils
import salt.modules.puppet
import salt.modules.cmdmod

import logging
import json
from salt.ext import six

log = logging.getLogger(__name__)

__salt__ = {
    'cmd.run': salt.modules.cmdmod._run_quiet,
    'cmd.run_all': salt.modules.cmdmod._run_all_quiet
}


def _check_facter():
    '''
    Checks if facter is installed.
    '''
    salt.utils.path.check_or_die('facter')


def facter():
    '''
    Return facter facts as grains.
    '''
    _check_facter()

    grains = {}
    try:
        # -p: load puppet libraries, for puppet specific facts
        # -j: return json data
        output = __salt__['cmd.run']('facter -p -j')
        try:
            facts = json.loads(output)
        except (KeyError, ValueError):
            log.critical('Failed to load json facter data')
            return {}
        for key, value in six.iteritems(facts):
            # Prefix fact names with 'facter_', so it doesn't
            # conflict with existing or future grain names.
            grain = 'facter_{0}'.format(key)
            grains[grain] = value
        return grains
    except OSError:
        log.critical('Failed to run facter')
        return {}
    return {}
