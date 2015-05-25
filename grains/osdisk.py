#!/usr/bin/env python
import os

def get_osdisk_stats():
    '''
    Calculates and returns the disk used, available and total capacity
    in gigabytes. Calculations code from:
    http://www.stealthcopter.com/blog/2009/09/python-diskspace/
    '''
    grains = {}
    grains['osdisk'] = {}
    disk = os.statvfs("/")

    capacity = disk.f_bsize * disk.f_blocks
    available = disk.f_bsize * disk.f_bavail
    used = disk.f_bsize * (disk.f_blocks - disk.f_bavail)

    # print information in bytes
    #print used, available, capacity
    # print information in Kilobytes
    #print used/1024, available/1024, capacity/1024
    # print information in Megabytes
    #print used/1.048576e6, available/1.048576e6, capacity/1.048576e6
    # print information in Gigabytes
    #print used/1.073741824e9, available/1.073741824e9, capacity/1.073741824e9

    grains['osdisk']['used'] = int(round(used/1.073741824e9))
    grains['osdisk']['available'] = int(round(available/1.073741824e9))
    grains['osdisk']['capacity'] = int(round(capacity/1.073741824e9))

    return grains
