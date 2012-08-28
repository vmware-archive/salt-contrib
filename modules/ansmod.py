"""Salt module that lets you invoke Ansible modules.

Requires Ansible installed on minion servers. (ie, the command:
"python -c 'import ansible'" should be successful)

See http://ansible.github.com/
"""
from __future__ import absolute_import
import os
import re
import logging
import tempfile
import subprocess
from subprocess import PIPE
from string import maketrans

log = logging.getLogger(__name__)

from ansible.utils import parse_json
import ansible.module_common as ans_common
import ansible.constants as ans_consts


# Module configuration. Set these in the minion configuration file.
__opts__ = {
    # Absolute path to the dir containing Ansible modules
    'ansible.modules_dir': ans_consts.DEFAULT_MODULE_PATH
}

__outputter__ = { 'run_mod': 'txt' }

# Path to the dir containing ansible module files.
ANSIBLE_MOD_DIR = '/Users/jkuan/work/ansible/library'

# Only ansible module names matching this pattern will be available in salt.
MOD_NAME_PATTERN = re.compile(r'[a-zA-Z][\w.-]*')

# Table for mapping illegal characters in an ansible module name to legal
# ones for a state function name.
MOD_NAME_TRANS_TABLE = maketrans('. -', '___')

# These are modules are not scripts and are handle specially by ansible.
VIRTUAL_MODS = set("shell fetch raw template".split())

# To keep track of the translated ansible module names and their original forms
STATE_NAMES = {} # { state_name: mod_name }

# These keys will be removed from the state call arguments dict before
# passing it as arguments to an ansible module.
SALT_KEYS = ['__id__', '__sls__', '__env__', 'order', 'name']


def __init__(opts):
    global ANSIBLE_MOD_DIR
    key = 'ansible.modules_dir'
    ANSIBLE_MOD_DIR = opts.get(key, __opts__[key])
    try:
        mods = [ os.path.basename(p) for p in os.listdir(ANSIBLE_MOD_DIR) ]
    except OSError:
        log.error("You might want to set `ansible.modules_dir' to "
                  "an Ansible modules directory in your minion config.")
        raise
    mods = filter(lambda name: \
                MOD_NAME_PATTERN.match(name) and name not in VIRTUAL_MODS,
                mods)
    for i, name in enumerate(mods):
        state = name.translate(MOD_NAME_TRANS_TABLE)
        STATE_NAMES[state] = name


def run(modpath, argline, argdict=None, raise_exc=False):
    """Run an Ansible module given its file path and arguments.

    modpath
      path to the ansible module.

    argline
      the arguments string for the ansible module.

    argdict
      a dict of argname=value that will be appended to argline.

    CLI Example::

    salt '*' ansmod.run /path/to/ansible/library/file "path=~/x.out mode=744"

    """
    if argdict:
        args = ' '.join('%s=%s' % (k, str(v)) for k, v in argdict.items())
    else:
        args = ''
    argline = (argline + " " + args).strip()

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        with open(modpath) as modfile:
            tmp.write(modfile.read() \
                .replace(ans_common.REPLACER, ans_common.MODULE_COMMON) \
                .replace(ans_common.REPLACER_ARGS, repr(argline))
            )
        tmp.flush()
        os.chmod(tmp.name, 0700)
        proc = subprocess.Popen([tmp.name], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        data, err = proc.communicate(argline)
        if proc.returncode != 0 and raise_exc:
            raise subprocess.CalledProcessError(proc.returncode, modpath, err)
    return data


def _state_func(state, **kws):
    """Map salt state invocation to ansible module invocation."""

    state = kws.pop('fun')
    if __opts__['test']:
        return dict(result=None, changes={}, name=state,
                    comment='test is not supported by Ansible modules!')
    argline = kws.pop('args', '')
    for k in SALT_KEYS:
        del kws[k]

    # detect and translate argument 'name_' into 'name'
    NAME_ARG = 'name_'
    if NAME_ARG in kws:
        kws['name'] = kws[NAME_ARG]
        del kws[NAME_ARG]

    modpath = os.path.join(ANSIBLE_MOD_DIR, STATE_NAMES[state])
    output = parse_json(run(modpath, argline, kws, raise_exc=True))

    ret = dict(name=state, result=False, changes={}, comment='')

    if 'failed' not in output:
        ret['result'] = True
    if state in ('command', 'shell') and output['rc'] != 0:
        ret['result'] = False

    if 'msg' in output:
        ret['comment'] = output['msg']
    elif state in ('command', 'shell') and output['stderr']:
        ret['comment'] = output['stderr']

    if ret.get('changed', True):
        ret['changes'] = dict(ansible=output)
    return ret


