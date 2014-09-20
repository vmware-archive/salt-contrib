# -*- coding: utf-8 -*-
'''
Look up data from other pillar values or by executing a module function.

Usage:

Generally, this module should be configured as the final ext_pillar, if other
ext_pillars are used.

A pillar value matching the pattern ${...} will trigger this module to perform
a lookup. A lookup may be a pillar value (e.g., ${other_value}) or a call to
an execution module (${cmd.run('echo "foo"')}). Note that module functions are
executed on the master. Nested functions are supported, as is the passing of
a pillar value to a function. E.g.: ${cmd.run(command)}

'''

# O Import python libs
import inspect
import logging
import ast
import re

# Import salt libs
import salt.utils

__virtualname__ = 'lookup'


def __virtual__():
    return __virtualname__


# Set up logging
log = logging.getLogger(__name__)


def ext_pillar(minion_id, pillar, *args, **kwargs):
    def process(o):
        if isinstance(o, ast.Call):
            f = '{0}.{1}'.format(o.func.value.id, o.func.attr)
            args = [process(a) for a in o.args]
            kwargs = dict((k.arg, process(k.value))
                          for k in o.keywords)
            func = __salt__[f]
            spec = inspect.getargspec(func)
            if ('pillar' in spec.args or
                    spec.keywords is not None):
                kwargs['pillar'] = pillar
            if ('minion_id' in spec.args or
                    spec.keywords is not None):
                kwargs['minion_id'] = minion_id
            return func(*args, **kwargs)
        elif isinstance(o, ast.Name):
            return salt.utils.traverse_dict_and_list(pillar, o.id, 'x', ':')
        elif isinstance(o, ast.Expr):
            return process(o.value)
        else:
            return ast.literal_eval(o)

    def walk(data):
        def process_val(k, v):
            if isinstance(v, dict) or isinstance(v, list):
                walk(v)
            elif isinstance(v, str) or isinstance(v, unicode):
                m = re.search('^\$\{(.*)\}$', v)
                if m:
                    s = m.groups()[0]
                    data[k] = process(ast.parse(s).body[0].value)

        if isinstance(data, dict):
            for k, v in data.iteritems():
                process_val(k, v)
        elif isinstance(data, list):
            i = 0
            for v in data:
                process_val(i, v)
                i = i+1

    walk(pillar)
