'''
Management of bacula File Daemon Configuration
==============================================

Configure Bacula file daemon to allow connections from a 
particular Bacula director, set password credentials, as well as 
the file daemon name and port that it runs on. Configure the 
messages that get returned to the director.

.. code-block:: yaml

    /etc/bacula/bacula-fd.conf:
      bacula:
        - fdconfig
        - dirname: bacula-dir
        - dirpasswd: test1234
        - fdname: bacula-fd
        - fdport: 9102
        - messages: bacula-dir = all, !skipped, !restored
'''
    
import re    


# Search Patterns
dirs = re.compile(r'Director {[^}]*}')
fd = re.compile(r'FileDaemon {[^}]*}')
msgs = re.compile(r'Messages {[^}]*}')


def _getConfig(pattern, config):
    '''
    Get Configuration block
    '''
    m = pattern.search(config)
    if m:
        return m.group()
    return None


def _getParam(pname, config):
    '''
    Get Param from config
    '''
    if pname == 'Password':
        search = '{0} = "(?P<{0}>.*)"'.format(pname)
    else:
        search = '{0} = (?P<{0}>.*)'.format(pname)
    mp = re.search(search, config)
    if mp:
        return mp.group(pname)
    return None
    

def _getConfigParams(config):
    '''
    Get configuration blocks for parameters
    '''
    cparams = {}

    dconfig = _getConfig(dirs, config)
    if not dconfig:
        return None

    cparams['dirname'] = _getParam('Name', dconfig)
    cparams['dirpasswd'] = _getParam('Password', dconfig)

    fdconfig = _getConfig(fd, config)
    if not fdconfig:
        return None

    cparams['fdname'] = _getParam('Name', fdconfig)
    cparams['fdport'] = _getParam('FDport', fdconfig)

    mconfig = _getConfig(msgs, config)
    if not mconfig:
        return None

    cparams['messages'] = _getParam('director', mconfig)
    
    return cparams


def fdconfig(name,
             dirname=None,
             dirpasswd=None,
             fdname=None,
             fdport=None,
             messages=None):
    '''
    Configure a bacula file daemon

    dirname
        The name of the director that is allowed to connect to the
        file daemon.

    dirpasswd
        The password that the director must use to successfully 
        connect to the file daemon.

    fdname
        The name of the file daemon

    fdport
        The port that the file daemon should run on

    messages
        Define how and what messages to send to a director.
    '''
    ret = {'name':name,
           'changes':{},
           'result':None,
           'comment':'',}

    config = ''
    with open(name) as f:
        config = f.read()

    if not config:
        ret['comment'] = config #'Could not find {0}\n'.format(name)
        ret['result'] = False
        return ret
    
    cparams = _getConfigParams(config)
    if not cparams:
        ret['comment'] += 'Could not find configuration information.\n'
        ret['result'] = False
        return ret

    changes = {}

    if dirname and dirname != cparams['dirname']:
        changes['dirname'] = dirname
    if dirpasswd and dirpasswd != cparams['dirpasswd']:
        changes['dirpasswd'] = dirpasswd
    if fdname and fdname != cparams['fdname']:
        changes['fdname'] = fdname
    if fdport and fdport != int(cparams['fdport']):
        changes['fdport'] = fdport
    if messages and messages != cparams['messages']:
        changes['messages'] = messages
        
    if not changes:
        ret['comment'] += 'Bacula file daemon configuration is up to date.\n'
        ret['result'] = True
        return ret

    if __opts__['test']:
        if changes.has_key('dirname'):
            ret['comment'] += \
                'Director Name set to be changed to {0}\n'.format(dirname)
        if changes.has_key('dirpasswd'):
            ret['comment'] += \
                'Director Password set to be changed to {0}\n'.format(dirpasswd)
        if changes.has_key('fdname'):
            ret['comment'] += \
                'File Daemon Name set to be changed to {0}\n'.format(fdname)
        if changes.has_key('fdport'):
            ret['comment'] += \
                'File Daemon Port set to be changed to {0}\n'.format(fdport)
        if changes.has_key('messages'):
            ret['comment'] += \
                'Messages Director set to be changed to {0}\n'.format(messages)
        return ret

    if changes.has_key('dirname') or changes.has_key('dirpasswd'):
        dconfig = _getConfig(dirs, config)
        if changes.has_key('dirname'):
            dconfig = re.sub(r'Name = (.*)', 
                             'Name = {0}'.format(dirname),
                             dconfig)
        if changes.has_key('dirpasswd'):
            dconfig = re.sub(r'Password = "(.*)"',
                             'Password = "{0}"'.format(dirpasswd),
                             dconfig)
        config = dirs.sub(dconfig, config)
        ret['changes']['Director'] = dconfig

    if changes.has_key('fdname') or changes.has_key('fdport'):
        fdconfig = _getConfig(fd, config)
        if changes.has_key('fdname'):
            fdconfig = re.sub(r'Name = (.*)',
                              'Name = {0}'.format(fdname),
                              fdconfig)
        if changes.has_key('fdport'):
            fdconfig = re.sub(r'FDport = (.*)',
                              'FDport = {0}'.format(fdport),
                              fdconfig)
        config = fd.sub(fdconfig, config)
        ret['changes']['FileDaemon'] = fdconfig

    if changes.has_key('messages'):
        mconfig = _getConfig(msgs, config)
        mconfig = re.sub(r'director = (.*)',
                         'director = {0}'. format(messages),
                         mconfig)
        ret['changes']['Messages'] = mconfig
        config = msgs.sub(mconfig, config)

    with open(name, 'w') as f:
        f.write(config)

    ret['comment'] += 'Updated bacula file daemon settings.\n'
    ret['result'] = True
    return ret
