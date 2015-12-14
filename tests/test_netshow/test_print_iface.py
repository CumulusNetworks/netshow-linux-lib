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

import netshow.linux.print_iface as print_iface
import netshowlib.linux.iface as linux_iface
import netshowlib.linux.bridge as linux_bridge
import mock
from asserts import assert_equals, mod_args_generator


class TestPrintIface(object):
    def setup(self):
        iface = linux_iface.Iface('eth22')
        self.piface = print_iface.PrintIface(iface)

    def test_print_list_in_chunks(self):
        portlist = ['eth1.20', 'eth2.20', 'eth3.20', 'eth4.20',
                    'eth13.50', 'eth17.50', 'eth20.50', 'eth21.50',
                    'eth30', 'eth40', 'eth44', 'eth55', 'eth60',
                    'eth70', 'eth80', 'eth90', 'eth100']
        title = 'untagged members'
        strlist = []
        self.piface.print_list_in_chunks(portlist, title, strlist)
        assert_equals(strlist,  ['untagged members: eth1-4.20, eth100, eth13.50, eth17.50',
                                 '    eth20-21.50, eth30, eth40, eth44',
                                 '    eth55, eth60, eth70, eth80',
                                 '    eth90'])

    @mock.patch('netshowlib.linux.iface.Iface.read_from_sys')
    def test_name_with_alias(self, mock_read_from_sys):
        values = {'ifalias': 'meme'}
        mock_read_from_sys.side_effect = mod_args_generator(values)
        _output = self.piface.name
        assert_equals(_output, 'eth22 (meme)')

    @mock.patch('netshowlib.linux.iface.Iface.read_from_sys')
    def test_name_no_alias(self, mock_read_from_sys):
        # when ifalias is none
        mock_read_from_sys.return_value = None
        assert_equals(self.piface.name, 'eth22')

    @mock.patch('netshow.linux.print_iface.PrintIface.cli_header')
    @mock.patch('netshow.linux.print_iface.PrintIface.ip_details')
    @mock.patch('netshow.linux.print_iface.PrintIface.lldp_details')
    @mock.patch('netshow.linux.print_iface.one_line_legend')
    @mock.patch('netshow.linux.print_iface.full_legend')
    def test_cli_output(self, mock_full_legend,
                        mock_one_legend, mock_lldp, mock_ip_details, mock_cli_header):
        mock_lldp.return_value = 'lldp_output\n'
        mock_ip_details.return_value = 'ip details\n'
        mock_cli_header.return_value = 'cli header\n'
        mock_one_legend.return_value = 'one legend\n'
        mock_full_legend.return_value = 'full legend\n'
        _output = self.piface.cli_output()
        assert_equals(_output.split('\n'),
                      ['one legend', 'cli header', 'ip details',
                       'lldp_output', 'full legend', ''])

    @mock.patch('netshow.linux.print_iface.linux_iface.Iface.read_from_sys')
    def test_linkstate(self, mock_read_from_sys):
        # admin down
        values = {'carrier': None, 'operstate': None}
        mock_read_from_sys.side_effect = mod_args_generator(values)
        assert_equals(self.piface.linkstate, 'admdn')
        # down
        values = {'carrier': '0', 'operstate': 'up'}
        mock_read_from_sys.side_effect = mod_args_generator(values)
        assert_equals(self.piface.linkstate, 'dn')
        # up
        self.piface.iface._linkstate = None  # reset linkstate setting
        values = {'carrier': '1', 'operstate': 'up'}
        mock_read_from_sys.side_effect = mod_args_generator(values)
        assert_equals(self.piface.linkstate, 'up')
        # dormant
        values = {'carrier': '1', 'operstate': 'dormant'}
        mock_read_from_sys.side_effect = mod_args_generator(values)
        assert_equals(self.piface.linkstate, 'drmnt')

    @mock.patch('netshow.linux.print_iface.linux_iface.Iface.is_loopback')
    @mock.patch('netshow.linux.print_iface.linux_iface.Iface.is_l3')
    @mock.patch('netshow.linux.print_iface.linux_iface.Iface.is_subint')
    def test_port_category(self, mock_is_subint, mock_is_l3,
                           mock_is_loopback):
        # if l3 is true and is not loopback
        mock_is_loopback.return_value = False
        mock_is_l3.return_value = True
        mock_is_subint.return_value = False
        assert_equals(self.piface.port_category, 'access/l3')
        # if l3/subint is true
        mock_is_l3.return_value = True
        mock_is_subint.return_value = True
        assert_equals(self.piface.port_category, 'subint/l3')
        # if l3 is not true
        mock_is_l3.return_value = False
        assert_equals(self.piface.port_category, 'unknown_int_type')
        # is loopback and of cause l3
        mock_is_l3.return_value = True
        mock_is_loopback.return_value = True
        mock_is_subint.return_value = False
        assert_equals(self.piface.port_category, 'loopback')

    @mock.patch('netshow.linux.print_iface.linux_iface.Iface.read_from_sys')
    def test_speed(self, mock_read_from_sys):
        # 100M
        mock_read_from_sys.return_value = '100'
        assert_equals(self.piface.speed, '100M')

        # 1G
        self.piface.iface._speed = None
        mock_read_from_sys.return_value = '1000'
        assert_equals(self.piface.speed, '1G')

        # 40G
        self.piface.iface._speed = None
        mock_read_from_sys.return_value = '40000'
        assert_equals(self.piface.speed, '40G')

    @mock.patch('netshow.linux.print_iface.linux_iface.Iface.read_from_sys')
    @mock.patch('netshow.linux.print_iface.linux_iface.Iface.check_port_dhcp_assignment')
    def test_summary(self, mock_is_l3, mock_dhcp):
        # if not l3. summary is blank
        mock_is_l3.return_value = False
        assert_equals(self.piface.summary, [''])
        # is l3 but not dhcp
        mock_is_l3.return_value = True
        self.piface.iface.ip_address.ipv4 = ['10.1.1.1/24']
        assert_equals(self.piface.summary, ['ip: 10.1.1.1/24'])
        # is l3 and is dhcp
        self.piface.iface._ip_addr_assign = 1
        assert_equals(self.piface.summary, ['ip: 10.1.1.1/24(dhcp)'])

    @mock.patch('netshow.linux.print_iface.linux_iface.Iface.read_from_sys')
    def test_single_iface_cli_header(self, mock_read_from_sys):
        values = {'carrier': '1', 'operstate': 'up',
                  'address': '11:22:33:44:55:66',
                  'speed': '1000',
                  'mtu': '9000',
                  'ifalias': None}
        mock_read_from_sys.side_effect = mod_args_generator(values)
        _output = self.piface.cli_header()
        assert_equals(_output.split('\n')[0].split(),
                      ['name', 'mac', 'speed', 'mtu', 'mode'])
        assert_equals(_output.split('\n')[2].split(),
                      ['up', 'eth22', '11:22:33:44:55:66', '1G',
                       '9000', 'unknown_int_type'])

    @mock.patch('netshow.linux.print_iface.linux_iface.Iface.is_l3')
    def test_ip_details(self, mock_is_l3):
        # if not l3.. print empty string
        mock_is_l3.return_value = False
        _output = self.piface.ip_details()
        assert_equals(_output, '')
        # if l3, print ip details
        mock_is_l3.return_value = True
        self.piface.iface.ip_address.ipv4 = ['10.1.1.1/32', '10.1.1.2/32',
                                             '10.1.1.3/32', '10.1.1.4/32',
                                             '10.1.1.5/32']
        self.piface.iface.ip_neighbor._all_neighbors = {
            '10.1.1.2': '222',
            '10.1.1.3': '333'}
        _output = self.piface.ip_details()
        _outputtable = _output.split('\n')
        assert_equals(_outputtable[0], 'ip_details')
        assert_equals(_outputtable[2].split(),
                      ['ip:', '10.1.1.1/32,', '10.1.1.2/32,',
                       '10.1.1.3/32,', '10.1.1.4/32'])
        assert_equals(_outputtable[3].split(),
                      ['10.1.1.5/32'])
        assert_equals(_outputtable[4].split(), ['arp_entries:', '2'])

    @mock.patch('netshowlib.linux.lldp.Lldp.run')
    def test_lldp_details(self, mock_lldp):
        mock_lldp.return_value = [{'adj_port': 'eth2',
                                   'adj_hostname': 'switch1'},
                                  {'adj_port': 'eth10',
                                   'adj_hostname': 'switch2'}]
        _output = self.piface.lldp_details()
        _outputtable = _output.split('\n')
        assert_equals(_outputtable[0].split(), ['lldp'])
        assert_equals(_outputtable[2].split(), ['eth22', '====', 'eth2(switch1)'])
        assert_equals(_outputtable[3].split(), ['====', 'eth10(switch2)'])

    @mock.patch('netshowlib.linux.common.read_file_oneline')
    @mock.patch('netshowlib.linux.iface.os.path.exists')
    @mock.patch('netshowlib.linux.common.read_symlink')
    def test_access_summary(self, mock_symlink, mock_os_path,
                            mock_oneline):
        self.piface.iface = linux_bridge.BridgeMember('eth22')
        mock_subint = mock.MagicMock()
        mock_subint.return_value = []
        self.piface.iface.get_sub_interfaces = mock_subint
        # bridgemember is trunk port
        values = {
            '/sys/class/net/eth22/brport': True,
        }
        values2 = {
            '/sys/class/net/eth22/brport/state': '3',
        }
        values3 = {
            '/sys/class/net/eth22/brport/bridge': 'br10',
        }
        mock_symlink.side_effect = mod_args_generator(values3)
        mock_oneline.side_effect = mod_args_generator(values2)
        mock_os_path.side_effect = mod_args_generator(values)
        br10 = linux_bridge.Bridge('br10')
        linux_bridge.BRIDGE_CACHE['br10'] = br10
        _output = self.piface.access_summary()
        # Untagged: br0
        assert_equals(_output, ['untagged: br10'])

    @mock.patch('netshowlib.linux.iface.Iface.is_trunk')
    @mock.patch('netshowlib.linux.bridge.os.listdir')
    @mock.patch('netshowlib.linux.common.read_file_oneline')
    @mock.patch('netshowlib.linux.iface.os.path.exists')
    @mock.patch('netshowlib.linux.common.read_symlink')
    def test_trunk_summary(self, mock_symlink, mock_os_path,
                           mock_oneline, mock_os_listdir,
                           mock_is_trunk):
        mock_is_trunk.return_value = True
        mock_subint = mock.MagicMock()
        mock_subint.return_value = ['eth22.11', 'eth22.20', 'eth22.30']
        self.piface.iface = linux_bridge.BridgeMember('eth22')
        self.piface.iface.get_sub_interfaces = mock_subint
        # bridgemember is trunk port
        values = {
            '/sys/class/net/eth22/brport': True,
            '/sys/class/net/eth22.11/brport': True,
            '/sys/class/net/eth22.20/brport': False,
            '/sys/class/net/eth22.30/brport': True,
        }
        values2 = {
            '/sys/class/net/eth22/brport/state': '3',
            '/sys/class/net/eth22/brport/bridge/bridge/root_port': 'aaa',
            '/sys/class/net/eth22/brport/port_id': 'aaa',
            '/sys/class/net/eth22.11/brport/state': '0',
            '/sys/class/net/eth22.11/brport/bridge/bridge/stp_state': '1',
            '/sys/class/net/eth22.11/brport/bridge/bridge/root_port': 'aaa',
            '/sys/class/net/eth22.11/brport/port_id': 'aaa',
            '/sys/class/net/eth22.30/brport/state': '0',
            '/sys/class/net/eth22.30/brport/bridge/bridge/stp_state': '0'

        }
        values3 = {
            '/sys/class/net/eth22/brport/bridge': 'br10',
            '/sys/class/net/eth22.11/brport/bridge': 'br11',
            '/sys/class/net/eth22.20/brport/bridge': None,
            '/sys/class/net/eth22.30/brport/bridge': 'br30'
        }
        values4 = {
            '/sys/class/net/br30/brif': ['eth22.30'],
            '/sys/class/net/br11/brif': ['eth22.11'],
            '/sys/class/net/br10/brif': ['eth22']
        }

        mock_os_listdir.side_effect = mod_args_generator(values4)
        mock_symlink.side_effect = mod_args_generator(values3)
        mock_oneline.side_effect = mod_args_generator(values2)
        mock_os_path.side_effect = mod_args_generator(values)
        br10 = linux_bridge.Bridge('br10')
        br11 = linux_bridge.Bridge('br11')
        br30 = linux_bridge.Bridge('br30')
        linux_bridge.BRIDGE_CACHE['br10'] = br10
        linux_bridge.BRIDGE_CACHE['br11'] = br11
        linux_bridge.BRIDGE_CACHE['br30'] = br30
        _output = self.piface.trunk_summary()
        assert_equals(_output[1], 'tagged: br11(11), br30(30)')
        assert_equals(_output[2], 'untagged: br10')

    @mock.patch('netshowlib.linux.iface.Iface.read_from_sys')
    def test_abbrev_linksummary(self, mock_read_from_sys):
        values = {'carrier': '1', 'operstate': 'up'}
        mock_read_from_sys.side_effect = mod_args_generator(values)
        assert_equals(self.piface.abbrev_linksummary(self.piface.iface), 'U')
        values = {'carrier': '0', 'operstate': 'down'}
        mock_read_from_sys.side_effect = mod_args_generator(values)
        assert_equals(self.piface.abbrev_linksummary(self.piface.iface), 'D')
