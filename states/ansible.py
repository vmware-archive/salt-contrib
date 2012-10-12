# A salt ansible state module that lets you use ansible
# modules as salt states like this:
#
# test_1:
#   ansible.command:
#     - args: /bin/ls -la
#     - chdir: /Users/jkuan
#
# test_2:
#   ansible.shell:
#     - args: echo 'hohoho' > ~/hoho.txt
#
# test_3:
#   ansible:
#     - setup
#
# test_4:
#   ansible.file:
#     - path: /etc/hosts
#     - dest: ~/hhh.txt
#     - mode: 644
#
# test_5:
#   ansible.easy_install:
#     - name_: sphinx
#
# The special 'args' argument is used for specifying the arguments
# to the ansible module. 'name=value' arguments can also be specified
# separately as shown in the example(test_4). It's also possible to
# mix 'args' and '- name: value' in a state, and in which case, the
# name-value's will be appended to 'args' as 'name=value' pairs.
#
# To work around salt's use of '- name' in state specification, if
# an ansible module has a 'name' argument, then it must be written
# as 'name_' if it is to be specified separately from 'args'.
#
# See the ansmod.py salt module for more information.
#
# To set it up, you'll need ansible installed on minion machines
# so that salt can run ansible locally on the machines. Make sure
# cd / && python -c 'import ansible' succeeds.
#
# Currently, you might also need to define the ansible.modules_dir
# property in your minion configuration file. It should to be set
# to your ansible/library/, where the ansible modules resides.
#
# Note: Not all ansible modules will be available. Those that are
# handled specially(eg, template, fetch, raw, shell) by ansible
# won't be available, except for 'shell'.
#
#
__opts__ = {}

import logging
log = logging.getLogger(__name__)

def __init__(opts):
    """Generate a state function for each ansible module found. """

    # ask salt to load and initialize the ansmod salt module
    from salt.loader import _create_loader, loaded_base_name
    tag = 'module'
    modname = 'ansmod'
    load = _create_loader(opts, 'modules', tag)
    load.gen_module(modname, {})

    # get the loaded ansmod module
    import sys
    try:
        ansmod = sys.modules[loaded_base_name+'.'+tag+'.'+modname]
    except KeyError:
        log.warn("Make sure the %s salt module's been loaded correctly!" \
                  % modname)
    else:
        # populate the state functions in this module
        mod = globals()
        for state in ansmod.STATE_NAMES:
            mod[state] = ansmod._state_func

        # make the use of the shell module actually invokes the
        # command module instead.
        ansmod.STATE_NAMES['shell'] = 'command'


def shell(state, **kws):
    args = kws.pop('args', '')
    return command(state, args=args+'#USE_SHELL', **kws)
    # Note: command will be defined after module __init__

