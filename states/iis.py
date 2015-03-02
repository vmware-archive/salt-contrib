# -*- coding: utf-8 -*-
'''
Support for Microsoft IIS

Note:
  when configuring iis resources (vdir, site, app, appool etc...)
  the states supports only configuration of top-level object
  for example in order to config a vdir property of a vdir of a certain app use the vdir_present and not the app_present.
  this sounds a bit obvious but it is a common pitfall =)
'''

# Python libs
import logging
import re

log = logging.getLogger(__name__)


def __virtual__():
    '''
    Load only on minions with the iis module
    '''
    if 'iis.cert_list_permission' in __salt__:
        return 'iis'
    return False


def _resource_present(resource, name, settings, alt_name=None):
    '''
    Generic State which make sure a resource is properly configured
    '''

    if alt_name is None:
        alt_name = name

    resource = resource.lower()
    if settings is None:
        settings = {}

    ret = {
        'name': name,
        'result': True,
        'changes': {},
        'comment': ''
    }

    # Decide what to do
    need_2_add = alt_name not in __salt__['iis.{0}_list'.format(resource)]()
    need_2_config = {}
    if not need_2_add:
        for key, value in __salt__['iis.{0}_get_config'.format(resource)](alt_name, settings.keys()).iteritems():
            if value.lower() != str(settings[key]).lower():
                need_2_config.update({key: settings[key]})
        if not need_2_config:
            return ret

    # Test
    if __opts__['test']:
        ret['result'] = None
        if need_2_add:
            ret['comment'] = '{0} will be created'.format(alt_name)
        else:
            ret['comment'] = 'the following will be set {0}'.format(need_2_config)
        return ret

    if need_2_add:
        if not __salt__['iis.{0}_add'.format(resource)](name, settings):
            ret['comment'] = 'could not create {1} "{0}"'.format(name, resource)
            ret['result'] = False
            return ret
        ret['comment'] = '{1} "{0}" created'.format(name, resource)
        ret['changes']['add'] = name
        return ret

    # Else we need to adjust the configuration
    if not __salt__['iis.{0}_set'.format(resource)](alt_name, need_2_config):
        ret['comment'] = 'could not configure {1} "{0}"'.format(name, resource)
        ret['result'] = False
        return ret
    ret['comment'] = '{1} "{0}" configured'.format(name, resource)
    ret['changes']['config'] = need_2_config
    return ret


def pfx_present(name, password, reg='LOCAL_MACHINE\My', granted_users=None):
    '''
    Install the PFX certificate
    grant permissions to the granted_users users

    name:
        absolute path to the pfx file
    password:
        password of the pfx file
    reg:
        Registry key of the certificate
    granted_users:
        list of users to have access to that certificate

    Example::

        install.pfx.certificate:
          iis.pfx_present:
            - name: c:\some.pfx
            - password: somepass
            - reg: LOCAL_MACHINE\My
            - granted_users:
              - Network Service
    '''

    ret = {
        'name': name,
        'result': True,
        'changes': {},
        'comment': ''
    }

    need_2_install = True
    need_2_grant = False

    # Normalize granted_users list
    if granted_users is None:
        granted_users = []
    else:
        granted_users = map(
            lambda x: x.upper(),
            granted_users
        )

    # Decide what to do
    pfx_data = __salt__['iis.get_data_from_pfx'](name, password)
    log.debug(pfx_data)
    if not pfx_data:
        ret['comment'] = 'can\'t get the meta data from the PFX certificate'
        ret['result'] = False
        return ret
    subject = re.match('CN=(.*?), .*', pfx_data['Subject']).group(1)

    for cert in __salt__['iis.cert_list'](reg, ['Thumbprint', 'Subject']):
        log.debug(cert)
        if pfx_data['Thumbprint'].upper() == cert['Thumbprint'].upper() and \
                        pfx_data['Subject'].upper() == cert['Subject'].upper():
            need_2_install = False
            granted = map(
                lambda x: x.split('\\')[1].upper(),
                __salt__['iis.cert_list_permission'](subject, reg)
            )
            need_2_grant = list(set(granted_users) - set(granted))
            if not need_2_grant:
                ret['comment'] = 'the certificate is installed and configured correctly'
                return ret
            break

    if need_2_install:
        need_2_grant = granted_users

    # Test
    if __opts__['test']:
        ret['result'] = None
        return ret

    # Install the PFX5
    if need_2_install:
        ret['result'] = __salt__['iis.cert_import_pfx'](name, password)
        if not ret['result']:
            ret['comment'] = 'Failed to import PFX certificate'
            return ret
        ret['changes']['install'] = '{0} imported'.format(name)

    # Grant users
    if need_2_grant:
        for user in granted_users:
            if not __salt__['iis.cert_grant_permission'](user, subject, reg):
                ret['result'] = False
                ret['comment'] = 'failed to grant permissions to "{0}"'.format(user)
                return ret
        ret['changes']['grant'] = need_2_grant

    return ret


