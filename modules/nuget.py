# -*- coding: utf-8 -*-
'''
_modules.nuget
~~~~~~~~~~~~~~~~~~~
Description
    Manage NuGet package installation on Windows servers.
Dependencies
    NuGet 3.x is required, and should be installed in the location specified by _NUGET.
References
    https://goo.gl/Z8Ury7
    https://goo.gl/wCoUXM
'''

# Import python libs
from __future__ import absolute_import
import logging
import os
# Import salt libs
import salt.utils

try:
    _NUGET = os.path.join(os.environ['PROGRAMFILES(X86)'], 'NuGet', 'nuget.exe')
except KeyError:
    pass

_LOG = logging.getLogger(__name__)

# Define the module's virtual name
__virtualname__ = 'nuget'

def __virtual__():
    '''
    Only works on Windows systems that have NuGet.
    '''
    if salt.utils.is_windows():
        if os.path.isfile(_NUGET):
            return __virtualname__
        else:
            _LOG.debug('Unable to find executable: nuget.exe')
    return False

def install(name, version, target, *sources, **kwargs):
    '''
    Install the named package from the provided URL.

    name: The package name.
    version: The version of the package.
    target: The target directory to install the package to.
    sources: The URLs of the NuGet servers.
    exclude_version: The destination directory will only include the package name.

    Returns a boolean representing whether installation succeeded.

    CLI Example:

    .. code-block:: bash

        salt '*' nuget.install name version target sources

        salt '*' nuget.install 'AutoMapper' '4.1.0' 'C:\\pkgs' 'https://api.nuget.org/v3/index.json'
    '''
    kwargs = salt.utils.clean_kwargs(**kwargs)
    exclude_version = kwargs.pop('exclude_version', False)

    if not sources:
        _LOG.error('No sources specified.')
        return False

    # The ExcludeVersion argument to NuGet creates a directory that's just the name of
    # the package, rather than the PackageName.Version format that is normally used.
    dir_name = name

    if not exclude_version:
        dir_name = '{}.{}'.format(dir_name, version)

    package_path = os.path.join(target, dir_name)

    if os.path.isdir(package_path):
        _LOG.debug('Package directory already present: %s', dir_name)
        return True

    command = [_NUGET, 'install', name, '-NonInteractive', '-OutputDirectory', target]

    for source in sources:
        command.extend(['-Source', source])

    if version:
        command.extend(['-Version', version])

    if exclude_version:
        command.extend(['-ExcludeVersion'])

    cmd_ret = __salt__['cmd.run_all'](command)

    if cmd_ret['retcode'] == 0:
        _LOG.debug("Package '%s' version '%s' has been installed.", name, version)
        return True

    _LOG.error('Unable to execute command: %s\nError: %s', command, cmd_ret['stderr'])
    return False

def list_pkgs(*sources):
    '''
    Get the packages and versions available from the provided URLs.

    sources: The URLs of the NuGet servers.

    Returns a dict of packages, with a list of available versions for each.

    CLI Example:

    .. code-block:: bash

        salt '*' nuget.list_pkgs sources

        salt '*' nuget.list_pkgs 'http://packages.local/nuget'
    '''
    ret = dict()

    if not sources:
        _LOG.error('No sources specified.')
        return False

    command = [_NUGET, 'list', '-AllVersions']

    for source in sources:
        command.extend(['-Source', source])

    cmd_ret = __salt__['cmd.run_all'](command)

    if cmd_ret['retcode'] != 0:
        _LOG.error('Unable to execute command: %s\nError: %s', command, cmd_ret['stderr'])
        return ret

    # Extract the package names and versions from the output.
    for line in cmd_ret['stdout'].splitlines():
        line = line.strip()
        items = [item.strip() for item in line.split(' ', 1)]

        if len(items) > 1:
            package, version = items

            if not package in ret:
                _LOG.debug('Found package: %s', package)
                ret[package] = list()
            ret[package].append(version)
    return ret

def get_locals(name='all'):
    '''
    Get the resource and locations.

    name: The local resource - global-packages, http-cache, packages-cache, or all.

    Returns a dict of resource names and their locations.

    CLI Example:

    .. code-block:: bash

        salt '*' nuget.get_locals name

        salt '*' nuget.get_locals 'global-packages'
    '''
    ret = dict()
    command = [_NUGET, 'locals', name, '-List']

    cmd_ret = __salt__['cmd.run_all'](command)

    if cmd_ret['retcode'] != 0:
        _LOG.error('Unable to execute command: %s\nError: %s', command, cmd_ret['stderr'])
        return ret

    # Extract the resource names and versions from the output.
    for line in cmd_ret['stdout'].splitlines():
        items = [item.strip() for item in line.split(': ', 1)]

        if len(items) > 1:
            resource, location = items
            _LOG.debug('Found resource: %s', resource)
            ret[resource] = location
    return ret

def clear_locals(name='all'):
    '''
    Clear the cached resource and locations.

    name: The local resource - global-packages, http-cache, packages-cache, or all.

    Returns a boolean representing whether clearing the cache succeeded. 

    CLI Example:

    .. code-block:: bash

        salt '*' nuget.clear_locals name

        salt '*' nuget.clear_locals 'global-packages'
    '''
    command = [_NUGET, 'locals', name, '-Clear']

    cmd_ret = __salt__['cmd.run_all'](command)

    if cmd_ret['retcode'] != 0:
        _LOG.error('Unable to execute command: %s\nError: %s', command, cmd_ret['stderr'])
        return False

    lines = cmd_ret['stdout'].splitlines()
    while len(lines) > 0:
        line = lines.pop().strip()

        if line == 'Cache cleared.':
            _LOG.debug(line)
            return True
    _LOG.error('Unable to clear cached resources.')
    return False

