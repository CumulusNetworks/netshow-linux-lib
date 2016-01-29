""" Linux Bond module tests
"""
# disable docstring checking
# pylint: disable=C0111
# disable checking no-self-use
# pylint: disable=R0201
# pylint: disable=W0212
# pylint: disable=W0201
# pylint: disable=F0401
import netshowlib.linux.lacp as linux_lacp
import netshowlib.linux.bond as linux_bond
import netshowlib.linux.bridge as linux_bridge
import netshowlib.linux.common as common
import mock
from mock import MagicMock
from asserts import assert_equals, mod_args_generator
import io


class TestLinuxBondMember(object):
    def setup(self):
        self.bond = linux_bond.Bond('bond0')
        self.iface = linux_bond.BondMember('eth22', master=self.bond)

    def test_showing_master(self):
        assert_equals(self.iface.master, self.bond)


    @mock.patch('netshowlib.linux.iface.Iface.read_from_sys')
    def test_bondstate(self, mock_read_from_sys):
        values = {'carrier': '0', 'operstate': 'down',
                  'bonding/mode': 'active-backup 2'}
        mock_read_from_sys.side_effect = mod_args_generator(values)
        # mock_read_from_sys.return_value = 'active-backup 2'
        # if lacp is not set and linkstate is not up
        assert_equals(self.iface.bondstate, 0)

        # if lacp is not set and linkstate is up
        values = {'carrier': '1', 'operstate': 'up',
                  'bonding/mode': 'active-backup 2'}
        mock_read_from_sys.side_effect = mod_args_generator(values)
        assert_equals(self.iface.bondstate, 1)

        # if lacp is set and agg_id is same
        values = {'carrier': '1', 'operstate': 'up',
                  'bonding/mode': '802.3ad 4'}
        mock_read_from_sys.side_effect = mod_args_generator(values)
        bondingfile = io.open('tests/test_netshowlib/proc_net_bonding_agg_id_match.txt')
        with mock.patch('io.open') as mock_open:
            mock_open.return_value = bondingfile
            assert_equals(self.iface.bondstate, 1)

        # if lacp is set and agg_id is different
        bondingfile = io.open('tests/test_netshowlib/proc_net_bonding_agg_id_no_match.txt')
        with mock.patch('io.open') as mock_open:
            mock_open.return_value = bondingfile
            assert_equals(self.iface.bondstate, 0)

    def test_link_failures(self):
        bondfile = io.open('tests/test_netshowlib/proc_net_bonding_agg_id_match.txt')
        with mock.patch('io.open') as mock_open:
            mock_open.return_value = bondfile
            assert_equals(self.iface.linkfailures, 12)


