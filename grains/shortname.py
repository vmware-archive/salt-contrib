# -*- coding: utf-8 -*-
'''
    :codeauthor: Nick Soracco
    :copyright: © 2015 by Nick Soracco
    :license: BSD

    salt.grains.shortname
    ~~~~~~~~~~~~~~~~~~~~~~~

    Returns a string of the shortname of the machine, courtesy of
    os.uname()[1].split('.')[0]

    FIXME: Only works in Linux, requires uname() system call.
'''
from __future__ import absolute_import

import os


def shortname():
    '''
    Return the first characters of a nodename prior to the first period.
    '''
    return {'shortname': os.uname()[1].split('.')[0]}
