# -*- coding: utf-8 -*-
'''
Support for Microsoft IIS

Notes:
  - WinHttpCertCfg should be installed (http://www.microsoft.com/en-us/download/confirmation.aspx?id=19801)
  - http://www.iis.net/learn/get-started/getting-started-with-iis/getting-started-with-appcmdexe
'''

# Python libs
import logging
import re
import os

# Import salt libs
import salt.utils

log = logging.getLogger(__name__)
try:
    WinHttpCertCfg = os.path.join(
        os.environ['PROGRAMFILES(X86)'], 'Windows Resource Kits', 'Tools', 'WinHttpCertCfg.exe'
    )
    appcmd = os.path.join(
        os.environ['WINDIR'], 'System32', 'inetsrv', 'appcmd.exe'
    )
except KeyError:
    pass


#########################
### Private Functions ###
#########################

def __virtual__():
    '''
    Load only on windows minions
    '''
    if salt.utils.is_windows():
        return 'iis'
    return False


def _resource_list(resource):
    '''
    Wrapper function to the appcmd list x function
    '''

    ret = []
    cmd_ret = __salt__['cmd.run_all']([appcmd, 'list', resource])
    if cmd_ret['retcode'] != 0:
        return False

    for line in cmd_ret['stdout'].splitlines():
        ret.append(line.split('"')[1])
    return ret


def _resource_add(resource, name, settings=None, arg_name_override=None):
    '''
    Add a new resource.

    settings:
        a dictionary of settings to be passed to the "appcmd add RESOURCE" command
    '''

    settings_params = _serialize_settings(settings)
    log.debug('settings: \'{0}\'')

    if arg_name_override is None:
        arg_name_override = resource.lower()

    cmd_ret = __salt__['cmd.run_all']([appcmd, 'add', resource.upper(), '/{0}.name:{1}'.format(arg_name_override, name)] + settings_params)
    if cmd_ret['retcode'] != 0:
        log.error('failed creating {0}'.format(resource))
        log.debug(cmd_ret['stderr'])
        return False
    return True

def _resource_get_config(resource, name, settings):
    '''
    Returns the configuration of the Resource
    '''

    ret = {}
    for i in settings:
        cmd_ret = __salt__['cmd.run_all']([appcmd, 'list', resource.upper(), '/{0}.name:{1}'.format(resource.lower(), name), '/text:{0}'.format(i)])
        if cmd_ret['retcode'] != 0:
            log.error('can\'t get "{0}" from {1} "{2}"'.format(i, resource, name))
            return False
        ret[i] = cmd_ret['stdout'].strip()
    return ret


def _resource_set(resource, name, settings):
    '''
    Configure the resource with the settings dictionary
    '''

    settings_params = _serialize_settings(settings)
    cmd_ret = __salt__['cmd.run_all']([appcmd, 'set', resource.upper(), name] + settings_params)
    if cmd_ret['retcode'] != 0:
        log.error('failed configuring {0}'.format(resource))
        log.debug(cmd_ret['stderr'])
        return False
    return True



def _resource_action(resource, name, action, ignoreNonExist=False):
    '''
    Generic fanction to Start / Stop / Delete  the resource
    '''

    if  name not in _resource_list(resource) and ignoreNonExist == False:
        log.error('not existing {0} {1}'.format(resource,name))
        return False



    cmd_ret = __salt__['cmd.run_all']([appcmd, action.upper(), resource.upper(), name])
    if cmd_ret['retcode'] != 0:
        log.error('failed configuring {0}'.format(resource))
        log.debug(cmd_ret['stderr'])
        return False
    return True


def _serialize_settings(settings):
    '''
    Serialize the settings dict to appcmd argument
    '''

    if not settings:
        return []
    return map(
        lambda (k, v): '/{0}:{1}'.format(k, v),
        settings.iteritems()
    )


##############################
### Certificate Management ###
##############################

