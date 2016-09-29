# -*- coding:utf-8 -*-
import os
import platform

try:
    import wmi
except ImportError:
    pass

def get_osdisk_stats():
    '''
    Calculates and returns the disk used, available and total capacity
    in gigabytes. Calculations code from:
    http://www.stealthcopter.com/blog/2009/09/python-diskspace/
    '''
    grains = {}
    grains['osdisk'] = {}
    if platform.system() == 'Windows':
        WMI = wmi.WMI()
        for disk in WMI.Win32_LogicalDisk():
            if disk.Size:
                available = int(disk.FreeSpace)
                size = int(disk.Size)
                used = size - available
                caption = disk.Caption
                grains['osdisk'][caption] = {'available': round(available/1.073741824e9), 'used': round(used/1.073741824e9)}
    elif platform.system() == 'Linux':
        with open('/proc/mounts', 'r') as f:
            mounts = [line.split()[1] for line in f.readlines()]
        for caption in mounts:
            disk = os.statvfs(caption)
            if disk.f_blocks:
                available = disk.f_bsize * disk.f_bavail
                used = disk.f_bsize * (disk.f_blocks - disk.f_bavail)
                grains['osdisk'][caption] = {'available': int(round(available/1.073741824e9)), 'used': int(round(used/1.073741824e9))}
    return grains

    # print information in bytes
    #print used, available, capacity
    # print information in Kilobytes
    #print used/1024, available/1024, capacity/1024
    # print information in Megabytes
    #print used/1.048576e6, available/1.048576e6, capacity/1.048576e6
    # print information in Gigabytes
    #print used/1.073741824e9, available/1.073741824e9, capacity/1.073741824e9

