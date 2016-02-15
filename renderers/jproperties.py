# -*- coding: utf-8 -*-
'''
Java Property file Renderer for Salt
http://aphor.github.io/jproperties_salt_renderer/
'''

from __future__ import absolute_import

# Import 3rd party libs
try:
    from jproperties import Properties as jp
    HAS_LIBS = True
except ImportError:
    HAS_LIBS = False

# Import salt libs
from salt.ext.six import string_types


def render(jp_data, saltenv='base', sls='', **kws):
    '''
    Accepts Java Properties as a string or as a file object and runs it through the jproperties
    parser.

    :rtype: A Python data structure
    '''
    if not isinstance(jp_data, string_types):
        jp_data = jp_data.read()

    if jp_data.startswith('#!'):
        container = jp_data[:jp_data.find('\n')].split()[1]
        jp_data = jp_data[(jp_data.find('\n') + 1):]
    else:
        container = False
    if not jp_data.strip():
        return {}
    properties = jp()
    properties.load(jp_data)
    if container:
      return {container: dict([(k,properties[k]) for k in properties.iterkeys()])}
    else:
      return dict([(k,properties[k]) for k in properties.iterkeys()])
