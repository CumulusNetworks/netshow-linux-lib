# http://pylint-messages.wikidot.com/all-codes
# pylint: disable=R0913
# disable unused argument
# pylint: disable=W0613
# disable docstring checking
# pylint: disable=C0111
# disable checking no-self-use
# pylint: disable=R0201
# pylint: disable=W0212
# disable invalid name
# pylint: disable=C0103
# pylint: disable=F0401
# pylint: disable=E0611
# pylint: disable=W0611

from asserts import assert_equals, mod_args_generator
import netshowlib.linux.cache as linux_cache
import mock
from mock import MagicMock


class TestLinuxCache(object):

    def setup(self):
        self.cache = linux_cache.Cache()

    def test_feature_list(self):
        featurelist = {'ip_neighbor': 'linux',
                       'ip_address': 'linux',
                       'counters': 'linux',
                       'lldp': 'linux'}
        assert_equals(self.cache.feature_list, featurelist)

    @mock.patch('netshowlib.netshowlib.import_module')
    def test_cache_feature_runs(self, mock_import):
        # test if features=None
        mock_ip_addr = MagicMock()
        mock_lldp = MagicMock()
        mock_ip_neighbor = MagicMock()
        mock_counters = MagicMock()
        values = {'netshowlib.linux.ip_address': mock_ip_addr,
                  'netshowlib.linux.lldp': mock_lldp,
                  'netshowlib.linux.counters': mock_counters,
                  'netshowlib.linux.ip_neighbor': mock_ip_neighbor}
        mock_import.side_effect = mod_args_generator(values)
        self.cache.run()
        assert_equals(mock_ip_neighbor.cacheinfo.call_count, 1)
        assert_equals(mock_lldp.cacheinfo.call_count, 1)
        assert_equals(mock_ip_addr.cacheinfo.call_count, 1)
        mock_import.reset_mock()
        # test if features=['ipaddr']
        mock_ipaddr = MagicMock()
        mock_ipaddr.cacheinfo.return_value = 'ip cache info'
        values = {'netshowlib.linux.ip_address': mock_ipaddr}
        mock_import.side_effect = mod_args_generator(values)
        self.cache.run(features={'ip_address': 'linux'})
        assert_equals(
            mock_import.call_args_list,
            [mock.call('netshowlib.linux.ip_address')])
        assert_equals(self.cache.ip_address, 'ip cache info')
