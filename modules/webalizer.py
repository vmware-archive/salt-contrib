'''
A module for managing webalizer web statistics

:maintainer: Brent Lambert <brent@enpraxis.net>
:maturity: new
:platform: RedHat, Debian Families
:depends: webalizer cron

Assumes that the appropriate web server configuration and access 
controls have already been configured. Will generate a script 
for updating webalizer and will use it with cron to enable automatic 
updates.
'''

from subprocess import Popen, PIPE
import os
import re


# Scripts and paths

webalizer_update='''#!/bin/bash
/usr/bin/webalizer -c {0}
'''

webalizer_scr_path = '/usr/local/bin/webalizer_update'
webalizer_hourly = '/etc/cron.hourly/webalizer'
webalizer_daily = '/etc/cron.daily/webalizer'


def __virtual__():
    '''
    Only supports RedHat and Debian OS Families for now
    '''
    return 'webalizer' if __grains__['os_family'] in ['RedHat', 'Debian'] else False


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


def configure(domain, logfile, period='hourly'):
    '''
    Configure webalizer to track statisctics for a particular domain,
    using a particular log file.

    Parameters:

        domain
            The name of the web domain webalizer should track
        logfile
            The logfile that contains web data for the above domain
        period
            Either 'hourly' or 'daily'

    CLI_Example::

        salt 'server' webalizer.configure domain.com \
          /var/log/httpd/access_log \
          period=daily

        salt 'server' webalizer.configure domain.com \
          /var/log/nginx/access.log
    '''
    if domain and logfile:

        # Get OS specific values
        if __grains__['os_family'] == 'RedHat':
            wconf = '/etc/webalizer.conf'
            hns = r'^#HostName .*$'
        elif __grains__['os_family'] == 'Debian':
            wconf = '/etc/webalizer/webalizer.conf'
            hns = r'^HostName .*$'
        else:
            return False

        hn = re.compile(hns, re.MULTILINE)
        lf = re.compile('^LogFile .*$', re.MULTILINE)

        # Modify the configuration
        with open(wconf, 'r+') as f:
            config = f.read()
            config = hn.sub('HostName {0}'.format(domain), config)
            config = lf.sub('LogFile {0}'.format(logfile), config)
            f.seek(0)
            f.write(config)
            f.truncate()

        # Generate an appropriate update script, store in /usr/local/bin
        update = webalizer_update.format(wconf)
        with open(webalizer_scr_path, 'w') as f:
            f.write(update)
            os.chmod(webalizer_scr_path, 0700)
    
        # Set up cron
        if period == 'hourly':
            if not os.path.exists(webalizer_hourly):
                os.symlink(webalizer_scr_path, webalizer_hourly)
        elif period == 'daily':
            if not os.path.exists(webalizer_daily):
                os.symlink(webalizer_scr_path, webalizer_daily)

        return True

    return False
            
    
def disable():
    '''
    Disable automatic updates.

    CLI_Example::
    
        salt 'server' webalizer.disable
    '''
    _remove(webalizer_hourly)
    _remove(webalizer_daily)
    return True


def update():
    '''
    Update webalizer stats immediately.

    CLI_Example::
    
        salt 'server' webalizer.update
    '''
    result = _runcmd(webalizer_scr_path)
    if result[0]:
        # We have a return code, must be an error
        return False
    return True


