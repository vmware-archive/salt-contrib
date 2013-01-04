'''
Drizzle is a MySQL fork optimized for Net and Cloud performance.
This module provides Drizzle compatibility to Salt execution

:Depends: MySQLdb python module
:Configuration: The following changes are to be made in
                /etc/salt/minion on respective minions

Example::
    drizzle.host: '127.0.0.1'
    drizzle.port: 4427
    drizzle.user: 'root'
    drizzle.passwd: ''
    drizzle.db: 'drizzle'

Configuration file can also be included such as::
    drizzle.default_file: '/etc/drizzle/config.cnf'
'''

# Importing the required libraries
import time
import logging
import re
import salt.utils

try:
    import MySQLdb
    import MySQLdb.cursors
    has_mysqldb = True
except ImportError:
    has_mysqldb = False


# Salt Dictionaries
__outputter__ = {
    'ping': 'txt',
    'status': 'yaml',
    'version': 'yaml'
}
__opts__ = __salt__['test.get_opts']()


def __virtual__():
    '''
    This module is loaded only if the
    database and the libraries are present
    '''

    # Finding the path of the binary
    has_drizzle = False
    if salt.utils.which('drizzle'):
        has_drizzle = True

    # Determining load status of module
    if has_mysqldb and has_drizzle:
        return 'drizzle'
    return False


# Helper functions
def _connect(**dsn):
    '''
    This method is used to establish a connection
    and returns the connection
    '''

    # Initializing the required variables
    dsn_url = {}
    parameter = ['host','user','passwd','db','port']

    # Gathering the dsn information
    for param in parameter:
        if param in dsn:
            dsn_url[param] = dsn[param]
        else:
            dsn_url[param] = __opts__['drizzle.{0}'.format(param)]

    # Connecting to Drizzle!
    drizzle_db = MySQLdb.connect(**dsn_url)
    drizzle_db.autocommit(True)
    return drizzle_db


def status():
    '''
    Show the status of the Drizzle server
    as Variable_name and Value

    CLI Example::

        salt '*' drizzle.status
    '''
    


def version():
    '''
    Returns the version of Drizzle server
    that is running on the minion

    CLI Example::

        salt '*' drizzle.version
    '''

    drizzle_db = _connect()
    cursor = drizzle_db.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT VERSION()')
    version = cursor.fetchone()
    cursor.close()
    drizzle_db.close()
    return version

def ping():
    return True
