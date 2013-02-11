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
    'version': 'yaml',
    'schemas': 'yaml',
    'schema_exists': 'txt',
    'schema_create': 'txt',
    'schema_drop': 'txt',
    'tables': 'yaml',
    'table_find': 'yaml',
    'query': 'txt'
}
__opts__ = __salt__['test.get_opts']()


# Check for loading the module
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
    parameter = ['host', 'user', 'passwd', 'db', 'port']

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


# Server functions
def status():
    '''
    Show the status of the Drizzle server
    as Variable_name and Value

    CLI Example::

        salt '*' drizzle.status
    '''

    # Initializing the required variables
    ret_val = {}
    drizzle_db = _connect()
    cursor = drizzle_db.cursor()

    # Fetching status
    cursor.execute('SHOW STATUS')
    for iter in range(cursor.rowcount):
        status = cursor.fetchone()
        ret_val[status[0]] = status[1]

    cursor.close()
    drizzle_db.close()
    return ret_val


def version():
    '''
    Returns the version of Drizzle server
    that is running on the minion

    CLI Example::

        salt '*' drizzle.version
    '''

    drizzle_db = _connect()
    cursor = drizzle_db.cursor(MySQLdb.cursors.DictCursor)

    # Fetching version
    cursor.execute('SELECT VERSION()')
    version = cursor.fetchone()

    cursor.close()
    drizzle_db.close()
    return version


# Database functions
def schemas():
    '''
    Displays the schemas which are already
    present in the Drizzle server

    CLI Example::

        salt '*' drizzle.schemas
    '''

    # Initializing the required variables
    ret_val = {}
    drizzle_db = _connect()
    cursor = drizzle_db.cursor()

    # Retriving the list of schemas
    cursor.execute('SHOW SCHEMAS')
    for iter, count in zip(range(cursor.rowcount),range(1,cursor.rowcount+1)):
        schema = cursor.fetchone()
        ret_val[count] = schema[0]

    cursor.close()
    drizzle_db.close()
    return ret_val


def schema_exists(schema):
    '''
    This method is used to find out whether
    the given schema already exists or not

    CLI Example::

        salt '*' drizzle.schema_exists
    '''

    drizzle_db = _connect()
    cursor = drizzle_db.cursor()

    # Checking for existance
    cursor.execute('SHOW SCHEMAS LIKE "{0}"'.format(schema))
    cursor.fetchall()
    if cursor.rowcount == 1:
        return True
    return False


def schema_create(schema):
    '''
    This method is used to create a schema.
    It takes the name of the schema as argument

    CLI Example::

        salt '*' drizzle.schema_create schema_name
    '''

    drizzle_db = _connect()
    cursor = drizzle_db.cursor()

    # Creating schema
    try:
        cursor.execute('CREATE SCHEMA {0}'.format(schema))
    except MySQLdb.ProgrammingError:
        return 'Schema already exists'

    cursor.close()
    drizzle_db.close()
    return True


def schema_drop(schema):
    '''
    This method is used to drop a schema.
    It takes the name of the schema as argument.

    CLI Example::

        salt '*' drizzle.schema_drop schema_name
    '''

    drizzle_db = _connect()
    cursor = drizzle_db.cursor()

    # Dropping schema
    try:
        cursor.execute('DROP SCHEMA {0}'.format(schema))
    except MySQLdb.OperationalError:
        return 'Schema does not exist'

    cursor.close()
    drizzle_db.close()
    return True


def tables(schema):
    '''
    Displays all the tables that are
    present in the given schema

    CLI Example::

        salt '*' drizzle.tables schema_name
    '''

    # Initializing the required variables
    ret_val = {}
    drizzle_db = _connect()
    cursor = drizzle_db.cursor()

    # Fetching tables
    try:
        cursor.execute('SHOW TABLES IN {0}'.format(schema))
    except MySQLdb.OperationalError:
        return 'Unknown Schema'

    for iter,count in zip(range(cursor.rowcount),range(1,cursor.rowcount+1)):
        table = cursor.fetchone()
        ret_val[count] = table[0]

    cursor.close()
    drizzle_db.close()
    return ret_val


def table_find(table_to_find):
    '''
    Finds the schema in which the
    given table is present

    CLI Example::

        salt '*' drizzle.table_find table_name
    '''

    # Initializing the required variables
    ret_val = {}
    count = 1
    drizzle_db = _connect()
    cursor = drizzle_db.cursor()

    # Finding the schema
    schema = schemas()
    for schema_iter in schema.iterkeys():
        table = tables(schema[schema_iter])
        for table_iter in table.iterkeys():
            if table[table_iter] == table_to_find:
                ret_val[count] = schema[schema_iter]
                count = count+1

    cursor.close()
    drizzle_db.close()
    return ret_val


# Plugin functions
def plugins():
    '''
    Fetches the plugins added to the database server

    CLI Example::

        salt '*' drizzle.plugins
    '''

    # Initializing the required variables
    ret_val = {}
    count = 1
    drizzle_db = _connect()
    cursor = drizzle_db.cursor()

    # Fetching the plugins
    query = 'SELECT PLUGIN_NAME FROM DATA_DICTIONARY.PLUGINS WHERE IS_ACTIVE LIKE "YES"'
    cursor.execute(query)
    for iter,count in zip(range(cursor.rowcount),range(1,cursor.rowcount+1)):
        table = cursor.fetchone()
        ret_val[count] = table[0]

    cursor.close()
    drizzle_db.close()
    return ret_val

#TODO: Needs to add plugin_add() and plugin_remove() methods.
#      However, only some of the plugins are dynamic at the moment.
#      Remaining plugins need the server to be restarted.
#      Hence, these methods can be hacked in the future!


# Query functions
def query(schema, query):
    '''
    Query method is used to issue any query to the database.
    This method also supports multiple queries.

    CLI Example::

        salt '*' drizzle.query test_db 'select * from test_table'
        salt '*' drizzle.query test_db 'insert into test_table values (1,"test1")'
    '''

    # Initializing the required variables
    ret_val = {}
    result = {}
    drizzle_db = _connect()
    cursor = drizzle_db.cursor()
    columns = ()
    rows = ()
    tuples = {}
    queries = []
    _entry = True

    # Support for mutilple queries
    queries = query.split(";")

    # Using the schema
    try:
        cursor.execute('USE {0}'.format(schema))
    except MySQLdb.Error:
        return 'check your schema'

    # Issuing the queries
    for issue in queries:
        try:
            rows_affected = cursor.execute(issue)
        except MySQLdb.Error:
            return 'Error in your SQL statement'

        # Checking whether the query is a SELECT
        if re.search(r'\s*select',issue) is None:
            result['Rows affected:'] = rows_affected
            ret_val[issue.lower()] = result
            result = {}
            continue

        # Fetching the column names
        if _entry:
            attributes = cursor.description
            for column_names in attributes:
                columns += (column_names[0],)
            _entry = False
        result['columns'] = columns

        # Fetching the tuples
        count = 1
        for iter in range(cursor.rowcount):
            row = cursor.fetchone()
            result['row{0}'.format(count)] = row
            count += 1
        result['Rows selected:'] = count-1
        ret_val[issue.lower()] = result
        result = {}

    return ret_val


def ping():
    '''
    Checks whether Drizzle module is loaded or not
    '''
    return True
