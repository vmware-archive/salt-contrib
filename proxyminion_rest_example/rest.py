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
from bottle import route, run, template, static_file, request, Bottle, redirect

app = Bottle()

app.PACKAGES = {'coreutils': '1.05'}
app.UPGRADE_PACKAGES = {}

app.SERVICES = {'apache': 'stopped', 'postgresql': 'stopped',
            'redbull': 'running'}
app.INFO = {'os': 'RestExampleOS', 'kernel': '0.0000001',
        'housecat': 'Are you kidding?'}
app.outage_mode = {'state': False}



@app.route('/package/uptodate')
def index():
    if app.UPGRADE_PACKAGES != {}:
        return app.UPGRADE_PACKAGES

    for k, v in app.PACKAGES.iteritems():
        app.UPGRADE_PACKAGES[k] = str(float(v) + 1)

    return app.UPGRADE_PACKAGES


@app.route('/package/upgrade')
def index():
    if app.UPGRADE_PACKAGES == {}:
        return {}
    else:
        app.PACKAGES = app.UPGRADE_PACKAGES
        app.UPGRADE_PACKAGES = {}
        return app.PACKAGES


@app.route('/package/list')
def index():
    return app.PACKAGES


@app.route('/package/install/<name>/<version>')
def index(name, version):
    '''
    Install a package endpoint
    '''
    app.PACKAGES[name] = version
    return {'comment': 'installed', 'ret': True}


@app.route('/package/remove/<name>')
def index(name):
    '''
    Remove a package endpoint
    '''
    app.PACKAGES.pop(name, None)
    return {'comment': 'removed', 'ret': True}


@app.route('/package/status/<name>')
def index(name):
    '''
    Is packaged installed?
    '''
    try:
        return app.PACKAGES[name]
    except KeyError:
        return {'comment': 'not present', 'ret': False}


@app.route('/service/list')
def index():
    '''
    List services
    '''
    return app.SERVICES


@app.route('/service/start/<name>')
def index(name):
    '''
    Start a service
    '''
    if name in app.SERVICES:
        app.SERVICES[name] = 'running'
        return {'comment': 'running', 'ret': True}
    else:
        return {'comment': 'not present', 'ret': False}


@app.route('/service/stop/<name>')
def index(name):
    '''
    Stop a service
    '''
    if name in app.SERVICES:
        app.SERVICES[name] = 'stopped'
        return {'comment': 'stopped', 'ret': True}
    else:
        return {'comment': 'not present', 'ret': False}


@app.route('/service/status/<name>')
def index(name):
    '''
    Is service running?
    '''
    try:
        return {'comment': app.SERVICES[name], 'ret': True}
    except KeyError:
        return {'comment': 'not present', 'ret': False}


@app.route('/service/restart/<name>')
def index(name):
    '''
    Restart a "service"
    '''
    if name in app.SERVICES:
        app.SERVICES[name] = 'running'
        return {'comment': 'restarted', 'ret': True}
    else:
        return {'comment': 'restart failed: not present', 'ret': False}


@app.route('/ping')
def index():
    '''
    Are you there?
    '''
    return {'comment': 'pong', 'ret': True}


@app.route('/info')
def index():
    '''
    Return grains
    '''
    return INFO


@app.route('/id')
def index():
    '''
    Return an id for the salt-master
    '''
    return { 'id': 'rest_sample-localhost' }


def _get_form():
    '''
    Get the form depending on what state we are in
    '''
    form = None

    if app.outage_mode['state']:
        form = template('fix_outage')
    else:
        form = template('outage')

    return form


def _set_outage_mode(outage):
    if outage:
        app.outage_mode['state'] = True
    else:
        app.outage_mode['state'] = False

def _get_html():

    services_html = '<table class="table table-bordered">'
    for s in app.SERVICES:
        services_html += '<tr><td>{}</td><td>{}</td></tr>'.format(s,
                                                                  app.SERVICES[s])
    services_html += '</table>'
    packages_html = '<table class="table table-bordered">'
    for s in app.PACKAGES:
        packages_html += '<tr><td>{}</td><td>{}</td></tr>'.format(s,
                                                                  app.PACKAGES[s])
    packages_html += '</table>'

    return (services_html, packages_html)

@app.route('/')
def index():
    '''
    Show the status of the server
    '''
    services_html, packages_html = _get_html()
    # services_html = '<table class="table table-bordered">'
    # for s in app.SERVICES:
    #     services_html += '<tr><td>{}</td><td>{}</td></tr>'.format(s,
    #                                                               app.SERVICES[s])
    # services_html += '</table>'
    # packages_html = '<table class="table table-bordered">'
    # for s in app.PACKAGES:
    #     packages_html += '<tr><td>{}</td><td>{}</td></tr>'.format(s,
    #                                                               app.PACKAGES[s])
    # packages_html += '</table>'

    # Always call before _get_form
    # _set_outage_mode(request.query.outage)

    form = _get_form()

    return template('monitor',  packages_html=packages_html,
                    services_html=services_html,
                    form=form)


@app.post('/outage')
def outage():
    app.outage_mode['state'] = not app.outage_mode['state']
    redirect('/')


@app.route('/beacon')
def index():
    '''
    Return outage status
    '''
    return {'outage': app.outage_mode['state']}


@app.route('/fix_outage')
def index():
    '''
    "Fix" the outage
    '''
    app.outage_mode['state'] = False
    return {'outage': app.outage_mode['state']}


@app.route('/<filename:path>')
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
                                     'localhost:8000 to respond to the rest_sample '
                                     'proxy minion')
    parser.add_argument('--address', default='127.0.0.1',
                        help='Start the REST server on this address')
    parser.add_argument('--port', default=8000, type=int,
                        help='Start the REST server on this port')
    args = parser.parse_args()

    # Start the Bottle server
    app.run(host=args.address, port=args.port)


if __name__ == '__main__':
    main()
