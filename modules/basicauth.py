'''
Module for managing basic authentication password files

:maintainer: Brent Lambert <brent@enpraxis.net>
:maturity: new
:platform: Any
:depends: apache
:configuration: The basicauth password file to be managed 
    can be passed directly into the adduser and deleteuser 
    functions, or it can be set in the minion configuration 
    file as follows::

        basicauth.password_file: /etc/httpd/.htpasswd

    It can also be set in pillar data in a similar manner using
    a .sls file. If no options are specified it will be assumed that
    the htpassword file is located at /etc/.htpasswd

This module looks for the binary /usr/bin/htpasswd and will load
if it is found. Normally this binary is included in the apache
package. 

The htpasswd file must exist in order to successfully 
add and delete users. You can create a new empty file as follows::

    touch /etc/.htpasswd

Be sure to set the correct permissions on the file and configure
your web server accordingly. 
'''

from subprocess import Popen, PIPE
import os


def __virtual__():
    '''
    Must have htpasswd installed
    '''
    if os.path.exists('/usr/bin/htpasswd'):
        return 'basicauth'
    return False


def _runcmd(cmd):
    '''
    Run a command and return output, any error info and return code
    '''
    child = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
    out, err = child.communicate()
    return child.returncode, out, err


def _getPasswordFile(path):
    '''
    Get the full path of the password file
    '''
    if path:
        # path has priority
        return path  
    elif __salt__['config.option']('basicauth.password_file'):
        # Module configuration next
        return __salt__['config.option']('basicauth.password_file')
    elif __pillar__.has_key('basicauth.password_file'):
        # look for pillar data
        return __pillar__['basicauth.password_file']
    else:
        # Specify some default neutral location
        return '/etc/.htpasswd'
    return ''


def adduser(user, passwd, path=None):
    '''
    Add a user and password to the htpasswd file. Password file must 
    already exist. Password file creation can be handled via states 
    or manually to handle permissions and ownership for specific use 
    cases. 

    Note:: Uses the -b option that passes a password via the command 
       line. Unfortunately this is necessary in order to set the 
       password in a non interactive manner. This is not generally 
       recommended and has security implications. Make sure you 
       understand these before you use this function.

    CLI_Example::

        salt 'server' basicauth.adduser bob test1234

        salt 'server' basicauth.adduser bob test1234 \
          /etc/httpd/.htpasswd
    '''
    if user and passwd:
        htpath = _getPasswordFile(path)
        cmd = '/usr/bin/htpasswd -b {0} {1} {2}'.format(htpath, 
                                                        user, 
                                                        passwd)
        result = _runcmd(cmd)
        if result[0] == 0:
            return True
    return False


def deleteuser(user, path=None):
    '''
    Delete user from the password file

    CLI_Example::

        salt 'server' basicauth.deleteuser bob

        salt 'server' basicauth.deleteuser bob /etc/.htpasswd
    '''
    if user:
        htpath = _getPasswordFile(path)
        cmd = '/usr/bin/htpasswd -D {0} {1}'.format(htpath, user)
        result = _runcmd(cmd)
        if result[0] == 0:
            return True
    return False
