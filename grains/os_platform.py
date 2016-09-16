#!/usr/bin/env python
import platform

def os_platform_grain():
    '''
        - run "saltutil.sync_grains" command before executing on registered old systems to sync new grain.
        - it gives the "platform" name of existing operating system as a grain (Ex: Linux, FreeBSD etc.)
        - like this:
                  osplatform:
                         Linux
    '''
    p = platform.system()
    os_platform = {'osplatform': p}
    return os_platform
