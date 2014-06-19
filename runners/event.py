# -*- coding: utf-8 -*-
'''
A backport of the state.event runner in Helium for earlier Salt versions
'''
# Import pytohn libs
from __future__ import print_function

import fnmatch
import json
import logging
import sys

# Import salt libs
import salt.utils.event

logger = logging.getLogger(__name__)

def event(tagmatch='*', count=1, quiet=False, sock_dir=None):
    '''
    Watch Salt's event bus and block until the given tag is matched

    .. versionadded:: Helium

    This is useful for taking some simple action after an event is fired via
    the CLI without having to use Salt's Reactor.

    :param tagmatch: the event is written to stdout for each tag that matches
        this pattern; uses the same matching semantics as Salt's Reactor.
    :param count: this number is decremented for each event that matches the
        ``tagmatch`` parameter; pass ``-1`` to listen forever.
    :param quiet: do not print to stdout; just block
    :param sock_dir: path to the Salt master's event socket file.

    CLI Examples:

    .. code-block:: bash

        # Reboot a minion and run highstate when it comes back online
        salt 'jerry' system.reboot && \\
            salt-run state.event 'salt/minion/jerry/start' quiet=True && \\
            salt 'jerry' state.highstate

        # Reboot multiple minions and run highstate when all are back online
        salt -L 'kevin,stewart,dave' system.reboot && \\
            salt-run state.event 'salt/minion/*/start' count=3 quiet=True && \\
            salt -L 'kevin,stewart,dave' state.highstate

        # Watch the event bus forever in a shell for-loop;
        # note, slow-running tasks here will fill up the input buffer.
        salt-run state.event count=-1 | while read -r tag data; do
            echo $tag
            echo $data | jq -colour-output .
        done

    Enable debug logging to see ignored events.
    '''
    sevent = salt.utils.event.SaltEvent(
            'master',
            sock_dir or __opts__['sock_dir'],
            id='')

    while True:
        ret = sevent.get_event(full=True)
        if ret is None:
            continue

        if fnmatch.fnmatch(ret['tag'], tagmatch):
            if not quiet:
                print('{0}\t{1}'.format(ret['tag'], json.dumps(ret['data'])))
                sys.stdout.flush()

            count -= 1
            logger.debug('Remaining event matches: {0}'.format(count))

            if count == 0:
                break
        else:
            logger.debug('Skipping event tag: {0}'.format(ret['tag']))
            continue
