# disable docstring checking
# pylint: disable=C0111
# disable checking no-self-use
# pylint: disable=R0201
# pylint: disable=W0212
# pylint: disable=W0201
# pylint: disable=F0401
import netshowlib.linux.counters as linux_counters
import mock
from asserts import assert_equals


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
