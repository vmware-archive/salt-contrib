# -*- coding: utf-8 -*-
'''
Java Property file Renderer for Salt
http://aphor.github.io/jproperties_salt_renderer/
'''

from __future__ import absolute_import
from salt.ext import six

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
    parser. Uses the jproperties package https://pypi.python.org/pypi/jproperties so please
    "pip install jproperties" to use this renderer.

    Returns a flat dictionary by default:
      {'some.java.thing': 'whatever'}
    If using a 'shebang' "#!jproperties" header on the first line, an argument can be optionally
    supplied as a key to contain a dictionary of the rendered properties (ie. "#!jproperties foo"):
      {'foo': {'some.java.thing': 'whatever'}}

    :rtype: A Python data structure
    '''
    if not isinstance(jp_data, string_types):
        jp_data = jp_data.read()

    container = False
    if jp_data.startswith('#!'):
        args = jp_data[:jp_data.find('\n')].split()
        if len(args) >= 2:
            container = args[1]
        jp_data = jp_data[(jp_data.find('\n') + 1):]
    if not jp_data.strip():
        return {}
    properties = jp()
    properties.load(jp_data)
    if container:
        return {container: dict([(k, properties[k]) for k in six.iterkeys(properties)])}
    else:
        return dict([(k, properties[k]) for k in six.iterkeys(properties)])
