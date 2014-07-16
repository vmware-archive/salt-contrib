# -*- coding: utf-8 -*-
'''
State module for syslog_ng
==========================

:maintainer:    Tibor Benke <btibi@sch.bme.hu>
:maturity:      new
:depends:       cmd, ps
:platform:      all

Users can generate syslog-ng configuration files from YAML format by using
this module or use plain ones and reload, start, or stop their syslog-ng.

Details
-------

The service module is not available on all system, so this module includes
:mod:`syslog_ng.reloaded <salt.states.syslog_ng.reloaded>`,
:mod:`syslog_ng.stopped <salt.states.syslog_ng.stopped>`,
and :mod:`syslog_ng.started <salt.states.syslog_ng.started>` functions.
If the service module is available on the computers, users should use that.

Syslog-ng can be installed via a package manager or from source. In the
latter case, the syslog-ng and syslog-ng-ctl binaries are not available
from the PATH, so users should set location of the sbin directory with
:mod:`syslog_ng.set_binary_path <salt.states.syslog_ng.set_binary_path>`.

Similarly, users can specify the location of the configuration file with
:mod:`syslog_ng.set_config_file <salt.states.syslog_ng.set_config_file>`, then
the module will use it. If it is not set, syslog-ng use the default
configuration file.

For more information see :doc:`syslog-ng state usage </topics/tutorials/syslog_ng-state-usage>`.

Syslog-ng configuration file format
-----------------------------------

The syntax of a configuration snippet in syslog-ng.conf:

    ..

        object_type object_id {<options>};


These constructions are also called statements. There are options inside of them:

    ..

        option(parameter1, parameter2); option2(parameter1, parameter2);

You can find more information about syslog-ng's configuration syntax in the
Syslog-ng Admin guide: http://www.balabit.com/sites/default/files/documents/syslog-ng-ose-3.5-guides/en/syslog-ng-ose-v3.5-guide-admin/html-single/index.html#syslog-ng.conf.5
'''

from __future__ import generators, print_function, with_statement
import logging


log = logging.getLogger(__name__)


def config(name,
           config,
           write=True):
    '''
    Builds syslog-ng configuration.

    name : the id of the Salt document
    config : the parsed YAML code
    write : if True, it writes  the config into the configuration file,
    otherwise just returns it
    '''
    return __salt__['syslog_ng.config'](name, config, write)


def write_config(name, config, newlines=2):
    '''
    Writes the given parameter config into the config file.
    '''
    return __salt__['syslog_ng.write_config'](name, config, newlines)


def write_version(name):
    '''
    Removes the previous configuration file, then creates a new one and writes the name line.
    '''
    return __salt__['syslog_ng.write_version'](name)


def stopped(name=None):
    '''
    Kills syslog-ng.
    '''
    return __salt__['syslog_ng.stop'](name)


def started(name=None,
            user=None,
            group=None,
            chroot=None,
            caps=None,
            no_caps=False,
            pidfile=None,
            enable_core=False,
            fd_limit=None,
            verbose=False,
            debug=False,
            trace=False,
            yydebug=False,
            persist_file=None,
            control=None,
            worker_threads=None,
            *args,
            **kwargs):
    '''
    Ensures, that syslog-ng is started via the given parameters.

    Users shouldn't use this function, if the service module is available on
    their system.
    '''
    return __salt__['syslog_ng.start'](name=name,
                                       user=user,
                                       group=group,
                                       chroot=chroot,
                                       caps=caps,
                                       no_caps=no_caps,
                                       pidfile=pidfile,
                                       enable_core=enable_core,
                                       fd_limit=fd_limit,
                                       verbose=verbose,
                                       debug=debug,
                                       trace=trace,
                                       yydebug=yydebug,
                                       persist_file=persist_file,
                                       control=control,
                                       worker_threads=worker_threads)


def reloaded(name):
    '''
    Reloads syslog-ng.
    '''
    return __salt__['syslog_ng.reload'](name)