class TestLinuxBond(object):
    """ Linux bond tests """

    def setup(self):
        """ setup function """
        self.iface = linux_bond.Bond('bond0')

    @mock.patch('netshowlib.linux.bridge.os.listdir')
    @mock.patch('netshowlib.linux.common.read_file_oneline')
    @mock.patch('netshowlib.linux.iface.os.path.exists')
    @mock.patch('netshowlib.linux.common.read_symlink')
    def test_get_vlan_list(self, mock_symlink, mock_os_path,
                           mock_oneline, mock_os_listdir):
        mock_subint = MagicMock()
        mock_subint.return_value = ['bond0.11', 'bond0.20', 'bond0.30']
        self.iface.get_sub_interfaces = mock_subint
        # bridgemember is trunk port
        values = {
            '/sys/class/net/bond0/brport': True,
            '/sys/class/net/bond0.11/brport': True,
            '/sys/class/net/bond0.20/brport': False,
            '/sys/class/net/bond0.30/brport': True,
        }
        values2 = {
            '/sys/class/net/bond0/brport/state': '3',
            '/sys/class/net/bond0/brport/bridge/bridge/root_port': 'aaa',
            '/sys/class/net/bond0/brport/port_id': 'aaa',
            '/sys/class/net/bond0.11/brport/state': '0',
            '/sys/class/net/bond0.11/brport/bridge/bridge/stp_state': '1',
            '/sys/class/net/bond0.11/brport/bridge/bridge/root_port': 'aaa',
            '/sys/class/net/bond0.11/brport/port_id': 'aaa',
            '/sys/class/net/bond0.30/brport/state': '0',
            '/sys/class/net/bond0.30/brport/bridge/bridge/stp_state': '0'

        }
        values3 = {
            '/sys/class/net/bond0/brport/bridge': 'br10',
            '/sys/class/net/bond0.11/brport/bridge': 'br11',
            '/sys/class/net/bond0.20/brport/bridge': None,
            '/sys/class/net/bond0.30/brport/bridge': 'br30'
        }
        values4 = {
            '/sys/class/net/br30/brif': ['bond0.30'],
            '/sys/class/net/br11/brif': ['bond0.11'],
            '/sys/class/net/br10/brif': ['bond0']
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
        vlanlist = self.iface.vlan_list
        assert_equals(vlanlist, {'br30': ['30'], 'br10': ['0'], 'br11': ['11']})

    @mock.patch('netshowlib.linux.bridge.os.listdir')
    @mock.patch('netshowlib.linux.common.read_file_oneline')
    @mock.patch('netshowlib.linux.iface.os.path.exists')
    @mock.patch('netshowlib.linux.common.read_symlink')
    def test_native_vlan(self, mock_symlink, mock_os_path,
                         mock_oneline, mock_os_listdir):
        mock_subint = MagicMock()
        mock_subint.return_value = ['bond0.11', 'bond0.20', 'bond0.30']
        self.iface.get_sub_interfaces = mock_subint
        # bridgemember is trunk port
        values = {
            '/sys/class/net/bond0/brport': True,
            '/sys/class/net/bond0.11/brport': True,
            '/sys/class/net/bond0.20/brport': False,
            '/sys/class/net/bond0.30/brport': True,
        }
        values2 = {
            '/sys/class/net/bond0/brport/state': '3',
            '/sys/class/net/bond0/brport/bridge/bridge/root_port': 'aaa',
            '/sys/class/net/bond0/brport/port_id': 'aaa',
            '/sys/class/net/bond0.11/brport/state': '0',
            '/sys/class/net/bond0.11/brport/bridge/bridge/stp_state': '1',
            '/sys/class/net/bond0.11/brport/bridge/bridge/root_port': 'aaa',
            '/sys/class/net/bond0.11/brport/port_id': 'aaa',
            '/sys/class/net/bond0.30/brport/state': '0',
            '/sys/class/net/bond0.30/brport/bridge/bridge/stp_state': '0'

        }
        values3 = {
            '/sys/class/net/bond0/brport/bridge': 'br10',
            '/sys/class/net/bond0.11/brport/bridge': 'br11',
            '/sys/class/net/bond0.20/brport/bridge': None,
            '/sys/class/net/bond0.30/brport/bridge': 'br30'
        }
        values4 = {
            '/sys/class/net/br30/brif': ['bond0.30'],
            '/sys/class/net/br11/brif': ['bond0.11'],
            '/sys/class/net/br10/brif': ['bond0']
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
        vlanlist = self.iface.native_vlan
        assert_equals(vlanlist, ['br10'])

    @mock.patch('netshowlib.linux.common.read_file_oneline')
    @mock.patch('netshowlib.linux.iface.os.path.exists')
    @mock.patch('netshowlib.linux.common.read_symlink')
    def test_get_bridge_masters(self, mock_symlink, mock_os_path,
                                mock_oneline):
        mock_subint = MagicMock()
        mock_subint.return_value = ['bond0.11', 'bond0.20', 'bond0.30']
        self.iface.get_sub_interfaces = mock_subint
        # bridgemember is trunk port
        values = {
            '/sys/class/net/bond0/brport': True,
            '/sys/class/net/bond0.11/brport': True,
            '/sys/class/net/bond0.20/brport': False,
            '/sys/class/net/bond0.30/brport': True,
        }
        values2 = {
            '/sys/class/net/bond0/brport/state': '3',
            '/sys/class/net/bond0/brport/bridge/bridge/root_port': 'aaa',
            '/sys/class/net/bond0/brport/port_id': 'aaa',
            '/sys/class/net/bond0.11/brport/state': '0',
            '/sys/class/net/bond0.11/brport/bridge/bridge/stp_state': '1',
            '/sys/class/net/bond0.11/brport/bridge/bridge/root_port': 'aaa',
            '/sys/class/net/bond0.11/brport/port_id': 'aaa',
            '/sys/class/net/bond0.30/brport/state': '0',
            '/sys/class/net/bond0.30/brport/bridge/bridge/stp_state': '0'

        }
        values3 = {
            '/sys/class/net/bond0/brport/bridge': 'br10',
            '/sys/class/net/bond0.11/brport/bridge': 'br11',
            '/sys/class/net/bond0.20/brport/bridge': None,
            '/sys/class/net/bond0.30/brport/bridge': 'br30'
        }
        mock_symlink.side_effect = mod_args_generator(values3)
        mock_oneline.side_effect = mod_args_generator(values2)
        mock_os_path.side_effect = mod_args_generator(values)
        br10 = linux_bridge.Bridge('br10')
        br11 = linux_bridge.Bridge('br11')
        br30 = linux_bridge.Bridge('br30')
        linux_bridge.BRIDGE_CACHE['br10'] = br10
        linux_bridge.BRIDGE_CACHE['br11'] = br11
        linux_bridge.BRIDGE_CACHE['br30'] = br30
        assert_equals(sorted(list(self.iface.bridge_masters.keys())),
                      ['br10', 'br11', 'br30'])

    @mock.patch('netshowlib.linux.common.read_file_oneline')
    def test_getting_bond_members(self, mock_file_oneline):
        bondmems = 'swp8 swp9'
        # If bond slaves exists
        mock_file_oneline.return_value = bondmems
        assert_equals(sorted(list(self.iface.members.keys())), ['swp8', 'swp9'])
        # make sure that master bond is the right one and not autogenerated
        assert_equals(self.iface.members.get('swp8').master, self.iface)
        mock_file_oneline.assert_called_with(
            '/sys/class/net/bond0/bonding/slaves')
        # If bond slaves do not exist
        mock_file_oneline.return_value = None
        assert_equals(self.iface.members, {})

    @mock.patch('netshowlib.linux.common.read_file_oneline')
    def test_get_bond_mode(self, mock_file_oneline):
        mock_file_oneline.return_value = '802.3ad 4'
        assert_equals(self.iface.mode, '4')
        mock_file_oneline.assert_called_with(
            '/sys/class/net/bond0/bonding/mode')
        # test failing to find something
        mock_file_oneline.return_value = None
        assert_equals(self.iface.mode, None)

    @mock.patch('netshowlib.linux.common.read_file_oneline')
    def test_getting_min_links(self, mock_file_oneline):
        mock_file_oneline.return_value = '3'
        assert_equals(self.iface.min_links, '3')
        mock_file_oneline.assert_called_with(
            '/sys/class/net/bond0/bonding/min_links')

    @mock.patch('netshowlib.linux.common.read_file_oneline')
    def test_get_bond_xmit_hash_policy(self, mock_file_oneline):
        mock_file_oneline.return_value = 'layer3+4 1'
        assert_equals(self.iface.hash_policy, '1')
        mock_file_oneline.assert_called_with(
            '/sys/class/net/bond0/bonding/xmit_hash_policy')
        # test failing to find something
        mock_file_oneline.return_value = None
        assert_equals(self.iface.hash_policy, None)

    @mock.patch('netshowlib.linux.common.read_file_oneline')
    def test_get_lacp_instance(self, mock_file_oneline):
        # test that calling iface.lacp and if iface is LACP
        # creates new Lacp instance
        mock_file_oneline.return_value = '802.3ad 4'
        assert_equals(isinstance(self.iface.lacp, linux_lacp.Lacp), True)
        mock_file_oneline.assert_called_with(
            '/sys/class/net/bond0/bonding/mode')
        # if bond is not using lacp
        mock_file_oneline.return_value = 'active-backup 1'
        assert_equals(self.iface.lacp, None)

    def test_getting_system_mac(self):
        bondingfile = io.open('tests/test_netshowlib/proc_net_bonding.txt')
        with mock.patch('io.open') as mock_open:
            mock_open.return_value = bondingfile
            assert_equals(self.iface.system_mac, '00:02:00:22:11:33')
