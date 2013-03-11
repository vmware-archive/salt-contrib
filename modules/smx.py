'''
Salt Module to manage Apache Service Mix

The following grains should be set
smx:
  user: admin user name
  pass: password
  path: /absolute/path/to/servicemix/home

or use pillar:
smx.user: admin user name
smx.pass: password
smx.path: /absolute/path/to/servicemix/home

Note:
- if both pillar & grains settings exists -> grains wins
- Tested on apache-servicemix-full-4.4.2.tar.gz
- When a feature is being removed it will not recursivly remove its nested features
  But it will remove the bundles configure in the feature it self
'''

# libs
import time

def __virtual__():
    '''
    Load the module by default
    '''
    
    return 'smx'

def _parse_list(list=[]):
    '''
    Used to parse the result off the list commands.
    for example:
     run('osgi:list')
     run('features:list')
    '''
    ret = []
    for line in list:
        line = line.replace(']','')
        line = line.replace('[','')
        ret.append(line)
    
    return ret

def run(cmd='shell:logout'):
    '''
    execute a command in the servicemix console
    will return an array of the STDOUT
    
    CLI Examples::
        
        salt '*' smx.run 'osgi:list'
    '''
    
    # Get command from grains, if are not set default to modules.config.option
    try:
        user = __grains__['smx']['user']
        password = __grains__['smx']['pass']
        bin = __grains__['smx']['path'] + '/bin/client'
    except KeyError:
        try:
            user = __salt__['config.option']('smx.user')
            password = __salt__['config.option']('smx.pass')
            bin = __salt__['config.option']('smx.path')
            if user and password and bin:
                bin += '/bin/client'
            else:
                return []
        except Exception:
            return []
    
    ret = __salt__['cmd.run']( "'{0}' -u '{1}' -p '{2}' '{3}'".format(bin, user, password, cmd) ).splitlines()
    if len(ret) > 0 and ret[0].startswith('client: JAVA_HOME not set'):
        ret.pop(0)
    return ret

def status():
    '''
    Test if the servicemix daemon is running
    
    CLI Examples::
        
        salt '*' smx.status
    '''
    return run('osgi:list | head -n 1 | grep -c ^START') == ['1']

def is_repo(url):
    '''
    check if the URL is configured as a feature repository
    
    CLI Examples::
        
        salt '*' smx.is_repo http://salt/smxrepo/repo.xml
    '''
    
    return run('features:listurl | grep -c " {0}$"'.format(url)) == ['1']

def feature_addurl(url):
    '''
    Add the url as a feature repository
    
    CLI Examples::
        
        salt '*' smx.features_addurl http://salt/smxrepo/repo.xml
    '''
    
    if is_repo(url):
        return 'present'
    
    run('features:addurl {0}'.format(url))
    if is_repo(url):
        return 'new'
    else:
        return 'missing'

def feature_removeurl(url):
    '''
    Remove the url as a feature repository
    
    CLI Examples::
        
        salt '*' smx.feature_removeurl http://salt/smxrepo/repo.xml
    '''
        
    if is_repo(url) == False:
        return 'absent'.format(url)
    else:
        run('features:removeurl {0}'.format(url))
        if is_repo(url) == False:
            return 'removed'.format(url)
        else:
            return 'failed'.format(url)

def feature_refreshurls():
    '''
    Refresh all the feature repositories
    
    CLI Examples::
        
        salt '*' smx.feature_refreshurls
    '''
    
    for line in run('features:listurl | grep -v "^ Loaded"'):
        url = line.split()[1]
        if feature_refreshurl(url) != 'refreshed':
            return 'error refreshing {0}'.format(url)
    return 'refreshed'

def feature_refreshurl(url):
    '''
    Refresh the feature repository
    
    CLI Examples::
        
        salt '*' smx.feature_refreshurl http://salt/smxrepo/repo.xml
    '''
    if is_repo(url):
        run('features:refreshurl {0}'.format(url))
        return 'refreshed'
    else:
        return 'missing'.format(url)

def bundle_active(bundle):
    '''
    check if the bundle is active
    
    CLI Examples::
        
        salt '*' smx.bundle_active 'some.bundle.name'
    '''
    
    for line in _parse_list(run('osgi:list -s -u | grep Active')):
        lst = line.split()
        if bundle == lst[-1]:
             return True
    
    return False

def nonactive_bundles(bundles=''):
    '''
    return a list of non-active bundles from the csv list
    
    CLI Examples::
        
        salt '*' smx.nonactive_bundles 'some.bundle.name,some.other.name'
    '''
    
    ret = []
    for b in bundles.split(','):
        if bundle_active(b) == False:
            ret.append(b)
    return ','.join(ret)

