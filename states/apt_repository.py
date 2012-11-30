# -*- coding: utf-8 -*-
# author: Bruno Clermont <patate@fastmail.cn>

'''
APT repository states
=====================

Handle Debian, Ubuntu and other Debian based distribution APT repositories

'''

import urlparse

from salt import exceptions, utils

def __virtual__():
    '''
    Verify apt is installed.
    '''
    try:
        utils.check_or_die('apt-key')
        return 'apt_repository'
    except exceptions.CommandNotFoundError:
        return False

def present(address, components, distribution=None, source=False, key_id=None,
            key_server=None, in_sources_list_d=True, filename=None):
    '''
    Manage a APT repository such as an Ubuntu PPA

    .. code-block:: yaml

    rabbitmq-server:
      apt_repository:
        - present
        - address: http://www.rabbitmq.com/debian/
        - components:
          - main
        - distribution: testing
        - key_server: pgp.mit.edu
        - key_id: 056E8E56

    address
        Repository address, usually a HTTP or HTTPs URL

    components
        List of repository components, such as 'main'

    distribution:
        Set this to use a different distribution than the one the host that run
        this state.

    source
        Add source "deb-src" statement? not the default.

    key_id
        GnuPG/PGP key ID used to authenticate packages of this repository.

    key_server
        The address of the PGP key server.
        This argument is ignored if key_id is unset.

    in_sources_list_d
        In many distribution, there is a directory /etc/apt/sources.list.d/
        that is included when you run apt-get command.
        Create a file there instead of change /etc/apt/sources.list
        This is used by default.
    '''
    if distribution is None:
        distribution = __salt__['grains.item']('oscodename')

    if filename is None:
        url = urlparse.urlparse(address)
        if not url.scheme:
            return {'name': address, 'result': False, 'changes': {},
                    'comment': "Invalid address '{0}'".format(address)}
        filename = '-'.join((
            url.netloc.split(':')[0], # address without port
            url.path.lstrip('/').replace('/', '_'), # path with _ instead of /
            distribution
            ))

    # deb http://ppa.launchpad.net/mercurial-ppa/releases/ubuntu precise main
    # without the deb
    line_content = [address, distribution]
    line_content.extend(components)

    if in_sources_list_d:
        apt_file = '/etc/apt/sources.list.d/{0}.list'.format(filename)
    else:
        apt_file = '/etc/apt/sources.list'

    text = [' '.join(['deb'] + line_content)]
    if source:
        text.append(' '.join(['deb-src'] + line_content))

    data = {
        filename: {
            'file': [
                'append',
                {
                    'name': apt_file
                },
                {
                    'text': text
                },
                {
                    'makedirs': True
                }
            ]
        }
    }

    if key_id:
        add_command = ['apt-key', 'adv', '--recv-keys']
        if key_server:
            add_command.extend(['--keyserver', key_server])
        add_command.extend([key_id])
        data[filename]['cmd'] = [
            'run',
            {'name': ' '.join(add_command)},
            {'unless': 'apt-key list | grep -q {0}'.format(key_id)}
        ]

    output = __salt__['state.high'](data)
    file_result, cmd_result = output.values()

    ret = {
        'name': filename,
        'result': file_result['result'] == cmd_result['result'] == True,
        'changes': file_result['changes'],
        'comment': ' and '.join((file_result['comment'], cmd_result['comment']))
    }
    if ret['result'] and ret['changes']:
        __salt__['pkg.refresh_db']
    ret['changes'].update(cmd_result['changes'])
    return ret

def ubuntu_ppa(user, name, key_id, source=False, distribution=None):
    '''
    Manage an Ubuntu PPA repository

    user
        Launchpad username

    name
        Repository name owned by this user

    key_id
        Launchpad PGP key ID

    source
        Add source "deb-src" statement? not the default.

    distribution:
        Set this to use a different Ubuntu distribution than the host that run
        this state.

    For this PPA: https://launchpad.net/~pitti/+archive/postgresql
    the state must be:

    .. code-block:: yaml

        postgresql:
          apt_repository.ubuntu_ppa:
            - user: pitti
            - name: postgresql
            - key_id: 8683D8A2
    '''
    address = 'http://ppa.launchpad.net/{0}/{1}/ubuntu'.format(user, name)
    filename = '{0}-{1}-{2}'.format(
        user, name,
        __salt__['grains.item']('lsb_codename'))
    return present(address, ('main',), distribution, source, key_id,
                   'keyserver.ubuntu.com', True, filename)
