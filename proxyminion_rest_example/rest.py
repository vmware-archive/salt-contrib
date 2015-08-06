#!env python
#  -*- coding: utf-8
#
# rest.py
#
# Provide a VERY simple REST endpoint against which a proxy minion can be tested
#
# Requires that the bottle Python packages are available

import argparse
import os
from bottle import route, run, template, static_file

PACKAGES = {'coreutils': '1.05'}
SERVICES = {'apache': 'stopped', 'postgresql': 'stopped',
            'redbull': 'running'}
INFO = {'os': 'RestExampleOS', 'kernel': '0.0000001',
        'housecat': 'Are you kidding?'}


@route('/package/list')
def index():
    return PACKAGES


@route('/package/install/<name>/<version>')
def index(name, version):
    '''
    Install a package endpoint
    '''
    PACKAGES[name] = version
    return {'comment': 'installed', 'ret': True}


@route('/package/remove/<name>')
def index(name):
    '''
    Remove a package endpoint
    '''
    PACKAGES.pop(name, None)
    return {'comment': 'removed', 'ret': True}


@route('/package/status/<name>')
def index(name):
    '''
    Is packaged installed?
    '''
    try:
        return PACKAGES[name]
    except KeyError:
        return {'comment': 'not present', 'ret': False}


@route('/service/list')
def index():
    '''
    List services
    '''
    return SERVICES


@route('/service/start/<name>')
def index(name):
    '''
    Start a service
    '''
    if name in SERVICES:
        SERVICES[name] = 'running'
        return {'comment': 'running', 'ret': True}
    else:
        return {'comment': 'not present', 'ret': False}


@route('/service/stop/<name>')
def index(name):
    '''
    Stop a service
    '''
    if name in SERVICES:
        SERVICES[name] = 'stopped'
        return {'comment': 'stopped', 'ret': True}
    else:
        return {'comment': 'not present', 'ret': False}


@route('/service/status/<name>')
def index(name):
    '''
    Is service running?
    '''
    try:
        return {'comment': SERVICES[name], 'ret': True}
    except KeyError:
        return {'comment': 'not present', 'ret': False}


@route('/service/restart/<name>')
def index(name):
    '''
    Restart a "service"
    '''
    if name in SERVICES:
        SERVICES[name] = 'running'
        return {'comment': 'restarted', 'ret': True}
    else:
        return {'comment': 'restart failed: not present', 'ret': False}


@route('/ping')
def index():
    '''
    Are you there?
    '''
    return {'comment': 'pong', 'ret': True}


@route('/info')
def index():
    '''
    Return grains
    '''
    return INFO


@route('/id')
def index():
    '''
    Return an id for the salt-master
    '''
    return 'rest_sample-localhost'


@route('/')
def index():
    '''
    Show the status of the server
    '''
    services_html = '<table class="table table-bordered">'
    for s in SERVICES:
        services_html += '<tr><td>{}</td><td>{}</td></tr>'.format(s,
                                                                  SERVICES[s])
    services_html += '</table>'
    packages_html = '<table class="table table-bordered">'
    for s in PACKAGES:
        packages_html += '<tr><td>{}</td><td>{}</td></tr>'.format(s,
                                                                  PACKAGES[s])
    packages_html += '</table>'

    return template('monitor',  packages_html=packages_html,
                    services_html=services_html)


@route('/<filename:path>')
def send_static(filename):
    '''
    Serve static files out of the same directory that
    rest.py is in.
    '''
    return static_file(filename, root=os.path.dirname('__file__'))


def main():
    # parse command line options
    parser = argparse.ArgumentParser(description=
                                     'Start a simple REST web service on '
                                     'localhost:8080 to respond to the rest_sample '
                                     'proxy minion')
    parser.add_argument('--address', default='127.0.0.1',
                        help='Start the REST server on this address')
    parser.add_argument('--port', default=8080, type=int,
                        help='Start the REST server on this port')
    args = parser.parse_args()

    # Start the Bottle server
    run(host=args.address, port=args.port)


if __name__ == '__main__':
    main()
