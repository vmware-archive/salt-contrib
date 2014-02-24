# -*- coding: utf-8 -*-
'''
Backport of Evan Borgstrom's pyobjects renderer.

Available (with full docs) in develop branch of Salt at
https://github.com/saltstack/salt/blob/develop/salt/renderers/pyobjects.py

To use, copy this file to the _renderers directory within your file roots
(e.g., /srv/salt/_renderers/pybojects.py) and execute:
'''

# Original file:
# https://github.com/saltstack/salt/blob/develop/salt/utils/pyobjects.py
'''
:maintainer: Evan Borgstrom <evan@borgstrom.ca>

Pythonic object interface to creating state data, see the pyobjects renderer
for more documentation.
'''
from collections import namedtuple

from salt.utils.odict import OrderedDict

REQUISITES = ('require', 'watch', 'use', 'require_in', 'watch_in', 'use_in')


class StateException(Exception):
    pass


class DuplicateState(StateException):
    pass


class InvalidFunction(StateException):
    pass


class StateRegistry(object):
    '''
    The StateRegistry holds all of the states that have been created.
    '''
    def __init__(self):
        self.empty()

    def empty(self):
        self.states = OrderedDict()
        self.requisites = []
        self.includes = []
        self.extends = OrderedDict()

    def include(self, *args):
        self.includes += args

    def salt_data(self):
        states = OrderedDict([
            (id_, state())
            for id_, state in self.states.iteritems()
        ])

        if self.includes:
            states['include'] = self.includes

        if self.extends:
            states['extend'] = OrderedDict([
                (id_, state())
                for id_, state in self.extends.iteritems()
            ])

        self.empty()

        return states

    def add(self, id_, state, extend=False):
        if extend:
            attr = self.extends
        else:
            attr = self.states

        if id_ in attr:
            raise DuplicateState("A state with id '%s' already exists" % id_)

        # if we have requisites in our stack then add them to the state
        if len(self.requisites) > 0:
            for req in self.requisites:
                if req.requisite not in state.kwargs:
                    state.kwargs[req.requisite] = []
                state.kwargs[req.requisite].append(req())

        attr[id_] = state

    def extend(self, id_, state):
        self.add(id_, state, extend=True)

    def make_extend(self, name):
        return StateExtend(name)

    def push_requisite(self, requisite):
        self.requisites.append(requisite)

    def pop_requisite(self):
        del self.requisites[-1]


class StateExtend(object):
    def __init__(self, name):
        self.name = name


class StateRequisite(object):
    def __init__(self, requisite, module, id_, registry):
        self.requisite = requisite
        self.module = module
        self.id_ = id_
        self.registry = registry

    def __call__(self):
        return {self.module: self.id_}

    def __enter__(self):
        self.registry.push_requisite(self)

    def __exit__(self, type, value, traceback):
        self.registry.pop_requisite()


class StateFactory(object):
    '''
    The StateFactory is used to generate new States through a natural syntax

    It is used by initializing it with the name of the salt module::

        File = StateFactory("file")

    Any attribute accessed on the instance returned by StateFactory is a lambda
    that is a short cut for generating State objects::

        File.managed('/path/', owner='root', group='root')

    The kwargs are passed through to the State object
    '''
    def __init__(self, module, registry, valid_funcs=None):
        self.module = module
        self.registry = registry
        if valid_funcs is None:
            valid_funcs = []
        self.valid_funcs = valid_funcs

    def __getattr__(self, func):
        if len(self.valid_funcs) > 0 and func not in self.valid_funcs:
            raise InvalidFunction("The function '%s' does not exist in the "
                                  "StateFactory for '%s'" % (func, self.module))

        def make_state(id_, **kwargs):
            return State(
                id_,
                self.module,
                func,
                registry=self.registry,
                **kwargs
            )
        return make_state

    def __call__(self, id_, requisite='require'):
        '''
        When an object is called it is being used as a requisite
        '''
        # return the correct data structure for the requisite
        return StateRequisite(requisite, self.module, id_,
                              registry=self.registry)


