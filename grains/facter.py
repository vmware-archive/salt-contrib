import salt.utils
import salt.modules.puppet
import salt.modules.cmdmod

__salt__ = {
    'cmd.run': salt.modules.cmdmod._run_quiet,
    'cmd.run_all': salt.modules.cmdmod._run_all_quiet
}


def _check_facter():
    '''
    Checks if facter is installed.
    '''
    salt.utils.check_or_die('facter')


def _format_fact(output):
    '''
    Format facter output into a tuple.
    '''
    try:
        fact, value = output.split(' => ', 1)
        value = value.strip()
    except ValueError:
        fact = None
        value = None
    return (fact, value)


def facter():
    '''
    Return facter facts as grains.
    '''
    _check_facter()

    grains = {}
    try:
        output = __salt__['cmd.run']('facter')

        # Prefix fact names with 'facter_', so it doesn't
        # conflict with existing or future grain names.
        for line in output.splitlines():
            if not line:
                continue
            fact, value = _format_fact(line)
            if not fact:
                continue
            grain = 'facter_{0}'.format(fact)
            grains[grain] = value
        return grains
    except OSError:
        return {}
    return {}
