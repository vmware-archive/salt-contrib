# -*- coding: utf-8 -*-
'''
    :synopsis: Unit Tests for OctopusDeploy Tentacle Module 'modules.octopus_tentacle'
    :platform: Windows
    :maturity: develop
'''

# Import Python Libs
from __future__ import absolute_import

# Import Salt Libs
from salt.modules import octopus_tentacle

# Import Salt Testing Libs
from salttesting import TestCase, skipIf
from salttesting.helpers import ensure_in_syspath
from salttesting.mock import (
    MagicMock,
    mock_open,
    patch,
    NO_MOCK,
    NO_MOCK_REASON,
)

ensure_in_syspath('../../')

# Globals
octopus_tentacle.__salt__ = {}

# Make sure this module runs on Windows system
HAS_TENTACLE = octopus_tentacle.__virtual__()

DEFAULT_CONFIG_PATH = r'C:\Octopus\Tentacle\Tentacle.config'
EXE_PATH = r'C:\Program Files\Octopus Deploy\Tentacle\Tentacle.exe'

CONFIG_DICT = {
    'app_path': r'C:\Octopus\Applications',
    'home_path': r'C:\Octopus',
    'port': 10933,
    'servers': [{
        'Address': None,
        'CommunicationStyle': 'TentaclePassive',
        'Squid': 'SQ-TEST01-FFFF9999',
        'Thumbprint': '9988776655443322111000AAABBBCCCDDDEEEFFF',
    }],
    'squid': 'SQ-TEST01-AAAA0000',
    'thumbprint': '9988776655443322111000AAABBBCCCDDDEEEFFF',
}
FILE_CONTENT = r'''<?xml version="1.0" encoding="utf-8"?>
<octopus-settings xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <set key="Octopus.Communications.Squid">SQ-TEST01-AAAA0000</set>
  <set key="Octopus.Home">C:\Octopus</set>
  <set key="Tentacle.CertificateThumbprint">9988776655443322111000AAABBBCCCDDDEEEFFF</set>
  <set key="Tentacle.Communication.TrustedOctopusServers">[{"Thumbprint":"9988776655443322111000AAABBBCCCDDDEEEFFF","CommunicationStyle":"TentaclePassive","Address":null,"Squid":"SQ-TEST01-FFFF9999"}]</set>
  <set key="Tentacle.Deployment.ApplicationDirectory">C:\Octopus\Applications</set>
  <set key="Tentacle.Services.PortNumber">10933</set>
</octopus-settings>'''