def cert_list_permission(subject, reg=r'LOCAL_MACHINE\My'):
    '''
    List users with permission to the supplied certificate
    '''

    ret = []
    cmd_ret = __salt__['cmd.run_all']('"{0}" -l -c "{1}" -s "{2}"'.format(
        WinHttpCertCfg, reg, subject
    ))

    if cmd_ret['retcode'] != 0:
        log.error('could not find certificate for "{0}" in "{1}"'.format(subject, reg))
        return False

    out = cmd_ret['stdout'].splitlines()
    line = out.pop(0)
    while line != 'Additional accounts and groups with access to the private key include:':
        line = out.pop(0)
    while out:
        ret.append(
            out.pop(0).strip()
        )

    return ret


def cert_grant_permission(user, subject, reg=r'LOCAL_MACHINE\My'):
    '''
    Grant permission to the certificate
    '''

    cmd_ret = __salt__['cmd.run_all']('"{0}" -g -c "{1}" -s "{2}" -a "{3}"'.format(
        WinHttpCertCfg, reg, subject, user
    ))

    if cmd_ret['retcode'] != 0:
        log.error('error granting permissions to "{0}" in "{1}" for "{2}"'.format(subject, reg, user))
        return False
    return True


def cert_import_pfx(pfx, password):
    '''
    Import a PFX certificate bundle via CertUtil
    '''

    cmd_ret = __salt__['cmd.run_all']('certutil -f -p {0} -importpfx {1}'.format(
        password, pfx
    ))

    if cmd_ret['retcode'] != 0:
        log.error('could not import pfx bundle "{0}"'.format(pfx))
        return False

    return True


def cert_list(reg=r'LOCAL_MACHINE\My', fields=None):
    '''
    List all the imported certificates
    '''

    reg = re.sub('LOCAL_MACHINE', 'LocalMachine', reg)
    ret = []
    if fields is None:
        fields = ['Subject', 'Thumbprint', 'SerialNumber']

    out = __salt__['cmd.run'](
        'If (Test-Path certlist.out ) {3} Remove-Item -Recurse -Force certlist.out {4} ; Get-ChildItem Cert:{0} | format-list {1} | Out-File certlist.out -append -width 1000 ; cat certlist.out | where {2}'.format(reg, ','.join(fields),"{$_ -ne \"\"}", "{", "}"),
        shell='powershell',
        python_shell=True
    ).splitlines()


    current = {}
    for line in out:
        if not line:
            continue
        key, value = line.split(':', 1)
        key = key.strip()
        value = value.strip()
        current.update({key: value})
        if len(current) == len(fields):
            ret.append(current)
            current = {}

    return ret


def get_data_from_pfx(pfx, password):
    '''
    Get the thumbprint from a certificate PFX file
    '''

    ret = {}

    cmd_ret = __salt__['cmd.run_all']('certutil -p {0} -dump {1}'.format(password, pfx))


    if cmd_ret['retcode'] != 0:
        log.error('could get data from pfx bundle "{0}", password: "{1}"'.format(pfx,password))
        return False

    match = re.search('^Cert Hash\(sha1\): (.*)', cmd_ret['stdout'], re.MULTILINE)
    try:
        ret['Thumbprint'] = match.group(1).replace(' ', '').strip()
    except (IndexError, AttributeError):
        log.error('could not parse thumbprint from certutil output !')
        return False

    match = re.search('^Subject: (.*)', cmd_ret['stdout'], re.MULTILINE)
    try:
        ret['Subject'] = match.group(1).strip()
    except (IndexError, AttributeError):
        log.error('could not parse subject from certutil output !')
        return False

    return ret


####################
### SSL Bindings ###
####################

def bind_list(address='0.0.0.0', port=443):
    '''
    List the bounded certificates to the ipport
    '''

    ret = {}
    if address == '*':
        address = '0.0.0.0'

    cmd_ret = __salt__['cmd.run_all']('netsh http show sslcert ipport={0}:{1}'.format(address, port))
    if cmd_ret['retcode'] != 0:
        log.error('could not register certificate')
        log.error(cmd_ret['stderr'])
        return False

    lines = cmd_ret['stdout'].splitlines()
    while not lines.pop(0).startswith('-'):
        pass

    for line in lines:
        if not line.strip():
            continue
        key, value = line.split(' : ')
        ret.update({key.strip(): value.strip()})

    return ret


