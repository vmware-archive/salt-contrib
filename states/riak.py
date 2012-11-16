'''
Support for riak$
'''

import salt.utils

def __virtual__():
    '''
    Only load the module if riak is installed
    '''
    cmd = 'riak'
    if salt.utils.which(cmd):
        return cmd
    return False


def running():
    '''
    Verify that riak is running
    '''
    ret = {'name': 'riak', 'result': None, 'comment': '', 'changes': {}}
    is_up = __salt__['riak.is_up']()
    if is_up == False:
        if __salt__['riak.start']():
            ret['result'] = True
            ret['changes']['riak'] = "Riak started"
            ret['comment'] = "Riak started successfully"
        else:
            ret['result'] = False
            ret['comment'] = "Riak failed to start"
    else:
        ret['result'] = True
    return ret


def mod_watch():
    '''
    The Riak watcher, called to invoke the watch command.
    '''
    changes = {'riak': __salt__['riak.restart']()}
    return {'name': 'riak',
            'changes': changes,
            'result': True,
            'comment': 'Service riak started'}
