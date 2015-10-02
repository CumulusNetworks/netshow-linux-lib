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

from collections import OrderedDict
from asserts import assert_equals, mod_args_generator
import netshowlib.linux.iface as linux_iface
import netshow.linux.show_interfaces as showint
import netshow.linux.print_bridge as print_bridge
import netshow.linux.print_bond as print_bond
import netshow.linux.print_iface as print_iface
import mock
import re
import json


class TestShowInterfaces(object):

    def setup(self):
        results = {'l2': True}
        self.showint = showint.ShowInterfaces(results)

    @mock.patch('netshowlib.linux.lldp.Lldp.run')
    @mock.patch('netshowlib.linux.common.read_file_oneline')
    @mock.patch('netshowlib.linux.iface.Iface.read_from_sys')
    def test_append_details(self, mock_read_from_sys, mock_file_oneline,
                            mock_lldp):
        values1 = {'carrier': '1',
                   'operstate': 'up',
                   'speed': '1000',
                   'ifalias': 'Blah',
                   'mtu': '1000',
                   'address': '00:11:22:33:44:55'}
        iface = linux_iface.Iface('eth22')
        piface = print_iface.PrintIface(iface)
        mock_read_from_sys.side_effect = mod_args_generator(values1)
        self.showint.show_mac = True
        results = self.showint.cli_append_oneline(piface)
        assert_equals(results, [['up', 'eth22 (Blah)',
                                '00:11:22:33:44:55', '1G',
                                '1000', 'unknown_int_type', '']])

    @mock.patch('netshowlib.linux.iface.portname_list')
    @mock.patch('netshow.linux.print_iface.linux_iface.Iface.exists')
    def test_multiple_ifaces_show_only_up(self, mock_exists,
                                          mock_portname_list):
        # test that when 'netshow interface' is run
        # that only interfaces that are UP are shown
        mock_portname_list.return_value = ['eth10', 'eth11']
        mock_exists.return_value = True
        self.showint.show_l2 = False
        assert_equals(self.showint.show_up, True)
        with mock.patch('netshowlib.linux.iface.Iface.linkstate',
                        new_callable=mock.PropertyMock) as mock_linkstate:
            mock_linkstate.return_value = 2
            self.showint.show_l2 = False
            _output = self.showint.print_many_ifaces(),
            _otable = _output[0].split('\n')

            assert_equals(len(_otable), 7)

        with mock.patch('netshowlib.linux.iface.Iface.linkstate',
                        new_callable=mock.PropertyMock) as mock_linkstate:
            mock_linkstate.return_value = 0
            self.showint._ifacelist = {'all': OrderedDict()}
            _output = self.showint.print_many_ifaces(),
            _otable = _output[0].split('\n')
            assert_equals(len(_otable), 5)



    @mock.patch('netshow.linux.print_iface.linux_iface.Iface.exists')
    @mock.patch('netshow.linux.show_interfaces.linux_iface.portname_list')
    @mock.patch('netshow.linux.show_interfaces.linux_cache.Cache')
    @mock.patch('netshow.linux.print_iface.linux_iface.Iface.is_bridgemem')
    def test_ifacelist_l2_subints(self, mock_bridgemem_test,
                                  mock_cache, mock_portname_list, mock_exists):
        mock_exists.return_value = True
        # make sure L2 subints don't get into the list
        mock_bridgemem_test.return_value = True
        mock_portname_list.return_value = ['eth1.1', 'eth2.1']
        assert_equals(self.showint.ifacelist.get('all'), OrderedDict())

    @mock.patch('netshow.linux.print_iface.linux_iface.Iface.exists')
    @mock.patch('netshow.linux.print_iface.linux_iface.Iface.is_bridge')
    @mock.patch('netshow.linux.show_interfaces.linux_cache.Cache')
    @mock.patch('netshow.linux.show_interfaces.linux_iface.portname_list')
    def test_ifacelist_is_bridge(self, mock_portname_list,
                                 mock_cache, mock_is_bridge,
                                 mock_exists):
        mock_exists.return_value = True
        # test to see if bridge is probably placed
        mock_is_bridge.return_value = True
        mock_portname_list.return_value = ['br0']
        self.showint.show_up = False
        assert_equals(isinstance(
            self.showint.ifacelist.get('all').get('br0'),
            print_bridge.PrintBridge), True)
        assert_equals(
            self.showint.ifacelist.get('bridge').get('br0'),
            self.showint.ifacelist.get('l2').get('br0'))
        assert_equals(
            self.showint.ifacelist.get('bridge').get('br0'),
            self.showint.ifacelist.get('all').get('br0'))

    @mock.patch('netshow.linux.print_iface.linux_iface.Iface.exists')
    @mock.patch('netshow.linux.print_iface.linux_iface.Iface.is_l3')
    @mock.patch('netshow.linux.print_iface.linux_iface.Iface.is_bond')
    @mock.patch('netshow.linux.show_interfaces.linux_cache.Cache')
    @mock.patch('netshow.linux.show_interfaces.linux_iface.portname_list')
    def test_ifacelist_is_bond_l3(self, mock_portname_list,
                                  mock_cache, mock_is_bond, mock_is_l3,
                                  mock_exists):
        mock_exists.return_value = True
        # test to see if bridge is probably placed
        mock_is_bond.return_value = True
        mock_is_l3.return_value = True
        mock_portname_list.return_value = ['bond0']
        self.showint.show_up = False
        assert_equals(isinstance(
            self.showint.ifacelist.get('all').get('bond0'),
            print_bond.PrintBond), True)
        assert_equals(
            self.showint.ifacelist.get('bond').get('bond0'),
            self.showint.ifacelist.get('l3').get('bond0'))
        assert_equals(
            self.showint.ifacelist.get('bond').get('bond0'),
            self.showint.ifacelist.get('all').get('bond0'))

    @mock.patch('netshow.linux.print_iface.linux_iface.Iface.exists')
    @mock.patch('netshow.linux.print_iface.linux_iface.Iface.is_l3')
    @mock.patch('netshow.linux.print_iface.linux_iface.Iface.is_trunk')
    @mock.patch('netshow.linux.print_iface.linux_iface.Iface.is_bridgemem')
    @mock.patch('netshow.linux.show_interfaces.linux_cache.Cache')
    @mock.patch('netshow.linux.show_interfaces.linux_iface.portname_list')
    def test_ifacelist_is_bridgemem_trunk(self, mock_portname_list,
                                          mock_cache, mock_is_bridgemem,
                                          mock_is_trunk, mock_is_l3,
                                          mock_exists):
        mock_exists.return_value = True
        mock_is_l3.return_value = False
        mock_is_trunk.return_value = True
        mock_is_bridgemem.return_value = True
        mock_portname_list.return_value = ['eth22']
        self.showint.show_up = False
        assert_equals(isinstance(
            self.showint.ifacelist.get('all').get('eth22'),
            print_bridge.PrintBridgeMember), True)
        assert_equals(self.showint.ifacelist.get('all').get('eth22'),
                      self.showint.ifacelist.get('l2').get('eth22'))
        assert_equals(
            self.showint.ifacelist.get('trunk').get('eth22'),
            self.showint.ifacelist.get('all').get('eth22'))

    @mock.patch('netshow.linux.print_iface.linux_iface.Iface.exists')
    @mock.patch('netshow.linux.print_iface.linux_iface.Iface.is_l3')
    @mock.patch('netshow.linux.print_iface.linux_iface.Iface.is_access')
    @mock.patch('netshow.linux.print_iface.linux_iface.Iface.is_trunk')
    @mock.patch('netshow.linux.print_iface.linux_iface.Iface.is_bridgemem')
    @mock.patch('netshow.linux.show_interfaces.linux_cache.Cache')
    @mock.patch('netshow.linux.show_interfaces.linux_iface.portname_list')
    def test_ifacelist_is_bridgemem_access(self, mock_portname_list,
                                           mock_cache, mock_is_bridgemem,
                                           mock_is_trunk, mock_is_access,
                                           mock_is_l3, mock_exists):
        mock_exists.return_value = True
        mock_is_l3.return_value = False
        mock_is_trunk.return_value = False
        mock_is_access.return_value = True
        mock_is_bridgemem.return_value = True
        mock_portname_list.return_value = ['eth22']
        self.showint.show_up = False
        assert_equals(isinstance(
            self.showint.ifacelist.get('all').get('eth22'),
            print_bridge.PrintBridgeMember), True)
        assert_equals(
            self.showint.ifacelist.get('access').get('eth22'),
            self.showint.ifacelist.get('all').get('eth22'))
        assert_equals(self.showint.ifacelist.get('all').get('eth22'),
                      self.showint.ifacelist.get('l2').get('eth22'))

    @mock.patch('netshowlib.linux.iface.Iface.exists')
    @mock.patch('netshow.linux.print_iface.linux_iface.Iface.is_bondmem')
    @mock.patch('netshow.linux.show_interfaces.linux_cache.Cache')
    @mock.patch('netshow.linux.show_interfaces.linux_iface.portname_list')
    def test_ifacelist_is_bondmem(self, mock_portname_list,
                                  mock_cache, mock_is_bondmem,
                                  mock_exists):
        mock_exists.return_value = True
        mock_is_bondmem.return_value = True
        mock_portname_list.return_value = ['eth22']
        self.showint.show_up = False
        assert_equals(isinstance(
            self.showint.ifacelist.get('all').get('eth22'),
            print_bond.PrintBondMember), True)
        assert_equals(
            self.showint.ifacelist.get('bondmem').get('eth22'),
            self.showint.ifacelist.get('all').get('eth22'))

    @mock.patch('netshow.linux.show_interfaces.ShowInterfaces.print_single_iface')
    @mock.patch('netshow.linux.show_interfaces.ShowInterfaces.print_many_ifaces')
    def test_run_single_iface(self, mock_many, mock_single):
        # single interface config
        self.showint.single_iface = True
        self.showint.run()
        assert_equals(mock_single.call_count, 1)

    @mock.patch('netshow.linux.show_interfaces.ShowInterfaces.print_single_iface')
    @mock.patch('netshow.linux.show_interfaces.ShowInterfaces.print_many_ifaces')
    def test_run_many_iface(self, mock_many, mock_single):
        # single interface config
        self.showint.single_iface = False
        self.showint.run()
        assert_equals(mock_many.call_count, 1)
        assert_equals(mock_single.call_count, 0)

    @mock.patch('netshow.linux.show_interfaces.print_iface.PrintIface.cli_output')
    @mock.patch('netshow.linux.show_interfaces.print_iface.linux_iface.Iface.exists')
    def test_print_single_iface(self, mock_exists, mock_cli_output):
        # iface does not exist
        mock_exists.return_value = False
        self.showint.single_iface = 'eth22'
        assert_equals(self.showint.print_single_iface(),
                      'interface_does_not_exist')
        # iface exists but print json
        mock_exists.return_value = True
        self.showint.use_json = True
        assert_equals(json.loads(
            self.showint.print_single_iface()
        ).get('linkstate'), 'admdn')
        # iface exists but print out cli
        self.showint.use_json = False
        self.showint.print_single_iface()
        assert_equals(mock_cli_output.call_count, 1)

    @mock.patch('netshowlib.linux.iface.Iface.is_bond')
    @mock.patch('netshow.linux.show_interfaces.print_iface.linux_iface.Iface.exists')
    def test_print_single_iface_json_bond(self, mock_exists, mock_is_bond):
        # test problem reporte where if vlan_list is not used,
        # json fails to be printed
        mock_exists.return_value = True
        mock_is_bond.return_value = True
        self.showint.single_iface = 'bond0'
        self.showint.use_json = True
        assert_equals(json.loads(
            self.showint.print_single_iface()).get('port_category'), 'bond')

    @mock.patch('netshow.linux.show_interfaces.ShowInterfaces.print_json_many_ifaces')
    @mock.patch('netshow.linux.show_interfaces.ShowInterfaces.print_cli_many_ifaces')
    def test_many_ifaces_cli_output(self, mock_cli_ifaces, mock_json_ifaces):
        mock_cli_ifaces.return_value = 'cli_output'
        # if json is false get cli output
        _output = self.showint.print_many_ifaces()
        mock_cli_ifaces.assert_called_with('l2')
        assert_equals(_output, 'cli_output')

    @mock.patch('netshow.linux.show_interfaces.ShowInterfaces.print_json_many_ifaces')
    @mock.patch('netshow.linux.show_interfaces.ShowInterfaces.print_cli_many_ifaces')
    def test_many_ifaces_json_output(self, mock_cli_ifaces, mock_json_ifaces):
        # if json is false get cli output
        mock_json_ifaces.return_value = 'json_output'
        self.showint.use_json = True
        _output = self.showint.print_many_ifaces()
        mock_json_ifaces.assert_called_with('l2')
        assert_equals(_output, 'json_output')

    @mock.patch('netshow.linux.print_iface.linux_iface.Iface.exists')
    @mock.patch('netshow.linux.show_interfaces.print_iface.linux_iface.Iface.read_from_sys')
    @mock.patch('netshow.linux.show_interfaces.print_iface.linux_iface.Iface.is_trunk')
    @mock.patch('netshow.linux.show_interfaces.print_iface.linux_iface.Iface.is_bridgemem')
    @mock.patch('netshow.linux.show_interfaces.linux_iface.portname_list')
    def test_many_cli_ifaces(self, mock_portlist, mock_bridgemem,
                             mock_trunk, mock_read_from_sys, mock_exists):
        mock_exists.return_value = True
        mock_portlist.return_value = ['eth10', 'eth11']
        mock_bridgemem.return_value = False
        mock_trunk.return_value = False
        values = {'mtu': '1500',
                  'carrier': '0', 'operstate': 'down',
                  'speed': '1000',
                  'ifalias': None}
        mock_read_from_sys.side_effect = mod_args_generator(values)
        self.showint.show_up = False
        _table = self.showint.print_cli_many_ifaces('all')
        assert_equals(re.split(r'\s+', _table.split('\n')[3]),
                      ['', 'name', 'speed', 'mtu', 'mode', 'summary'])
        assert_equals(re.split(r'\s+', _table.split('\n')[5]),
                      ['dn', 'eth10', '1G', '1500', 'unknown_int_type'])

    @mock.patch('netshow.linux.print_iface.linux_iface.Iface.exists')
    @mock.patch('netshow.linux.show_interfaces.print_iface.linux_iface.Iface.read_from_sys')
    @mock.patch('netshow.linux.show_interfaces.print_iface.linux_iface.Iface.is_trunk')
    @mock.patch('netshow.linux.show_interfaces.print_iface.linux_iface.Iface.is_bridgemem')
    @mock.patch('netshow.linux.show_interfaces.linux_iface.portname_list')
    def test_print_json_ifaces(self, mock_portlist, mock_bridgemem,
                               mock_trunk, mock_read_from_sys, mock_exists):
        mock_exists.return_value = True
        mock_portlist.return_value = ['eth10', 'eth11']
        mock_bridgemem.return_value = True
        mock_trunk.return_value = True
        values = {'mtu': '1500',
                  'carrier': '0', 'operstate': 'down',
                  'speed': '1000',
                  'ifalias': 'some description',
                  'address': '11:22:33:44:55:66'}
        mock_read_from_sys.side_effect = mod_args_generator(values)
        self.showint.use_json = True
        self.showint.show_up = False
        _output = self.showint.print_json_many_ifaces('all')
        _testjson = json.loads(_output)
        assert_equals(_testjson['eth10']['speed'], '1G')
        assert_equals(_testjson['eth10']['iface_obj']['speed'], '1000')