def ssl_bind_builtin(name, port, appid='00000000-0000-0000-0000-000000000000'):
    '''
    Bind to ipport the builtin SSL certificate that comes with IIS

    Example::

        bind_to_iis:
          iis.ssl_bind_builtin:
            - name: 0.0.0.0
            - port: 443
    '''

    thumbprint = None
    for c in __salt__['iis.cert_list'](r'LOCAL_MACHINE\My', ['Thumbprint', 'Subject']):
        if c['Subject'].startswith('CN=WMSvc-'):
            thumbprint = c['Thumbprint']
            break

    if thumbprint is None:
        return {
            'name': name,
            'result': False,
            'changes': {},
            'comment': 'could not find built-in SSL certificate'
        }
    return ssl_bind(thumbprint, appid, name, port)


def ssl_bind(name, appid, address, port):
    '''
    Bind the SSL certificate with named thumbprint and appid to the specified address and port

    Example::

        37cc65cf61f02f860c1370a24a404025988eae21:
          iis.ssl_bind:
            - appid: 00000000-0000-0000-0000-000000000000
            - address: 0.0.0.0
            - port: 443
    '''

    ret = {
        'name': name,
        'result': True,
        'changes': {},
        'comment': ''
    }

    # Decide what to do
    need_2_remove = False
    current_config = __salt__['iis.bind_list'](address, port)
    if current_config is False:
        ret['changes'] = {'bind': 'add a new bind'}
    else:
        if current_config['Certificate Hash'].lower() == name.lower() and\
                current_config['Application ID'].lower() == '{{{0}}}'.format(appid).lower():
            return ret
        need_2_remove = True

    # Test
    if __opts__['test']:
        ret['result'] = None
        return ret

    if need_2_remove:
        if not __salt__['iis.unbind_ssl'](address, port):
            ret['comment'] = 'could not unbind certificate from {0}:{1}'.format(address, port)
            ret['result'] = False
            return ret
        ret['changes']['removed'] = 'replace current thumbprint={0}, appid={1}'.format(
            current_config['Certificate Hash'], current_config['Application ID']
        )
    ret['result'] = __salt__['iis.bind_ssl'](name, appid, address, port)
    if not ret['result']:
        ret['comment'] = 'failed to bind ssl certificate'
    else:
        ret['changes'] = {'added': 'add a new bind'}
    return ret


def apppool_present(name, settings=None):
    '''
    Install and Configure an application pool

    Example::

        MyApp:
          iis.apppool_present:
            - settings:
                managedRuntimeVersion: 4.0
                processModel.loadUserProfile: True
    '''

    return _resource_present('apppool', name, settings)


def site_present(name, settings=None):
    '''
    Install and Configure an application pool

    Example::

        MySite:
          iis.site_present:
            - settings:
                bindings: https/*:443:
    '''

    return _resource_present('site', name, settings)


def app_present(name, site, settings=None):
    '''
    Install and Configure an application

    Example::

        /myapp:
          iis.app_present:
            - site: mysite
    '''

    if settings is None:
        settings = {}
    settings['path'] = name

    return _resource_present('app', site, settings, site+name)


def vdir_present(name, app, settings=None):
    '''
    Install and Configure a virtual directory

    Example::

        /:
          iis.vdir_present:
            - app: mysite/myapp
            - settings:
                physicalPath: C:\myapp

        root.vdir:
          iis.vdir_present:
            - name: /
            - app: rootapp/
            - settings:
                physicalPath: C:\myapp
    '''

    if settings is None:
        settings = {}
    settings['path'] = name

    if name == '/' and '/' not in app[0:-1]:
        return _resource_present('vdir', app, settings, app)
        
    alt_name = app.rstrip('/') + name
    return _resource_present('vdir', app, settings, alt_name)