class State(object):
    '''
    This represents a single item in the state tree

    The id_ is the id of the state, the func is the full name of the salt
    state (ie. file.managed). All the keyword args you pass in become the
    properties of your state.

    The registry is where the state should be stored. It is optional and will
    use the default registry if not specified.
    '''

    def __init__(self, id_, module, func, registry, **kwargs):
        self.id_ = id_
        self.module = module
        self.func = func
        self.kwargs = kwargs
        self.registry = registry

        if isinstance(self.id_, StateExtend):
            self.registry.extend(self.id_.name, self)
            self.id_ = self.id_.name
        else:
            self.registry.add(self.id_, self)

        self.requisite = StateRequisite('require', self.module, self.id_,
                                        registry=self.registry)

    @property
    def attrs(self):
        kwargs = self.kwargs

        # handle our requisites
        for attr in REQUISITES:
            if attr in kwargs:
                # our requisites should all be lists, but when you only have a
                # single item it's more convenient to provide it without
                # wrapping it in a list. transform them into a list
                if not isinstance(kwargs[attr], list):
                    kwargs[attr] = [kwargs[attr]]

                # rebuild the requisite list transforming any of the actual
                # StateRequisite objects into their representative dict
                kwargs[attr] = [
                    req() if isinstance(req, StateRequisite) else req
                    for req in kwargs[attr]
                ]

        # build our attrs from kwargs. we sort the kwargs by key so that we
        # have consistent ordering for tests
        return [
            {k: kwargs[k]}
            for k in sorted(kwargs.iterkeys())
        ]

    @property
    def full_func(self):
        return "%s.%s" % (self.module, self.func)

    def __str__(self):
        return "%s = %s:%s" % (self.id_, self.full_func, self.attrs)

    def __call__(self):
        return {
            self.full_func: self.attrs
        }

    def __enter__(self):
        self.registry.push_requisite(self.requisite)

    def __exit__(self, type, value, traceback):
        self.registry.pop_requisite()


class SaltObject(object):
    '''
    Object based interface to the functions in __salt__

    .. code-block:: python
       :linenos:
        Salt = SaltObject(__salt__)
        Salt.cmd.run(bar)
    '''
    def __init__(self, salt):
        _mods = {}
        for full_func in salt:
            mod, func = full_func.split('.')

            if mod not in _mods:
                _mods[mod] = {}
            _mods[mod][func] = salt[full_func]

        # now transform using namedtuples
        self.mods = {}
        for mod in _mods:
            mod_object = namedtuple('%sModule' % mod.capitalize(),
                                    _mods[mod].keys())

            self.mods[mod] = mod_object(**_mods[mod])

    def __getattr__(self, mod):
        if mod not in self.mods:
            raise AttributeError

        return self.mods[mod]


# Original file:
# https://github.com/saltstack/salt/blob/develop/salt/renderers/pyobjects.py
'''
Python renderer that includes a Pythonic Object based interface

:maintainer: Evan Borgstrom <evan@borgstrom.ca>

Let's take a look at how you use pyobjects in a state file. Here's a quick
example that ensures the ``/tmp`` directory is in the correct state.

.. code-block:: python
   :linenos:
    #!pyobjects

    File.managed("/tmp", user='root', group='root', mode='1777')

Nice and Pythonic!

By using the "shebang" syntax to switch to the pyobjects renderer we can now
write our state data using an object based interface that should feel at home
to python developers. You can import any module and do anything that you'd
like (with caution, importing sqlalchemy, django or other large frameworks has
not been tested yet). Using the pyobjects renderer is exactly the same as
using the built-in Python renderer with the exception that pyobjects provides
you with an object based interface for generating state data.

Creating state data
^^^^^^^^^^^^^^^^^^^
Pyobjects takes care of creating an object for each of the available states on
the minion. Each state is represented by an object that is the CamelCase
version of it's name (ie. ``File``, ``Service``, ``User``, etc), and these
objects expose all of their available state functions (ie. ``File.managed``,
``Service.running``, etc).

The name of the state is split based upon underscores (``_``), then each part
is capitalized and finally the parts are joined back together.

Some examples:

* ``postgres_user`` becomes ``PostgresUser``
* ``ssh_known_hosts`` becomes ``SshKnownHosts``

Context Managers and requisites
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
How about something a little more complex. Here we're going to get into the
core of what makes pyobjects the best way to write states.

.. code-block:: python
   :linenos:
    #!pyobjects

    with Pkg.installed("nginx"):
        Service.running("nginx", enable=True)

        with Service("nginx", "watch_in"):
            File.managed("/etc/nginx/conf.d/mysite.conf",
                         owner='root', group='root', mode='0444',
                         source='salt://nginx/mysite.conf')


The objects that are returned from each of the magic method calls are setup to
be used a Python context managers (``with``) and when you use them as such all
declarations made within the scope will **automatically** use the enclosing
state as a requisite!

The above could have also been written use direct requisite statements as.

.. code-block:: python
   :linenos:
    #!pyobjects

    Pkg.installed("nginx")
    Service.running("nginx", enable=True, require=Pkg("nginx"))
    File.managed("/etc/nginx/conf.d/mysite.conf",
                 owner='root', group='root', mode='0444',
                 source='salt://nginx/mysite.conf',
                 watch_in=Service("nginx"))

You can use the direct requisite statement for referencing states that are
generated outside of the current file.

.. code-block:: python
   :linenos:
    #!pyobjects

    # some-other-package is defined in some other state file
    Pkg.installed("nginx", require=Pkg("some-other-package"))

The last thing that direct requisites provide is the ability to select which
of the SaltStack requisites you want to use (require, require_in, watch,
watch_in, use & use_in) when using the requisite as a context manager.

.. code-block:: python
   :linenos:
    #!pyobjects

    with Service("my-service", "watch_in"):
        ...

The above example would cause all declarations inside the scope of the context
manager to automatically have their ``watch_in`` set to
``Service("my-service")``.

Including and Extending
^^^^^^^^^^^^^^^^^^^^^^^

To include other states use the ``include()`` function. It takes one name per
state to include.

To extend another state use the ``extend()`` function on the name when creating
a state.

.. code-block:: python
   :linenos:
    #!pyobjects

    include('http', 'ssh')

    Service.running(extend('apache'),
                    watch=[{'file': '/etc/httpd/extra/httpd-vhosts.conf'}])

Salt object
^^^^^^^^^^^
In the spirit of the object interface for creating state data pyobjects also
provides a simple object interface to the ``__salt__`` object.

A function named ``salt`` exists in scope for your sls files and will dispatch
its attributes to the ``__salt__`` dictionary.

The following lines are functionally equivalent:

.. code-block:: python
   :linenos:
    #!pyobjects

    ret = salt.cmd.run(bar)
    ret = __salt__['cmd.run'](bar)

Pillar, grain & mine data
^^^^^^^^^^^^^^^^^^^^^^^^^
Pyobjects provides shortcut functions for calling ``pillar.get``,
``grains.get`` & ``mine.get`` on the ``__salt__`` object. This helps maintain
the readability of your state files.

Each type of data can be access by a function of the same name: ``pillar()``,
``grains()`` and ``mine()``.

The following pairs of lines are functionally equivalent:

.. code-block:: python
   :linenos:
    #!pyobjects

    value = pillar('foo:bar:baz', 'qux')
    value = __salt__['pillar.get']('foo:bar:baz', 'qux')

    value = grains('pkg:apache')
    value = __salt__['grains.get']('pkg:apache')

    value = mine('os:Fedora', 'network.interfaces', 'grain')
    value = __salt__['mine.get']('os:Fedora', 'network.interfaces', 'grain')


TODO
^^^^
* Interface for working with reactor files
'''

