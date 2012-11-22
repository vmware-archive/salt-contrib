'''
Parse EXIF data from images using exiv2
'''

import salt.utils


def __virtual__():
    '''
    Only load the module if bluetooth is installed
    '''
    if salt.utils.which('exiv2'):
        return 'image'
    return False


def exif(image):
    '''
    Parse EXIF data from image file

    CLI Example::

        salt '*' image.exif /path/to/filename.jpg
    '''
    cmd = 'exiv2 {0}'.format(image)
    out = __salt__['cmd.run'](cmd).split('\n')
    ret = {}
    for line in out:
        comps = line.split(':')
        ret[comps[0].strip()] = comps[1].strip()
    return ret

