#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''

wireunlurk

Python script and Salt execution module to detect and remove WireLurker.
Based on WireLurkerDectectorOSX.py by Claud Xiao, Palo Alto Networks and the
bash-based WireLurker cleaner 'killer.sh' by wxzjohn.

https://github.com/PaloAltoNetworks-BD/WireLurkerDetector
https://github.com/wzxjohn/WireLurkerDetector

Usage:

    From the command line:

        wireunlurk.py [-c] [-h]
          -h: Show help

          -c: Clean as well as detect.  Cleaning will move infected files to
              a dynamically determined temporary directory.  Cleaned machines
              should be rebooted after disinfection.

    From Salt:
        
        Drop this file in your master's /srv/salt/_modules directory
        or equivalent and execute a `salt '*' modules.sync_modules`

        then

        General target:
        salt //target// wireunlurk.scan [clean=True]

        Grains based OS match:
        salt -G 'os:MacOS' wireunlurk.scan [clean=True]



License:

Copyright (c) 2014, SaltStack, Inc.
Copyright (c) 2014, Palo Alto Networks, Inc.

Permission to use, copy, modify, and/or distribute this software for any purpose
with or without fee is hereby granted, provided that the above copyright notice
and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS
OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER
TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF
THIS SOFTWARE.
'''

__copyright__    = 'Copyright (c) 2014, SaltStack, Inc and Palo Alto Networks, Inc.'
__author__       = 'C. R. Oldham, wxzjohn, Claud Xiao'
__version__      = '1.0'


import os
import sys
import shutil
import platform
import plistlib
import subprocess
import tempfile
from os.path import expanduser

SALT_RESULT = ''
THIS_IS_SALT = False

try:
    if isinstance(__salt__, dict):
        THIS_IS_SALT = True
        import logging
        log = logging.getLogger(__name__)
except NameError:
    pass

BACKUP_DIR = '/tmp/wirelurker_backup'

MALICIOUS_LAUNCHD_PLISTS = [
    '/Library/LaunchDaemons/com.apple.machook_damon.plist',
    '/Library/LaunchDaemons/com.apple.globalupdate.plist',
    '/Library/LaunchDaemons/com.apple.watchproc.plist',
    '/Library/LaunchDaemons/com.apple.itunesupdate.plist',
    '/System/Library/LaunchDaemons/com.apple.appstore.plughelper.plist',
    '/System/Library/LaunchDaemons/com.apple.MailServiceAgentHelper.plist',
    '/System/Library/LaunchDaemons/com.apple.systemkeychain-helper.plist',
    '/System/Library/LaunchDaemons/com.apple.periodic-dd-mm-yy.plist',
]

MALICIOUS_FILES = [
    '/Users/Shared/run.sh',
    '/usr/bin/globalupdate',
    '/usr/local/machook/',
    '/usr/bin/WatchProc',
    '/usr/bin/itunesupdate',
    '/usr/bin/com.apple.MailServiceAgentHelper',
    '/usr/bin/com.apple.appstore.PluginHelper',
    '/usr/bin/periodicdate',
    '/usr/bin/systemkeychain-helper',
    '/usr/bin/stty5.11.pl',
]

SUSPICIOUS_FILES = [
    '/etc/manpath.d/',
    '/usr/local/ipcc/',
    os.path.join(expanduser('~'), 'Library/Caches/com.maiyadi.appinstaller/'),
    os.path.join(expanduser('~'), 'Library/Saved Application State/com.maiyadi.appinstaller.savedState/'),
]


def _console_print(txt):
    global SALT_RESULT
    if not THIS_IS_SALT:
        print txt,

    SALT_RESULT += txt


def _scan_files(paths):
    results = []

    for f in paths:
        if os.path.exists(f):
            results.append(f)

    return results


def _is_file_hidden(f):
    if not os.path.exists(f) or not os.path.isfile(f):
        return False

    if sys.version_info[0] >= 2 and sys.version_info[2] >= 7 and sys.version_info >= 3:
        return os.stat(f).st_flags.UF_HIDDEN

    else:
        try:
            proc = subprocess.Popen("ls -ldO '%s' | awk '{print $5}'" % f, shell=True, 
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT)
            output = proc.stdout.read()
            proc.communicate()
            return output.find('hidden') != -1

        except Exception as e:
            return False


def _is_app_infected(root):
    try:
        pl = plistlib.readPlist(os.path.join(root, 'Contents', 'Info.plist'))
        be = pl['CFBundleExecutable']
        bundle_exec = os.path.join(root, 'Contents', 'MacOS', be)
        bundle_exec_ = bundle_exec + '_'
        if _is_file_hidden(bundle_exec) and is_file_hidden(bundle_exec_):
            return True

        the_script = os.path.join(root, 'Contents', 'Resources', 'start.sh')
        the_pack = os.path.join(root, 'Contents', 'Resources', 'FontMap1.cfg')
        if _is_file_hidden(the_script) and is_file_hidden(the_pack):
            return True

        the_installer = os.path.join(root, 'Contents', 'MacOS', 'appinstaller')
        the_mal_ipa = os.path.join(root, 'Contents', 'Resources', 'infoplistab')
        if os.path.isfile(the_installer) and os.path.isfile(the_mal_ipa):
            return True

        return False

    except Exception:
        return False


def _scan_app():
    infected_apps = []

    for target in ['/Applications', expanduser('~/Applications')]:
        for root, __, __ in os.walk(target):
            if root.lower().endswith('.app'):
                if _is_app_infected(root):
                    infected_apps.append(root)

    return infected_apps


def _clean_launchd(launchd_plists):

    results = {}
    exit_code = 0
    for pl in launchd_plists:
        try:
            output = subprocess.check_output(['/bin/launchctl', 'unload', pl],
                                            stderr=subprocess.STDOUT).rstrip()
            results[pl] = 'launchctl unload: {0}'.format(output)
        except subprocess.CalledProcessError, e:
            results[pl] = 'launchctl unload: {0}'.format(e.output)
            exit_code = 1
            pass

        try:
            os.unlink(pl)
            if pl in results:
                results[pl] = results[pl] + '; plist rm OK'
            else:
                results[pl] = 'plist rm OK'
        except Exception, e:
            exit_code = 1
            if pl in results:
                results[pl] = results[pl] + '; plist rm: {0}'.format(e.strerror)
            else:
                results[pl] = 'plist rm: {0}'.format(e.strerror)

    return (exit_code, results)


def _clean(mal_files, infected_apps, BACKUP_DIR):

    for f in mal_files:
        shutil.move(f, BACKUP_DIR)
    for a in infected_apps:
        shutil.move(a, BACKUP_DIR)

    return True


def scan(clean=False):

    '''
    Salt execution module to detect and remove WireLurker.


    CLI Example:

        .. code-block:: bash

            salt //target// wireunlurk.scan [clean=False]

    clean
        pass 'clean=True' to clean the infection, if any is found.

    Example results for a non-infected system:

        .. code-block: yaml

            lepto:
                ----------
                retcode:
                    0
                return:
                    Based on WireLurker Detector (1.1.0)
                    Copyright (c) 2014, SaltStack, Inc and Palo Alto Networks, Inc.

                    INFO: Infected files will be backed up to /tmp/wirelurker_bk_wRpapm
                    [+] Scanning for known malicious files ...
                    [-] Nothing is found.
                    [+] Scanning for known malicious launchd plists ...
                    [-] Nothing is found.
                    [+] Scanning for known suspicious files ...
                    [-] Nothing is found.
                    [+] Scanning for infected applications ... (may take minutes)
                    [-] No infected apps found.
                    [+] Your OS X system is not infected by the WireLurker. Thank you!
                success:
                    True

    Example reults for a hypothetical infected system:

        .. code-block: yaml

            lepto:
                ----------
                retcode:
                    0
                return:
                    wireunlurk Detector and cleaner (version 1.0)
                    Based on WireLurker Detector (1.1.0)
                    Copyright (c) 2014, SaltStack, Inc and Palo Alto Networks, Inc.

                    INFO: Infected files will be backed up to /tmp/wirelurker_bk_s6XAMy
                    [+] Scanning for known malicious files ...
                    [!] Found malicious file: /Users/Shared/run.sh
                    [+] Scanning for known malicious launchd plists ...
                    [-] Nothing is found.
                    [+] Scanning for known suspicious files ...
                    [-] Nothing is found.
                    [+] Scanning for infected applications ... (may take minutes)
                    [-] No infected apps found.
                    [+] Cleaning...Malicious files and apps were removed.
                    [!] You should reboot this machine.

                    [!] For more information about the WireLurker, please refer:
                    [!] http://researchcenter.paloaltonetworks.com/2014/11/wirelurker-new-era-os-x-ios-malware/

    '''
    

    global SALT_RESULT
    output = 'wireunlurk Detector and cleaner (version %s)\n' % __version__
    output += 'Based on WireLurker Detector (1.1.0)\n'
    output += __copyright__
    output += '\n\n'

    _console_print(output)

    if platform.system() != 'Darwin':
        output = 'ERROR: The script should only be run in a Mac OS X system.\n'
        _console_print(output)
        if THIS_IS_SALT:
            return SALT_RESULT
        else:
            return -1

    if clean:
        BACKUP_DIR = tempfile.mkdtemp(dir='/tmp', prefix='wirelurker_bk_')
        output = 'INFO: Infected files will be backed up to {0}\n'.format(BACKUP_DIR)
    output += '[+] Scanning for known malicious files ...\n'

    mal_files = _scan_files(MALICIOUS_FILES)
    if len(mal_files) == 0:
        output += '[-] Nothing is found.\n'
    else:
        for f in mal_files:
            output += '[!] Found malicious file: %s\n' % f

    output += '[+] Scanning for known malicious launchd plists ...\n'
    launchd_plists = _scan_files(MALICIOUS_LAUNCHD_PLISTS)

    if len(launchd_plists) == 0:
        output += '[-] Nothing is found.\n'
    else:
        for f in launchd_plists:
            output += '[!] Found malicious launchd plist: %s\n' % f

    output += '[+] Scanning for known suspicious files ...\n'
    _console_print(output)

    sus_files = _scan_files(SUSPICIOUS_FILES)
    if len(sus_files) == 0:
        output = '[-] Nothing is found.\n'
    else:
        for f in sus_files:
            output = '[!] Found suspicious file: %s\n' % f

    _console_print(output)

    output = '[+] Scanning for infected applications ... (may take minutes)\n'
    _console_print(output)

    infected_apps = _scan_app()
    infected_apps = []
    if len(infected_apps) == 0:
        output = '[-] No infected apps found.\n'
        _console_print(output)
    else:
        for a in infected_apps:
            output = '[!] Found infected application: %s\n' % a
            _console_print(output)

    if len(mal_files) == 0 and len(sus_files) == 0 \
       and len(infected_apps) == 0 and len(launchd_plists) == 0:
        output = '[+] Your OS X system is not infected by the WireLurker. Thank you!'
        _console_print(output)
        if clean:
            shutil.rmtree(BACKUP_DIR)
        if not THIS_IS_SALT:
            return 0
        else:
            log.debug('+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
            log.debug(SALT_RESULT)
            return { 'return':SALT_RESULT, 'retcode':0, 'success':True }
    else:
        exit_code = 0
        if clean:
            output = '[+] Cleaning...'
            _console_print(output)

            if _clean(mal_files, infected_apps, BACKUP_DIR):
                output = 'Malicious files and apps were removed.\n'
                _console_print(output)

            plist_exit_code, results = _clean_launchd(launchd_plists)
            if len(results) > 0:
                output = 'Launchd plist results:\n'
                _console_print(output)
                for r in results.iterkeys():
                    output = '{0}: {1}\n'.format(r, results[r])
                    _console_print(output)

            if len(sus_files) > 0:
                output = 'Suspicious files remain.  You should investigate each\n'
                output += 'of these files, on rare occasions they exist for\n'
                output += 'reasons not related to WireLurker\n'
                _console_print(output)
                exit_code = 1

            output = '[!] You should reboot this machine.\n\n'
            output += '[!] For more information about the WireLurker, please refer: \n'
            output += '[!] http://researchcenter.paloaltonetworks.com/2014/11/wirelurker-new-era-os-x-ios-malware/\n'
            _console_print(output)
        else:
            output = 'This system is infected.\n'
            _console_print(output)
            exit_code = 1

        if not THIS_IS_SALT:
            return exit_code
        else:
            log.debug(SALT_RESULT)
            return { 'return':SALT_RESULT, 'retcode':exit_code, 'success':exit_code == 0 }


def usage():

    print '''
Usage:

    From the command line:

        wireunlurk.py [-c] [-h]
          -h: Show help

          -c: Clean as well as detect.  Cleaning will move infected files to
              a dynamically determined temporary directory.  Cleaned machines
              should be rebooted after disinfection.
'''


def main(argv=None):
    if argv is None:
        argv = sys.argv

    if '-h' in argv:
        usage()
        return 0

    return scan(clean='-c' in argv)


if __name__ == '__main__':

    if THIS_IS_SALT:
        sys.exit(main()['retcode'])
    else:
        sys.exit(main())
