'''
AWStats Configuration and Update for Static Deployment

:maintainer: Brent Lambert <brent@enpraxis.net>
:maturity: new
:platform: RedHat, Debian Families

A module to configure and update awstats deployed in non-dynamic mode, It

- Controls access to statistics through basic authentication vi .htpasswd file
- Adds and deletes users
- Triggers an immediate update to current stats files managed by awstats.

This module assumes that you already have your web server configured 
with basic authentication, and that you already have a .htpasswd file
present in the awstats static html directory (/var/www/awstats). You can 
add these manually or set up salt states that provide the default 
configuration. For an example how apache could be configured see the 
example below (paths may need to be altered depending on your Linux 
distribution)

Example Apache configuration::

  Alias /awstatscss /usr/share/awstats/wwwroot/css
  Alias /awstatsicons /usr/share/awstats/wwwroot/icon
  Alias /usage /var/www/awstats

  <Directory /var/www/awstats>
    AuthType Basic
    AuthName "Web Site Statistics"
    AuthUserFile /var/www/awstats/.htpasswd
    Require valid-user
    Options +FollowSymLinks
  </Directory>

Create empty password file::

  touch /var/www/awstats/.htpasswd

'''

from subprocess import Popen, PIPE
import os


# Script for updating awstats static pages

update_script = '''#!/bin/bash
SERVER={0}
TARGET_DIR={1}
BUILD_DATE=`date +"%Y-%m"`

{2} -config=$SERVER -update
{3} -config=$SERVER -dir=$TARGET_DIR -month=`date +"%m"` -year=`date +"%Y"` -builddate=$BUILD_DATE
if [ -L $TARGET_DIR/index.html ]
then
  rm -f $TARGET_DIR/index.html
fi
ln -s $TARGET_DIR/awstats.$SERVER.$BUILD_DATE.html $TARGET_DIR/index.html
'''


def __virtual__():
    '''
    Only supports RedHat and Debian OS Families for now
    '''
    return 'awstats' if __grains__['os_family'] in ['RedHat', 'Debian'] else False


# Get Default locations for awstats stuff

def _getAwstatsConfig():
    '''
    Get awstats scripts and configs based on OS Family
    '''
    config = { 'static':'/usr/share/awstats/tools/buildstaticpages.pl', }
    if __grains__['os_family'] == 'RedHat':
        config['awstats'] = '/usr/share/awstats/wwwroot/cgi-bin/awstats.pl'
        config['model'] = '/etc/awstats/awstats.model.conf'
    elif __grains__['os_family'] == 'Debian':
        config['awstats'] = '/usr/lib/cgi-bin/awstats.pl'
        config['model'] = '/etc/awstats/awstats.conf'
    return config


def _getTargetDir():
    '''
    Get configuration values based on OS Family
    '''
    if __grains__['os_family'] == 'RedHat':
        return '/var/www/awstats'
    elif __grains__['os_family'] == 'Debian':
        return '/var/awstats'
    return ''


def _runcmd(cmd):
    '''
    Run a command and return output, any error info and return code
    '''
    child = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
    out, err = child.communicate()
    return child.returncode, out, err


def configure(domain, logfile, period="hourly"):
    '''
    Configure awstats to track a specific domain

    Parameters:

        domain
            The name of the web domain awstats should track
        logfile
            The logfile that contains web data for the above domain
        period
            Either 'hourly' or 'daily'

    CLI Example::

        salt 'server' awstats.configure domain=example.com \
          logfile=/var/log/nginx/access.log \
          period=weekly

        salt 'server' awstats.configure domain=example.com \
          logfile=/var/log/httpd/example.com-access_log
    '''
    if domain and logfile:
        awcfg = _getAwstatsConfig()

        # Generate a valid awstats configuration file
        with open(awcfg['model']) as f:
            config = f.read()
            if __grains__['os_family'] == 'RedHat':
                config = config.replace(
                    'LogFile="/var/log/httpd/access_log"',
                    'LogFile="{0}"'.format(logfile), 1)
                config = config.replace(
                    'SiteDomain="localhost.localdomain"',
                    'SiteDomain="%s"' %domain, 1)
            elif __grains__['os_family'] == 'Debian':
                config = config.replace(
                    'LogFile="/var/log/apache2/access.log"',
                    'LogFile="{0}"'.format(logfile), 1)
                config = config.replace(
                    'SiteDomain=""',
                    'SiteDomain="%s"' %domain, 1)
            with open('/etc/awstats/awstats.%s.conf' %domain, 'w') as f1:
                f1.write(config)

        # Generate an appropriate update script, store in /usr/local/bin
        update = update_script.format(domain,
                                      TARGET_DIR,
                                      AWSTATS,
                                      AWSTATS_STATIC)
        with open('/usr/local/bin/awstats_update', 'w') as f:
            os.chmod('/usr/local/bin/awstats_update', 0700)
            f.write(update)
        
        # Set up cron
        if period == 'hourly':
            if not os.path.exists('/etc/cron.hourly/awstats'):
                os.symlink('/usr/local/bin/awstats_update', 
                           '/etc/cron.hourly/awstats')
        elif period == 'daily':
            if not os.path.exists('/etc/cron.daily/awstats'):
                os.symlink('/usr/local/bin/awstats_update', 
                           '/etc/cron.daily/awstats')

        return domain,

    return False


def adduser(user, passwd):
    '''
    Add a user and password to access awstats info
    
    CLI_Example::

        salt 'server' awstats.adduser bob test1234
    '''
    if user and passwd:
        tdir = _getTargetDir()
        cmd = '/usr/bin/htpasswd -b {0}/.htpasswd {1} {2}'.format(tdir, user, passwd)
        result = _runcmd(cmd)
        if not result[0]:
            return True
    return False


def deleteuser(user):
    '''
    Delete user from password file, and prevent access to awstats info

    CLI_Example::

        salt 'server' awstats.deleteuser bob
    '''
    if user:
        tdir = _getTargetDir()
        cmd = '/usr/bin/htpasswd -D {0}/.htpasswd {1}'.format(tdir, user)
        result = _runcmd(cmd)
        if not result[0]:
            return True
    return False


def update():
    '''
    Update awstats immediately.

    CLI_Example::

        salt 'server' awstats.update
    '''
    result = _runcmd('/usr/local/bin/awstats_update')
    if result[0]:
        return False
    return True
    
