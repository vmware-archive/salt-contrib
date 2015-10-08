#!env python
#  -*- coding: utf-8
#
# cmd.py
#
# Provide a VERY simple "shell" that acts as an endpoint for
# a proxy minion connecting over SSH.
#

import os
import cmd
import json

PACKAGES = {'coreutils': '1.05'}
SERVICES = {'apache': 'stopped', 'postgresql': 'stopped',
            'redbull': 'running'}
INFO = {'os': 'SshExampleOS', 'kernel': '0.0000001',
        'housecat': 'Are you kidding?'}

class DumbShell(cmd.Cmd):
    '''
    Implement a "dumb" shell that only handles these commands:
        ps
        start
        stop
        pkg_install
        pkg_remove
        pkg_list
        exit
    '''

    use_rawinput = False

    def emptyline(self):
        pass

    def do_EOF(self, line):
            return True

    def do_ps(self, line):
        print(json.dumps(SERVICES, indent=2))

    def do_info(self, line):
        print(json.dumps(INFO, indent=2))

    def do_status(self, line):
        if SERVICES.get(line, False):
            print(json.dumps({'retcode':0,
                              'message': 'Service {0} is {1}'.format(line, SERVICES[line]) }))
        else:
            print(json.dumps({'retcode': 2,
                              'message': 'Service does not exist' }))

    def do_start(self, line):
        name = line
        if SERVICES.get(name, None) == 'running':
            print(json.dumps({'retcode': 1,
                              'message': 'Service already running' }))
        elif not SERVICES.get(name, None):
            print(json.dumps({'retcode': 2,
                              'message': 'Service does not exist' }))
        else:
            SERVICES[name] = 'running'
            print(json.dumps({'retcode': 0,
                              'message': 'Service started' }))

    def do_restart(self, line):
        name = line
        if SERVICES.get(name, None) == 'running':
            print(json.dumps({'retcode': 0,
                              'message': 'Service was restarted' }))
        elif not SERVICES.get(name, None):
            print(json.dumps({'retcode': 2,
                              'message': 'Service does not exist' }))
        else:
            SERVICES[name] = 'stopped'
            print(json.dumps({'retcode': 1,
                              'message': 'Service was not running, not restarted' }))

    def do_stop(self, line):
        name = line.split()[1]
        if SERVICES.get(name, None) != 'running':
            print(json.dumps({'retcode': 1,
                              'message': 'Service not running' }))
        elif not SERVICES.get(name, None):
            print(json.dumps({'retcode': 2,
                              'message': 'Service does not exist' }))
        else:
            SERVICES[name] = 'stopped'
            print(json.dumps({'retcode': 0,
                              'message': 'Service stopped' }))

    def do_pkg_list(self, line):
        print(json.dumps(PACKAGES, indent=2))

    def do_pkg_install(self, line):

        pkg = line.split()

        if len(pkg) <= 1:
            pkg.append('1.0')

        PACKAGES[pkg[0]] = pkg[1]

        print(json.dumps({'retcode': 0,
                          'message': 'Package {0} {1} installed'.format(pkg[0],pkg[1]) }))

    def do_pkg_remove(self, line):

        if line in PACKAGES:
            PACKAGES.pop(line)
            print(json.dumps({'retcode': 0,
                              'message': 'Package {0} removed'.format(line) }))
        else:
            print(json.dumps({'retcode': 1,
                              'message': 'Package {0} was not installed'.format(line) }))

    def do_pkg_status(self, line):
        if line in PACKAGES:
            print(json.dumps({'retcode': 0,
                              'message': 'Package {0} {1} is present'.format(line, PACKAGES[line]) }))
        else:
            print(json.dumps({'retcode': 1,
                              'message': 'Package {0} is not present'.format(line) }))


    def do_exit(self, line):
        return True

def main():
    DumbShell().cmdloop()

if __name__ == '__main__':
    main()

# @route('/service/status/<name>')
# def index(name):
#     '''
#     Is service running?
#     '''
#     try:
#         return {'comment': SERVICES[name], 'ret': True}
#     except KeyError:
#         return {'comment': 'not present', 'ret': False}
# 
# 
# @route('/service/restart/<name>')
# def index(name):
#     '''
#     Restart a "service"
#     '''
#     if name in SERVICES:
#         SERVICES[name] = 'running'
#         return {'comment': 'restarted', 'ret': True}
#     else:
#         return {'comment': 'restart failed: not present', 'ret': False}
# 
# 
# @route('/ping')
# def index():
#     '''
#     Are you there?
#     '''
#     return {'comment': 'pong', 'ret': True}
# 
# 
# @route('/info')
# def index():
#     '''
#     Return grains
#     '''
#     return INFO
# 
# 
# @route('/id')
# def index():
#     '''
#     Return an id for the salt-master
#     '''
#     return { 'id': 'rest_sample-localhost' }
# 
# 
# @route('/')
# def index():
#     '''
#     Show the status of the server
#     '''
#     services_html = '<table class="table table-bordered">'
#     for s in SERVICES:
#         services_html += '<tr><td>{}</td><td>{}</td></tr>'.format(s,
#                                                                   SERVICES[s])
#     services_html += '</table>'
#     packages_html = '<table class="table table-bordered">'
#     for s in PACKAGES:
#         packages_html += '<tr><td>{}</td><td>{}</td></tr>'.format(s,
#                                                                   PACKAGES[s])
#     packages_html += '</table>'
# 
#     return template('monitor',  packages_html=packages_html,
#                     services_html=services_html)
# 
# 
# @route('/<filename:path>')
# def send_static(filename):
#     '''
#     Serve static files out of the same directory that
#     rest.py is in.
#     '''
#     return static_file(filename, root=os.path.dirname('__file__'))
# 
# 