import logging
import sys


log = logging.getLogger(__name__)


def render(template, saltenv='base', sls='',
           tmplpath=None, rendered_sls=None,
           _states=None, **kwargs):

    _globals = {}
    _locals = {}

    _registry = StateRegistry()
    if _states is None:
        try:
            _states = __states__
        except NameError:
            from salt.loader import states
            __opts__['grains'] = __grains__
            __opts__['pillar'] = __pillar__
            _states = states(__opts__, __salt__)

    # build our list of states and functions
    _st_funcs = {}
    for func in _states:
        (mod, func) = func.split(".")
        if mod not in _st_funcs:
            _st_funcs[mod] = []
        _st_funcs[mod].append(func)

    # create our StateFactory objects
    _st_globals = {'StateFactory': StateFactory, '_registry': _registry}
    for mod in _st_funcs:
        _st_locals = {}
        _st_funcs[mod].sort()
        mod_camel = ''.join([
            part.capitalize()
            for part in mod.split('_')
        ])
        mod_cmd = "%s = StateFactory('%s', registry=_registry, valid_funcs=['%s'])" % (
            mod_camel, mod,
            "','".join(_st_funcs[mod])
        )
        if sys.version > 3:
            exec(mod_cmd, _st_globals, _st_locals)
        else:
            exec mod_cmd in _st_globals, _st_locals
        _globals[mod_camel] = _st_locals[mod_camel]

    # add our Include and Extend functions
    _globals['include'] = _registry.include
    _globals['extend'] = _registry.make_extend

    # for convenience
    try:
        _globals.update({
            # salt, pillar & grains all provide shortcuts or object interfaces
            'salt': SaltObject(__salt__),
            'pillar': __salt__['pillar.get'],
            'grains': __salt__['grains.get'],
            'mine': __salt__['mine.get'],

            # the "dunder" formats are still available for direct use
            '__salt__': __salt__,
            '__pillar__': __pillar__,
            '__grains__': __grains__
        })
    except NameError:
        pass

    if sys.version > 3:
        exec(template.read(), _globals, _locals)
    else:
        exec template.read() in _globals, _locals

    return _registry.salt_data()