def bundle_exists(bundle):
    '''
    check if the bundle exists
    
    CLI Examples::
        
        salt '*' smx.bundle_exists 'some.bundle.name'
    '''
    
    for line in _parse_list(run('osgi:list -s -u')):
        lst = line.split()
        if bundle == lst[-1]:
             return True
    
    return False

def bundle_start(bundle):
    '''
    start the bundle
    
    CLI Examples::
        
        salt '*' smx.bundle_start 'some.bundle.name'
    '''
    
    if bundle_exists(bundle) == False:
        return 'missing'
    
    run('osgi:start {0}'.format(bundle))
    
    if bundle_active(bundle):
        return 'active'
    else:
        return 'error'

def bundle_stop(bundle):
    '''
    stop the bundle
    
    CLI Examples::
        
        salt '*' smx.bundle_stop 'some.bundle.name'
    '''
    
    if bundle_exists(bundle) == False:
        return 'missing'
    
    run('osgi:stop {0}'.format(bundle))
    
    if bundle_active(bundle) == False:
        return 'stopped'
    else:
        return 'error'

def is_feature_installed(feature, version=''):
    '''
    check if the feature is installed
    
    CLI Examples::
        
        salt '*' smx.is_feature_installed 'myFeature'
        salt '*' smx.is_feature_installed 'myFeature' '1.1.0'
    '''
    
    for line in _parse_list(run('features:list -i')):
        lst = line.split()
        if version:
            if version == lst[1] and feature == lst[2]:
                return True
        else:
             if feature == lst[2]:
                 return True
    
    return False

def is_feature_installed_latest(feature):
    '''
    check if the feature is installed
    
    CLI Examples::
        
        salt '*' smx.is_feature_installed_latest 'myFeature'
    '''
    
    latest = '0'
    feature_refreshurls()
    for line in _parse_list(run('features:list')):
        lst = line.split()
        if lst[2] == feature:
            latest = max(str(lst[1]),latest)
    
    return is_feature_installed(feature, str(latest))

def feature_install(feature, version='', bundles='', wait4bundles=5):
    '''
    Install a feature.
    
    a third optional arguments is a csv list of bundle names
      that should be in Active mode after the feature installation to validate
      (in the format of osgi:list -s command)
    a forth argument is a time in seconds to check the bundles if active
    
    CLI Examples::
        
        salt '*' smx.feature_install 'myFeature'
        salt '*' smx.feature_install 'myFeature' '1.0.0'
        salt '*' smx.feature_install 'myFeature' '1.2.3' 'com.sun.jersey.core,some.other.bundle' 10
    '''
    
    if version:
        feature_fullname = '/'.join([feature, version])
    else:
        feature_fullname = feature
    
    if is_feature_installed(feature, version) == False:
        feature_refreshurls()
        run('features:install {0}'.format(feature_fullname))
        if is_feature_installed(feature, version) == False:
            return 'failed'
    
    if bundles != '':
        time.sleep(wait4bundles)
    errBundles = nonactive_bundles(bundles)
    
    if len(errBundles) == 0:
        return 'installed'
    else:
        return 'failed, non Active bundles: {0}'.format(','.join(errBundles))
    
def feature_remove(feature, version=''):
    '''
    Uninstall the feature
    
    CLI Examples::
        
        salt '*' smx.feature_remove name-of-feature
        salt '*' smx.feature_remove name-of-feature 1.1.1
    '''
        
    if is_feature_installed(feature, version) == False:
        return 'absent'
    
    if version:
        feature_fullname = '/'.join([feature, version])
    else:
        feature_fullname = feature
    
    run('features:uninstall {0}'.format(feature_fullname))
    if is_feature_installed(feature, version):
        return 'error'
    else:
        return 'removed'

def feature_remove_all_versions(feature):
    '''
    Uninstall the feature in all its versions
    
    CLI Examples::
        
        salt '*' smx.feature_remove_all_versions name-of-feature
    '''
    
    removed = ""
    for line in _parse_list(run('features:list -i')):
        lst = line.split()
        if lst[0] == 'installed' and lst[2] == feature:
            removed += " {0}".format(lst[1])
            if feature_remove(feature, lst[1]) == 'error':
                return 'error removing {0}'.format('/'.join([feature, lst[1]]))
    
    if removed:
        return 'removed: {0}'.format(removed)
    else:
        return 'no version removed'