def bind_ssl(thumbprint, appid, address='0.0.0.0', port=443):
    '''
    Register SSL Certificate with a port and a address
    '''

    if address == '*':
        address = '0.0.0.0'

    ret = __salt__['cmd.run_all'](
        'netsh http add sslcert ipport={0}:{1} certhash={2} appid={{{3}}}'.format(
            address, port, thumbprint, appid
        )
    )
    if ret['retcode'] != 0:
        log.error('could not register certificate')
        log.error(ret['stderr'])
        return False
    return True


def unbind_ssl(address='0.0.0.0', port=443):
    '''
    Unbind a certificate from a ipport
    '''

    if address == '*':
        address = '0.0.0.0'

    ret = __salt__['cmd.run_all'](
        'netsh http delete sslcert ipport={0}:{1}'.format(
            address, port
        )
    )
    if ret['retcode'] != 0:
        log.error('could not unbind certificate')
        log.error(ret['stderr'])
        return False
    return True


#########################
### Application Pools ###
#########################

def apppool_list():
    '''
    List the name of all the application pools
    '''

    return _resource_list('APPPOOL')


def apppool_get_config(name, settings):
    '''
    Returns the configuration of the Application Pool
    '''

    return _resource_get_config('APPPOOL', name, settings)


def apppool_add(name, settings=None):
    '''
    Add a new application pool.

    settings:
        a dictionary of settings to be passed to the "appcmd add apppool" command
    '''

    return _resource_add('APPPOOL', name, settings)


def apppool_set(name, settings):
    '''
    Configure the application pool with the settings dictionary
    '''

    return _resource_set('APPPOOL', name, settings)


def apppool_action(name, action):
    '''
    start / stop / delete the application pool
    '''

    return _resource_action('APPPOOL', name, action)


#############
### Sites ###
#############

def site_list():
    '''
    List the name of all the sites
    '''

    return _resource_list('SITE')


def site_get_config(site, settings):
    '''
    Returns the configuration of the Site
    '''

    return _resource_get_config('SITE', site, settings)


def site_add(name, settings=None):
    '''
    Add a new site.

    settings:
        a dictionary of settings to be passed to the "appcmd add site" command
    '''

    return _resource_add('SITE', name, settings)


def site_set(name, settings):
    '''
    Configure the site with the settings dictionary
    '''

    return _resource_set('SITE', name, settings)


def site_action(name, action):
    '''
    start / stop / delete the site
    '''

    return _resource_action('SITE', name, action)



####################
### Applications ###
####################


def app_list():
    '''
    List the name of all the applications
    '''

    return _resource_list('APP')


def app_get_config(app, settings):
    '''
    Returns the configuration of the application
    '''

    return _resource_get_config('APP', app, settings)


def app_add(name, settings=None):
    '''
    Add a new application.

    settings:
        a dictionary of settings to be passed to the "appcmd add app" command
    '''

    return _resource_add('APP', name, settings, 'site')


def app_set(name, settings):
    '''
    Configure the application with the settings dictionary
    '''

    return _resource_set('APP', name, settings)

def app_action(name, action):
    '''
    start / stop / delete the application
    '''

    return _resource_action('APP', name, action)



############
### vDir ###
############


def vdir_list():
    '''
    List the name of all the virtual directories
    '''

    return _resource_list('VDIR')


def vdir_get_config(vdir, settings):
    '''
    Returns the configuration of the virtual directories
    '''

    return _resource_get_config('VDIR', vdir, settings)


def vdir_add(name, settings=None):
    '''
    Add a new virtual directory.

    settings:
        a dictionary of settings to be passed to the "appcmd add vdir" command
    '''

    return _resource_add('VDIR', name, settings, 'app')


def vdir_set(name, settings):
    '''
    Configure the virtual directories with the settings dictionary
    '''

    return _resource_set('VDIR', name, settings)



####################
### IIS configuration Backups ###
####################


def backup_action(name, action):
    '''
    Add / Restore / delete IIS cconfigurations backup .

    '''

    return _resource_action("BACKUP", name, action, True)

def backup_list():
    '''
    List the name of all the backup configurations
    '''

    return _resource_list('BACKUP')
