# -*- coding: utf-8 -*-
'''
    :codeauthor: Nick Soracco
    :copyright: © 2014 by Nick Soracco
    :license: BSD

    salt.grains.has_battery
    ~~~~~~~~~~~~~~~~~~~~~~~

    Returns a boolean indicating whether (or not) the system has a battery.

    FIXME: Only works in Linux, requires the acpi binary, which CentOS doesn't ship.
    FIXME: See: http://sourceforge.net/projects/acpiclient/
'''

from __future__ import absolute_import

import logging               # Need this for logging
import salt.log              # need this for logging
import salt.utils            # Need this for which()
import salt.modules.cmdmod   # Process execution helper

# Configure logger
log = logging.getLogger(__name__)


def has_battery():
    '''
    Return true if a battery exists.
    '''

    # We need to have the `acpi` binary installed to avoid having to do the
    # old vs new acpi detection our selves.
    acpi = salt.utils.which('acpi')
    if acpi is None or acpi == "":
        return {}

    # call ACPI binary: `acpi -b` to return the battery status.  As long as the
    # binary exists, it will return either the status of all batteries it knows
    # about in the following format:
    # 'Battery X: Full, YY%' or 'No support for device type: power_supply'
    # In the former, we return True, the latter we return False. I hope it's
    # obvious why. ;)
    result = salt.modules.cmdmod._run_quiet('acpi -b')
    if 'No support for device type' in result:
        return {'has_battery': 0}
    elif 'Battery ' in result:
        return {'has_battery': 1}
    else:
        log.warn('Unexpected output from `acpi -b`: {0}'.format(result))
        return {}
