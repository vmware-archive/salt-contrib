"""
    Return grains information about available hardware RAID controllers.
"""

import subprocess
import re
import platform
import logging


__author__ = "Ivan Adam Vari"
__license__ = "Apache License, Version 2.0"


log = logging.getLogger(__name__)


def _kmod_name(slot_id):
    """
        Return kernel module name used by detected controller. Takes one parameter,
        returns string.

        @slot_id:         (string) pci slot id as returned by lspci
    """

    try:
        cmd = 'lspci -s {0} -k'.format(slot_id)

        kmod = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE).communicate()[0]

        regex = re.compile(r'Kernel\sdriver\sin\suse:\s+(.*)\n')
        match = regex.search(kmod)

        return match.group(1)

    except OSError:
        pass


def _kmod_info(module):
    """
        Return kernel module details used by detected controller. Takes one parameter,
        returns dict.

        @module:           (string) kernel module name as lspci returns
    """

    kmod_info = {}

    try:
        cmd = 'modinfo {0}'.format(module)

        _ = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)

        for line in _.stdout.readlines():
            for field in ['filename', 'version', 'description', 'author']:
                if line.startswith(field):
                    kmod_info.update({'driver_' + field: line.strip().split(' ', 1)[1].strip()})

        if kmod_info:
            return kmod_info

        else:
            log.debug('Unable to fetch kernel module data')

    except OSError:
        pass


def raid_info():
    """
        Return RAID info, takes no parameters, returns dict.
    """

    field_names = ['slot', 'class', 'vendor', 'device', 'rev', 'subsystem_vendor', 'subsystem', 'driver']
    field_values = []

    if platform.system() == 'Linux':
        try:
            hwinfo = subprocess.Popen('lspci -m'.split(), stdout=subprocess.PIPE)

            for line in hwinfo.stdout.readlines():
                if re.search('RAID|Serial Attached SCSI', line):
                    # sanitize the output and load it into a list
                    raw_fields = line.strip().split('"')
                    fields = [field for field in raw_fields if not (field == ' ' or field == '')]
                    field_values = [string.strip().rstrip() for string in fields]
                    # append kmod name to data based on fetched slot id
                    field_values.append(_kmod_name(field_values[0]))

            pci_data = dict(zip(field_names, field_values))

            # for detected cards append kernel module info
            if pci_data:
                try:
                    pci_data.update(_kmod_info(pci_data['driver']))
                    return {'raidcontroller': pci_data}

                except (KeyError):
                    log.debug('No RAID driver found')
                    return {'raidcontroller': pci_data}
            else:
                log.debug('No RAID controllers detected')

        except OSError:
            pass

    else:
        log.debug('Not supported OS "{0}"'.format(platform.system()))

