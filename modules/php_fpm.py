#!/usr/bin/python
'''
Get varyous php fpm statistic
'''

import flup_fcgi_client as fcgi_client
import salt.utils
from os import listdir
from ConfigParser import ConfigParser

def ping(baseConfigPath = None):
    '''
    Just used to make sure the php-fpm pool is up and responding
    Return PHP FPM status (UP/DOWN)

    CLI Example::

        salt '*' php_fpm.ping
        salt '*' php_fpm.ping baseConfigPath = '/etc/php5/fpm/pool.d/'
    '''

    config = _detect_fpm_configuration(baseConfigPath)
    result = []
    if len(config.sections()) == 0:
        result.append('Can not read PHP FPM config')    
    else:
        for pool_name in config.sections():
            if not config.has_option(pool_name, 'ping.path'):
                result.append('Ping path is not configured for pool:' + pool_name)    
            else:
                code, headers, out, err = _make_fcgi_request(config, pool_name, config.get(pool_name, 'ping.path'))

                response = 'pong'
                if config.has_option(pool_name, 'ping.response'):
                    response = config.get(pool_name, 'ping.response')
                
                if code.startswith('200') and out == response:
                    result.append('Pool: ' + pool_name + ' is UP')
                else:
                    result.append('Pool: ' + pool_name + ' is DOWN')

    return "\n".join(result)


def status(baseConfigPath=None):
    '''
    Try to get php-fpm real time statistic (if its available)
    Return PHP realtime statistic

    CLI Example::

        salt '*' php_fpm.status
        salt '*' php_fpm.status baseConfigPath = '/etc/php5/fpm/pool.d/'
    '''
    
    config = _detect_fpm_configuration(baseConfigPath)
    result = []
    if len(config.sections()) == 0:
        result.append('Can not read PHP FPM config')    
    else:
        for pool_name in config.sections():
            if not config.has_option(pool_name, 'pm.status_path'):
                result.append('Status path is not configured for pool:' + pool_name)    
            else:
                code, headers, out, err = _make_fcgi_request(config, pool_name, config.get(pool_name, 'pm.status_path'))
                if code.startswith('200'):
                    result.append(out)
                else:
                    result.append('Can not get PHP FPM status')    
    return "\n".join(result)

@salt.utils.memoize
def _detect_fpm_configuration(basePath):
    """ try to read php fpm config """
    configFiles = []

    if basePath is None:
        basePath = '/etc/php5/fpm/pool.d/'
    
    dirList= listdir(basePath)
    for fname in dirList:
        if fname[-5:] != '.conf':
            continue
        configFiles.append(basePath + fname)

    config = ConfigParser()
    config.read(configFiles)
    
    return config


def _make_fcgi_request(config, section, request_path):
    """ load fastcgi page """
    try:
        listen = config.get(section, 'listen')
        if listen[0] == '/': 
            #its unix socket
            fcgi = fcgi_client.FCGIApp(connect = listen)
        else:
            if listen.find(':') != -1:
                _listen = listen.split(':') 
                fcgi = fcgi_client.FCGIApp(host = _listen[0], port = _listen[1])
            else:
                fcgi = fcgi_client.FCGIApp(port = listen, host = '127.0.0.1')
            
        env = {
           'SCRIPT_FILENAME': request_path,
           'QUERY_STRING': '',
           'REQUEST_METHOD': 'GET',
           'SCRIPT_NAME': request_path,
           'REQUEST_URI': request_path,
           'GATEWAY_INTERFACE': 'CGI/1.1',
           'SERVER_SOFTWARE': 'ztc',
           'REDIRECT_STATUS': '200',
           'CONTENT_TYPE': '',
           'CONTENT_LENGTH': '0',
           #'DOCUMENT_URI': url,
           'DOCUMENT_ROOT': '/',
           'DOCUMENT_ROOT': '/var/www/'
           }
        ret = fcgi(env)
        return ret
    except Exception as e:
        print str(e)
        print "exception "
        return '500', [], '', str(e)

if __name__ == '__main__':
    print ping()
