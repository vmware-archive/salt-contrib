# -*- coding: utf-8 -*-
'''
    :codeauthor: Iggy
    :copyright: © 2016 by the SaltStack Community
    :license: Apache 2.0, see LICENSE for more details.

    Load grains from the metadata service in the Vultr cloud provider
        http://vultr.com
        https://discuss.vultr.com/discussion/582/cloud-init-user-data-testing

    This service appears to currently be in flux. If this doesn't work, please
    contact iggy in the #salt irc channel.

    TODO
    Currently opens more connections than I'd like, but there's no way to get
    an all-in-one/recursive response from the metadata service
'''

import logging
import requests

LOG = logging.getLogger(__name__)

MD_BASE_URI = "http://169.254.169.254/current/meta-data/"
__virtualname__ = "vultr"


def __virtual__():
    '''
    We should only load if this is actually a vultr instance
    '''
    try:
        ret = requests.get(MD_BASE_URI + 'mac')
        if ret.content.find(":") <= 0:
            return False
        return __virtualname__
    except Exception as e:
        return False

def vultr():
    '''
    Return Vultr metadata.
    '''
    vultr = {}
    with requests.Session() as sess:
        for i in ['mac', 'instance-id', 'local-ipv4', 'public-ipv4', 'SUBID',
                  'ipv6-addr', 'ipv6-prefix']:
            LOG.debug('Making request to: %s%s', MD_BASE_URI, i)
            vultr[i] = sess.get(MD_BASE_URI + i).content

    return {'vultr': vultr}


if __name__ == '__main__':
    print vultr()
