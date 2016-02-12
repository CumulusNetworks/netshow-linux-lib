# http://pylint-messages.wikidot.com/all-codes
# attribute defined outside init
# pylint: disable=W0201
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
import netshow.linux.show_counters as show_counters
import mock


class TestShowCounters(object):

    @mock.patch('netshow.linux.print_iface.linux_iface.Iface.read_from_sys')
    @mock.patch('netshow.linux.print_iface.linux_iface.Iface.exists')
    @mock.patch('netshow.linux.show_counters.nn.portname_list')
    @mock.patch('netshow.linux.show_counters.linux_cache.Cache')
    def test_show_counters_cli(self, mock_cache, mock_portlist,
                               mock_port_exists, mock_read_from_sys):
        values = {
            'carrier': '1',
            'operstate': 'up',
            'speed': '1000',
            'ifalias': None
            }
        mock_read_from_sys.side_effect = mod_args_generator(values)
        mock_port_exists.return_value = True
        mock_portlist.return_value = ['eth20', 'eth2', 'eth3']
        cache_mock = mock.MagicMock()
        counters_mock = {
            'eth20': {
                'tx': {
                    'errors': 100, 'packets': 100, 'bytes': 100
                },
                'rx': {
                    'errors': 100, 'packets': 100, 'bytes': 100
                }
            }
        }
        cache_mock.__dict__['counters'] = counters_mock
        mock_cache.return_value = cache_mock
        test_counters = show_counters.ShowCounters({})
        output = test_counters.run()
        splitlines = output.splitlines()
        assert_equals(splitlines[3].split(),
                      ['port', 'speed', 'mode', 'packets', 'errors'])
        assert_equals(splitlines[5].split(),
                      ['up', 'eth20', '1G', 'access/l3',
                       'rx', '100', '100'])
        assert_equals(splitlines[6].split(),
                      ['tx', '100', '100'])
