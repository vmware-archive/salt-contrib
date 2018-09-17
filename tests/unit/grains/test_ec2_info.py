# -*- coding: utf-8 -*-
'''
    :codeauthor: :email:`Faye Salwin <faye@futureadvisor.com>`
'''

# Import python libs
from __future__ import absolute_import

# Import Salt Testing libs
from salttesting.helpers import ensure_in_syspath
from tests.support.unit import TestCase, skipIf
from tests.support.mock import (
    patch,
    mock_open,
    MagicMock,
    NO_MOCK,
    NO_MOCK_REASON
)

# Import Salt Libs
import salt.grains.ec2_info as ec2_info

@skipIf(NO_MOCK, NO_MOCK_REASON)

def mock_call_aws(url):
    class MockResponse:
        def __init__(self, data, status_code):
            self.data = data
            self.status_code = status_code

        def read(self):
            return self.data

    result = { "latest": { "meta-data": { "first": "value", "second": {}, "third": None}}}
    path = url.split("/")
    path.pop(0)
    val = result
    for k in path:
        if k:
            if isinstance(val, dict):
                if k in val:
                    val = val[k]
                else:
                    return MockResponse("", 404)
            else:
                return MockResponse("", 404)
        else:
            if isinstance(val, dict):
                # return a slash-terminated value if the value is a dictionary
                v = map(lambda k: k+"/" if isinstance(val[k],dict) else k, val)
                return MockResponse("\n".join(v), 200)
            else:
                return MockResponse("", 404)
    if val:
        return MockResponse(val, 200)
    else:
        return MockResponse("", 404)

class Ec2InfoTestCase(TestCase):
    '''
    Test cases for ec2_info
    '''

    def test_mock_call_aws(self):
        self.assertEqual(mock_call_aws("/latest/meta-data/").read(),"second/\nthird\nfirst")
        self.assertEqual(mock_call_aws("/latest/meta-data/second/").read(),"")

    def test__get_ec2_hostinfo(self):
        with patch('salt.grains.ec2_info._call_aws', side_effect=mock_call_aws):
            self.assertEqual(ec2_info._get_ec2_hostinfo(""), {"first": "value", "second": {}, "third": None})

if __name__ == '__main__':
    from integration import run_tests
    run_tests(Ec2InfoTestCase, needs_daemon=False)
