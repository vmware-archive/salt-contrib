'''
Support for riak
'''

import salt.utils

__outputter__ = {
    'signal': 'txt',
}

def __virtual__():
    '''
    Only load the module if riak is installed
    '''
    cmd = 'riak'
    if salt.utils.which(cmd):
        return cmd
    return False


def version():
    '''
    Return Riak node version

    CLI Example::

        salt '*' riak.version
    '''
    cmd = 'riak version'
    out = __salt__['cmd.run'](cmd).split('\n')
    return out[1]


def ping():
    if is_up() == True:
        return "pong"
    else:
        return ""


def is_up():
    '''
    Ping a Riak node to check its status

    CLI Example::

        salt '*' riak.is_up
    '''
    cmd = 'riak ping'
    out = __salt__['cmd.run'](cmd).split('\n')
    if len(out) == 2 and out[1] == "pong":
        return True
    else:
        return False


def start():
    '''
    Start a Riak node.

    CLI Example::

        salt '*' riak.start
    '''
    cmd = 'riak start'
    out = __salt__['cmd.run'](cmd).split('\n')
    if len(out) == 1:
        return True
    else:
        return False


def stop():
    '''
    Stop a running Riak node.

    CLI Example::

        salt '*' riak.stop
    '''
    cmd = 'riak stop'
    out = __salt__['cmd.run'](cmd).split('\n')
    if len(out) == 2 and out[1] == "ok":
        return True
    else:
        return False


def restart():
    '''
    Stops and then starts the running Riak node without exiting the Erlang VM.

    CLI Example::

        salt '*' riak.restart
    '''
    cmd = 'riak restart'
    out = __salt__['cmd.run'](cmd).split('\n')
    if len(out) == 2 and out[1] == "ok":
        return True
    else:
        return False


def cluster_join(node):
    '''
    Join this node to the cluster containing <node>.

    node
        The full node name, in the form user@ip-address

    CLI Example::

        salt '*' riak.cluster_join <node>
    '''
    if len(node.split("@")) != 2:
        return False
    cmd = 'riak-admin cluster join %s' % node
    out = __salt__['cmd.run'](cmd).split('\n')
    if len(out) == 2 and out[1].startswith("Success"):
        return True
    else:
        return out[1]


def cluster_leave(node=None, force=False):
    '''
    Instruct this node to hand off its data partitions, leave the cluster and 
    shutdown.

    node
        The full node name, in the form user@ip-address.
        If this is not supplied, the node will attempt to remove itself.

    force
        Remove <node> from the cluster without first handing off data 
        partitions. This command is designed for crashed, unrecoverable nodes, 
        and should be used with caution.

    CLI Example::

        salt '*' riak.cluster_leave <node> [<force>]
    '''
    if node is not None and len(node.split("@")) != 2:
        return False
    if force == False:
        cmd = 'riak-admin cluster leave'
    else:
        cmd = 'riak-admin cluster force-remove'
    if node is not None:
        cmd = '%s %s' % (cmd, node)
    out = __salt__['cmd.run'](cmd).split('\n')
    if len(out) == 2 and out[1].startswith("Success"):
        return True
    else:
        return out[1]


def cluster_replace(node1, node2, force=False):
    '''
    Instruct <node1> to transfer all data partitions to <node2>, then leave the
    cluster and shutdown.

    node1
        The full node name, in the form user@ip-address

    node2
        The full node name, in the form user@ip-address

    force
        Remove <node> from the cluster without first handing off data 
        partitions. This command is designed for crashed, unrecoverable nodes, 
        and should be used with caution.

    CLI Example::

        salt '*' riak.cluster_replace <node>
    '''
    if len(node1.split("@")) != 2 and len(node2.split("@")) != 2:
        return False
    cmd = 'riak-admin cluster replace %s %s' % (node1, node2)
    out = __salt__['cmd.run'](cmd).split('\n')
    if len(out) == 2 and out[1].startswith("Success"):
        return True
    else:
        return out[1]


def cluster_plan():
    '''
    Display the currently staged cluster changes.

    CLI Example::

        salt '*' riak.cluster_plan
    '''
    cmd = 'riak-admin cluster plan'
    out = __salt__['cmd.run'](cmd).split('\n')
    if len(out) == 2 and out[1] == "There are no staged changes":
        return None
    return out


def cluster_clear():
    '''
    Clear the currently staged cluster changes.

    CLI Example::

        salt '*' riak.cluster_clear
    '''
    cmd = 'riak-admin cluster clear'
    out = __salt__['cmd.run'](cmd).split('\n')
    if len(out) == 2 and out[1] == "Cleared staged cluster changes":
        return True
    return out


def cluster_commit():
    '''
    Commit the currently staged cluster changes.

    CLI Example::

        salt '*' riak.cluster_commit
    '''
    cmd = 'riak-admin cluster commit'
    out = __salt__['cmd.run'](cmd).split('\n')
    if len(out) == 2 and out[1].startswith("You must verify the plan"):
        return cluster_plan()
    return out


def ring_status():
    '''
    Outputs the current claimant, its status, ringready, pending ownership 
    handoffs and a list of unreachable nodes.

    CLI Example::

        salt '*' riak.ring_status
    '''
    cmd = 'riak-admin ring-status'
    out = __salt__['cmd.run'](cmd).split('\n')
    out = out[1:len(out)]
    ret = []
    for line in out:
        if len(line) > 0 and line[:1] != "=" and line[:1] != " ":
            ret.append(line)
    return ret


def member_status():
    '''
    Prints the current status of all cluster members.

    CLI Example::

        salt '*' riak.member_status
    '''
    cmd = 'riak-admin member-status'
    out = __salt__['cmd.run'](cmd).split('\n')
    out = out[1:len(out)]
    ret = []
    for line in out:
        if len(line) > 0 and line[:1] != "=" and line[:1] != "-":
            ret.append(line)
    return ret