@skipIf(not HAS_TENTACLE, 'This test case runs only on Windows systems')
@skipIf(NO_MOCK, NO_MOCK_REASON)
class OctopusTentacleTestCase(TestCase):
    '''
    Test cases for salt.modules.octopus_tentacle
    '''

    @patch('salt.modules.octopus_tentacle._get_version',
           MagicMock(return_value='2.5.12.666'))
    def test_version_is_3_or_newer(self):
        '''
        Test - Determine if the Tentacle executable version is 3.0 or newer.
        '''
        with patch.dict(octopus_tentacle.__salt__):
            self.assertFalse(octopus_tentacle.version_is_3_or_newer())

    def test_get_comms_styles(self):
        '''
        Test - Determine the available communication styles.
        '''
        comms_styles = set(['TentacleActive', 'TentaclePassive'])
        with patch.dict(octopus_tentacle.__salt__):
            self.assertEqual(set(octopus_tentacle.get_comms_styles()),
                             comms_styles)

    def test_get_config_path(self):
        '''
        Test - Determine the configuration file used for the provided instance.
        '''
        mock_value = MagicMock(return_value={'vdata': DEFAULT_CONFIG_PATH})
        with patch.dict(octopus_tentacle.__salt__, {'reg.read_value': mock_value}):
            self.assertEqual(octopus_tentacle.get_config_path(),
                             DEFAULT_CONFIG_PATH)

    @patch('salt.modules.octopus_tentacle._get_exe_path',
           MagicMock(return_value=EXE_PATH))
    @patch('salt.modules.octopus_tentacle.get_config_path',
           MagicMock(return_value=DEFAULT_CONFIG_PATH))
    @patch('os.path.isfile',
           MagicMock(return_value=False))
    def test_set_config_path(self):
        '''
        Test - Manage the configuration file for the provided instance.
        '''
        mock_cmd = MagicMock(return_value={'retcode': 0})
        with patch.dict(octopus_tentacle.__salt__, {'cmd.run_all': mock_cmd}):
            self.assertTrue(octopus_tentacle.set_config_path(r'C:\Test.config'))

    @patch('salt.modules.octopus_tentacle.get_config_path',
           MagicMock(return_value=DEFAULT_CONFIG_PATH))
    @patch('os.path.isfile',
           MagicMock(return_value=True))
    @patch('salt.utils.fopen',
           mock_open(read_data=FILE_CONTENT))
    def test_get_config(self):
        '''
        Test - Determine the configuration of the provided instance.
        '''
        with patch.dict(octopus_tentacle.__salt__):
            self.assertEqual(octopus_tentacle.get_config(),
                             CONFIG_DICT)

    @patch('salt.modules.octopus_tentacle._get_exe_path',
           MagicMock(return_value=EXE_PATH))
    @patch('salt.modules.octopus_tentacle.version_is_3_or_newer',
           MagicMock(return_value=False))
    @patch('salt.modules.octopus_tentacle.get_config',
           MagicMock(return_value=CONFIG_DICT))
    @patch('salt.modules.octopus_tentacle.get_config_path',
           MagicMock(return_value=DEFAULT_CONFIG_PATH))
    @patch('salt.modules.octopus_tentacle.set_cert',
           MagicMock(return_value=True))
    @patch('salt.modules.octopus_tentacle.set_squid',
           MagicMock(return_value=True))
    def test_set_config(self):
        '''
        Test - Manage the application configuration of the provided instance.
        '''
        mock_cmd = MagicMock(return_value={'retcode': 0})
        with patch.dict(octopus_tentacle.__salt__, {'cmd.run_all': mock_cmd}):
            self.assertTrue(octopus_tentacle.set_config())

    @patch('salt.modules.octopus_tentacle._get_exe_path',
           MagicMock(return_value=EXE_PATH))
    @patch('salt.modules.octopus_tentacle.get_config',
           MagicMock(return_value=CONFIG_DICT))
    def test_set_cert(self):
        '''
        Test - Generate a tentacle certificate for the provided instance.
        '''
        mock_cmd = MagicMock(return_value={'retcode': 0})
        with patch.dict(octopus_tentacle.__salt__, {'cmd.run_all': mock_cmd}):
            self.assertTrue(octopus_tentacle.set_cert())

    @patch('salt.modules.octopus_tentacle._get_exe_path',
           MagicMock(return_value=EXE_PATH))
    @patch('salt.modules.octopus_tentacle.version_is_3_or_newer',
           MagicMock(return_value=False))
    @patch('salt.modules.octopus_tentacle.get_config',
           MagicMock(return_value=CONFIG_DICT))
    def test_set_squid(self):
        '''
        Test - Manage the SQUID of the provided instance.
        '''
        mock_cmd = MagicMock(return_value={'retcode': 0})
        with patch.dict(octopus_tentacle.__salt__, {'cmd.run_all': mock_cmd}):
            self.assertTrue(octopus_tentacle.set_squid())

    @patch('salt.modules.octopus_tentacle._get_exe_path',
           MagicMock(return_value=EXE_PATH))
    @patch('salt.modules.octopus_tentacle.get_config',
           MagicMock(return_value=CONFIG_DICT))
    def test_set_trust(self):
        '''
        Test - Manage the server thumbprint trust of the provided instance.
        '''
        mock_cmd = MagicMock(return_value={'retcode': 0})
        with patch.dict(octopus_tentacle.__salt__, {'cmd.run_all': mock_cmd}):
            self.assertTrue(octopus_tentacle.set_trust('FFFEEEDDDCCCBBBAAA0001112233445566778899'))

if __name__ == '__main__':
    from integration import run_tests  # pylint: disable=import-error
    run_tests(OctopusTentacleTestCase, needs_daemon=False)
