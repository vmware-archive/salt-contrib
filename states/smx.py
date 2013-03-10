'''
Manages Apache Service Mix

The following grains should be set
grains:
  smx:
    user: admin user name
    pass: password
    path: /absolute/path/to/servicemix/home

Note:
- Tested on apache-servicemix-full-4.4.2.tar.gz
- When a feature is being removed it will not recursivly remove its nested features
  But it will remove the bundles configure in the feature it self
'''

def __virtual():
    '''
    Load the state only if smx module is loaded
    '''
    
    return 'smx' if 'smx' in __salt__ else False

def feauture_repository_present(name):
    '''
    Verifies that the repository url is configured and updated
    '''
    
    ret = {'name': name,
           'result': True,
           'changes': {},
           'comment': ''}
    
    if __salt__['smx.is_feature_url_configured'](name):
        ret['comment'] = 'The repository {0} is already configured'.format(name)
        return ret
    
    if __opts__['test']:
        ret['changes'] = {'added': name}
        return ret
    
    if __salt__['smx.feature_addurl'](name) == 'new':
        ret['changes'] = {'added': name}
    else:
        ret['result'] = False
        ret['comment'] = 'fail to configure {0} as a feature repository'.format(name)
    
    return ret

def feature_installed_latest(name, bundles=''):
    '''
    Verifies that the feature is installed in its latest version
    a second optional arguments is a csv list of bundle names
    that should be in Active mode after the feature installation
    (in the format of osgi:list -s -u command)
    
    Note: it won't start the bundles if the feature is already installed
    '''
    
    version = __salt__['smx.get_latest_feature_version'](name)
    if version:
        return feature_installed(name, version, bundles)
    else:
        return {'name': name,
           'result': False,
           'changes': {},
           'comment': 'could not get latest version of the feature'}

def feature_installed(name, version, bundles=''):
    '''
    Verifies that the feature is installed
    a third optional arguments is a csv list of bundle names
    that should be in Active mode after the feature installation
    (in the format of osgi:list -s -u command)
    
    Note: it won't start the bundles if the feature is already installed
    '''
    
    ret = {'name': name,
           'result': True,
           'changes': {},
           'comment': ''}
    
    # validate
    if version  == '':
        ret['result'] = False
        ret['comment'] = 'must specify a version'
        return ret
    
    # prepare
    feature_fullname = '/'.join([name, version])
    if __salt__['smx.is_feature_installed'](name, version):
            ret['comment'] = 'the feature is installed already'
            return ret
    
    # remove old versions if needed
    msg = __salt__['smx.feature_remove_all_versions'](name)
    if msg.startswith('error'):
        ret['comment'] = msg
        ret['result'] = False
        return ret
    elif msg.startswith('removed'):
        ret['changes']['removed'] = msg
    
    # Install it
    instRes = __salt__['smx.feature_install'](name, version, bundles)
    if instRes == 'installed':
        ret['changes']['installed'] = feature_fullname
        if bundles != '':
            ret['comment'] += ', bundles are Active'
    elif instRes == 'failed':
        ret['result'] = False
        ret['comment'] += ', could not install feature'
    else:
        ret['result'] = False
        ret['comment'] += ', the following bundles are not Active {0}'.format(__salt__['smx.get_nonactive_bundles'](bundles))
    
    return ret
