"""
Support for Circus: process and socket manager.

:maintainer: Marconi Moreto <caketoad@gmail.com>
:maturity:   new
:platform:   all
"""

import salt.utils


@salt.utils.memoize
def __detect_os():
    return salt.utils.which('circusctl')


def __virtual__():
    """
    Only load the module if circus is installed.
    """
    return 'circus' if __detect_os() else False


def version():
    """
    Return circus version from circusctl --version

    CLI Example::

        salt '*' circus.version
    """
    cmd = '{0} --version'.format(__detect_os())
    out = __salt__['cmd.run'](cmd)
    return out.split(' ')[1]


def list(watcher=None):
    """
    Return list of watchers or active processes in a watcher.

    CLI Example::

        salt '*' circus.list
    """
    return _list(watcher)


def _list(watcher):
    arguments = '{0}'.format(watcher) if watcher else ''
    cmd = '{0} list {1}'.format(__detect_os(), arguments)
    return __salt__['cmd.run'](cmd).split(',')


def dstats():
    """
    Return statistics of circusd.

    CLI Example::

        salt '*' circus.dstats
    """
    cmd = '{0} dstats'.format(__detect_os())
    return __salt__['cmd.run'](cmd)


def stats(watcher=None, pid=None):
    """
    Return statistics of processes.

    CLI Example::

        salt '*' circus.stats mywatcher
    """
    if watcher and pid:
        arguments = '{0} {1}'.format(watcher, pid)
    elif watcher and not pid:
        arguments = '{0}'.format(watcher)
    else:
        arguments = ''

    cmd = '{0} stats {1}'.format(__detect_os(), arguments)
    out = __salt__['cmd.run'](cmd).splitlines()

    # return immediately when looking for specific process
    if pid:
        return out

    processes = _list(None)
    processes_dict = {}
    current_process = None
    for line in out:
        for process in processes:
            if process in line:
                processes_dict[process] = []
                current_process = process
        if current_process not in line:
            processes_dict[current_process].append(line)
    return processes_dict


def status(watcher=None):
    """
    Return status of a watcher or all watchers.

    CLI Example::

        salt '*' circus.status mywatcher
    """
    if watcher:
        arguments = ' status {0}'.format(watcher)
    else:
        arguments = ' status'

    cmd = __detect_os() + arguments
    out = __salt__['cmd.run'](cmd).splitlines()
    return dict([line.split(':') for line in out])


def signal(signal, opts=None):
    """
    Signals circus to start, stop, or restart.

    CLI Example::

        salt '*' circus.signal restart myworker
    """
    valid_signals = ('start', 'stop', 'restart', 'reload', 'quit')

    if signal not in valid_signals:
        return

    if opts:
        arguments = ' {0} {1}'.format(signal, opts)
    else:
        arguments = ' {0}'.format(signal)

    cmd = __detect_os() + arguments
    return __salt__['cmd.run'](cmd)
