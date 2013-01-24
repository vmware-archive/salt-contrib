'''
Salt module to manage openvz hosts through vzctl and vzlist.
'''

import salt.utils

__outputter__ = {
                'version': 'txt',
                'vzlist': 'txt',
                'execute': 'txt',
                'start': 'txt',
                'stop': 'txt',
                'restart': 'txt'
                }

def __virtual__():
    '''
    Check to see if vzctl and vzlist are installed and load module
    '''
    if salt.utils.which('vzctl') and salt.utils.which('vzlist'):
        return 'vzctl'
    return False

def version():
    '''
    Return version from vzctl --version

    CLI Example::

    salt '*' vzctl.version
    ''' 
    out = __salt__['cmd.run']('vzctl --version')
    return out

def vzlist():
    '''
    Return list of containers from "vzlist -a"

    CLI Example::

    salt '*' vzctl.vzlist
    '''
    out = __salt__['cmd.run']('vzlist -a')
    return out

def execute(ctid=None,
          option=None):
    '''
    Execute a command on a container.

    CLI Example::

    salt '*' vzctl.execute 123 "df -h"
    '''
    if not ctid:
        return "Error: No container ID specified."
    if not option:
        return "Error: No option parameter specified."
	
    ret, error = _checkCtid(ctid)

    if ret:
        output = _runCommand(
                            "exec",
                            ctid,
                            option
                            )
        return output
    else:
        return error

def start(ctid=None,
        option=None):
    '''
    Start a container.

    CLI Example::

    salt '*' vzctl.start 123

    Can accept the wait or force arguments.

    For example::

    salt '*' vzctl.start 123 force
    '''
    if not ctid:
        return "Error: No container ID specified."
	
    ret, error = _checkCtid(ctid)

    if ret:
        output = _runCommand(
                             "start",
                             ctid,
                             option
                             )
        return output
    else:
        return error

def stop(ctid=None,
         option=None):
    '''
    Stop a container.

    CLI Example::

    salt '*' vzctl.stop 123

    Can accept the wait or skip-unmount arguments.

    For example::

    salt '*' vzctl.stop 123 skip-unmount
    '''
    if not ctid:
        return "Error: No container ID specified."
	
    ret, error = _checkCtid(ctid)

    if ret:
        output = _runCommand(
                            "stop",
                            ctid,
                            option
                            )
        return output
    else:
        return error

def restart(ctid=None,
            option=None):
    '''
    Restart a container.

    CLI Example::

    salt '*' vzctl.restart 123

    Can accept the wait, force or fast arguments.

    For example::

    salt '*' vzctl.restart 123 fast
    '''
    if not ctid:
        return "Error: No container ID specified."

    ret, error = _checkCtid(ctid)

    if ret:
        output = _runCommand(
                            "restart",
                            ctid,
                            option
                            )
        return output
    else:
        return error

def _checkCtid(ctid):
    '''
    Checks to see if the ctid is a valid number
    '''
    try:
        ctid = int(ctid)
        return True, None
    except:
        return False, "Error: ctid is not a number."

def _runCommand(
               command,
               ctid,
               option
               ):
    '''
    Use salt to run the command and output.
    '''
    if option is None:
        cmd = 'vzctl {0} {1}'.format(command,ctid)
        out = __salt__['cmd.run'](cmd)
        return out
    else:
        cmd = 'vzctl {0} {1} --{2}'.format(command,ctid,option)
        out = __salt__['cmd.run'](cmd)
        return out
