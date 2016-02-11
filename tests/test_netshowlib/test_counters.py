# disable docstring checking
# pylint: disable=C0111
# disable checking no-self-use
# pylint: disable=R0201
# pylint: disable=W0212
# pylint: disable=W0201
# pylint: disable=F0401
import netshowlib.linux.counters as linux_counters
import mock
from asserts import assert_equals, mod_args_generator


class TestLinuxIfaceCounters(object):
    """ Linux Iface  """

    def setup(self):
        """ setup function """
        self.iface_count = linux_counters.IfaceCounters('eth1')

    @mock.patch('netshowlib.linux.common.read_file_oneline')
    def test_getting_rx_bytes(self, mock_read_oneline):
        _receive_bytes = '6000'
        mock_read_oneline.return_value = _receive_bytes
        assert_equals(self.iface_count.rx_bytes(), _receive_bytes)
        mock_read_oneline.assert_called_with('/sys/class/net/eth1/statistics/rx_bytes')

    @mock.patch('netshowlib.linux.common.read_file_oneline')
    @mock.patch('netshowlib.linux.iface.Iface.has_stats')
    @mock.patch('netshowlib.linux.common.portname_list')
    def test_cacheinfo(self, mock_portnamelist, mock_has_stats, mock_read_file):
        values2 = {
            '/sys/class/net/eth1/statistics/rx_packets': '100',
            '/sys/class/net/eth1/statistics/rx_bytes': '200',
            '/sys/class/net/eth1/statistics/rx_errors': '300',
            '/sys/class/net/eth1/statistics/tx_packets': '400',
            '/sys/class/net/eth1/statistics/tx_bytes': '500',
            '/sys/class/net/eth1/statistics/tx_errors': '600'
        }
        mock_read_file.side_effect = mod_args_generator(values2)
        mock_portnamelist.return_value = ['eth1']
        mock_has_stats.return_value = True
        assert_equals(linux_counters.cacheinfo(), {
            'eth1': {
                'rx': {
                    'packets': '100',
                    'errors': '300',
                    'bytes': '200'},
                'tx': {'packets': '400',
                       'errors': '600',
                       'bytes': '500'
                       }
            }
        })
