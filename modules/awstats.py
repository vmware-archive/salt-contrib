'''
A module for managing awstats web statsicics in static mode

:maintainer: Brent Lambert <brent@enpraxis.net>
:maturity: new
:platform: RedHat, Debian Families
:depends: awstats cron

Assumes that the appropriate web server configuration and access
controls have already been configured. Will generate a script for
updating awstats static files, and will use it with cron to enable 
automatic updates.

'''

from subprocess import Popen, PIPE
import os
import re


# Script for updating awstats static pages

awstats_update = '''#!/bin/bash
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

# Default paths

awstats_scr_path = '/usr/local/bin/awstats_update'
awstats_static = '/usr/share/awstats/tools/awstats_buildstaticpages.pl'
awstats_hourly = '/etc/cron.hourly/awstats'
awstats_daily = '/etc/cron.daily/awstats'


def __virtual__():
    '''
    Only supports RedHat and Debian OS Families for now
    '''
    return 'awstats' if __grains__['os_family'] in ['RedHat', 'Debian'] else False


def _runcmd(cmd):
    '''
    Run a command and return output, any error info and return code
    '''
    child = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
    out, err = child.communicate()
    return child.returncode, out, err


def _remove(fpath):
    '''
    If a file exist remove it
    '''
    try:
        os.unlink(fpath)
    except OSError, e:
        # Ignore if file does not exist
        if e.errno != 2:
            raise OSError, e


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
          period=daily

        salt 'server' awstats.configure domain=example.com \
          logfile=/var/log/httpd/example.com-access_log
    '''
    if domain and logfile:

        # Get OS specific values
        if __grains__['os_family'] == 'RedHat':
            awstats = '/usr/share/awstats/wwwroot/cgi-bin/awstats.pl'
            model = '/etc/awstats/awstats.model.conf'
            tdir = '/var/www/awstats'
        elif __grains__['os_family'] == 'Debian':
            awstats = '/usr/lib/cgi-bin/awstats.pl'
            model = '/etc/awstats/awstats.conf'
            tdir = '/var/awstats'
        else:
            return False

        sd = re.compile('^SiteDomain=.*$', re.MULTILINE)
        lf = re.compile('^LogFile=>*$', re.MULTILINE)
        awconfig = '/etc/awstats/awstats.{0}.conf'.format(domain)

        # Generate a valid awstats configuration file
        with open(model) as f:
            config = f.read()
            config = sd.sub('SiteDomain="{0}"'.format(domain), config)
            config = lf.sub('LogFile="{0}"'.format(logfile), config)
            with open(awconfig, 'w') as f1:
                f1.write(config)

        # Generate an appropriate update script, store in /usr/local/bin
        update = awstats_update.format(domain,
                                       tdir,
                                       awstats,
                                       awstats_static)

        with open(awstats_scr_path, 'w') as f:
            f.write(update)
            os.chmod(awstats_scr_path, 0700)
        
        # Set up cron
        if period == 'hourly':
            if not os.path.exists(awstats_hourly):
                os.symlink(awstats_scr_path, awstats_hourly)
        elif period == 'daily':
            if not os.path.exists(awstats_daily):
                os.symlink(awstats_scr_path, awstats_daily)

        return True

    return False


def disable():
    '''
    Disable automatic updates.

    CLI_Example::
    
        salt 'server' awstats.disable
    '''
    _remove(awstats_hourly)
    _remove(awstats_daily)
    return True


def update():
    '''
    Update awstats immediately.

    CLI_Example::

        salt 'server' awstats.update
    '''
    result = _runcmd(awstats_scr_path)
    if result[0]:
        # We have a return code, must be an error
        return False
    return True
    
