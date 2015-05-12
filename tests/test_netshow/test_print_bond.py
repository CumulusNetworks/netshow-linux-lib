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

import netshow.linux.print_bond as print_bond
import netshowlib.linux.bond as linux_bond
import mock
from asserts import assert_equals, mod_args_generator
from nose.tools import set_trace
import re


class TestPrintBondMember(object):
    def setup(self):
        self.bond = linux_bond.Bond('bond0')
        iface = linux_bond.BondMember('eth22', master=self.bond)
        self.piface = print_bond.PrintBondMember(iface)

    def test_port_category(self):
        assert_equals(self.piface.port_category, 'bondmem')

    @mock.patch('netshowlib.linux.common.read_file_oneline')
    @mock.patch('netshowlib.linux.iface.Iface.read_from_sys')
    def test_summary(self, mock_read_from_sys, mock_file_oneline):
        values1 = {'carrier': '1',
                   'bonding/mode': 'something 2'}
        values2 = {}
        mock_read_from_sys.side_effect = mod_args_generator(values1)
        mock_file_oneline.side_effect = mod_args_generator(values2)
        assert_equals(self.piface.summary, ['master: bond0(UP)'])

    @mock.patch('netshowlib.linux.lldp.interface')
    @mock.patch('netshowlib.linux.common.read_file_oneline')
    @mock.patch('netshowlib.linux.iface.Iface.read_from_sys')
    def test_bondmem_details(self, mock_read_from_sys, mock_file_oneline,
                             mock_lldp):
        values1 = {'carrier': '1',
                   'bonding/mode': '802.3ad 4',
                   'bonding/slaves': 'eth22 eth23',
                   'bonding/xmit_hash_policy': 'layer3+4 1',
                   'bonding/min_links': '2'}
        values2 = {'/sys/class/net/bond0/bonding/ad_sys_priority': '65535',
                   '/sys/class/net/bond0/bonding/lacp_rate': 'slow 0'}
        values = [{'adj_port': 'eth2',
                   'adj_hostname': 'switch1'},
                  {'adj_port': 'eth10',
                   'adj_hostname': 'switch2'}]
        mock_lldp.return_value = values
        mock_read_from_sys.side_effect = mod_args_generator(values1)
        mock_file_oneline.side_effect = mod_args_generator(values2)
        _output = self.piface.bondmem_details()
        _outputtable = _output.split('\n')
        assert_equals(len(_outputtable), 11)
        assert_equals(_outputtable[0].split(r'\s{3,}'), ['bond_details'])
        assert_equals(re.split(r'\s{3,}', _outputtable[2]), ['master_bond:', 'bond0'])
        assert_equals(re.split(r'\s{3,}', _outputtable[3]), ['state_in_bond:',
                                                             'port_not_in_bond'])
        assert_equals(re.split(r'\s{3,}', _outputtable[4]), ['link_failures:', '0'])
        assert_equals(re.split(r'\s{3,}', _outputtable[5]), ['bond_members:',
                                                             'eth22, eth23'])

        assert_equals(re.split(r'\s{3,}', _outputtable[6]), ['bond_mode:', 'lacp'])
        assert_equals(re.split(r'\s{3,}', _outputtable[7]), ['load_balancing:',
                                                             'layer3+4'])
        assert_equals(re.split(r'\s{3,}', _outputtable[8]), ['minimum_links:', '2'])
        assert_equals(re.split(r'\s{2,}', _outputtable[9]),
                      ['lacp_sys_priority:', '65535'])
        assert_equals(re.split(r'\s{3,}', _outputtable[10]), ['lacp_rate:', 'slow_lacp'])

    @mock.patch('netshow.linux.print_bond.PrintBondMember.lldp_details')
    @mock.patch('netshow.linux.print_bond.PrintBondMember.bondmem_details')
    @mock.patch('netshow.linux.print_bond.PrintBondMember.cli_header')
    def test_cli_output(self, mock_cli_header, mock_bondmem_details, mock_lldp):
        mock_cli_header.return_value = 'cli_output'
        mock_bondmem_details.return_value = 'bondmem_details'
        mock_lldp.return_value = 'lldp_output'
        assert_equals(self.piface.cli_output(),
                      'cli_output\n\nbondmem_details\n\nlldp_output\n\n')


class TestPrintBond(object):
    def setup(self):
        iface = linux_bond.Bond('bond0')
        self.piface = print_bond.PrintBond(iface)

    @mock.patch('netshow.linux.print_iface.PrintIface.cli_header')
    @mock.patch('netshow.linux.print_bond.PrintBond.bond_details')
    @mock.patch('netshow.linux.print_iface.PrintIface.ip_details')
    @mock.patch('netshow.linux.print_bond.PrintBond.bondmem_details')
    def test_cl_output(self, mock_bondmems,
                       mock_ip, mock_bond_details,
                       mock_cli_header):
        mock_ip.return_value = 'ip output'
        mock_bondmems.return_value = 'bondmem output'
        mock_bond_details.return_value = 'bond details'
        mock_cli_header.return_value = 'cli header'
        _output = self.piface.cli_output()
        assert_equals(_output,
                      'cli header\n\nbond details\n\nip output\n\nbondmem output\n\nno_lldp_entries\n\n')

    @mock.patch('netshowlib.linux.lldp.interface')
    @mock.patch('netshowlib.linux.common.read_file_oneline')
    @mock.patch('netshowlib.linux.iface.Iface.read_from_sys')
    def test_lldp_details(self, mock_read_from_sys, mock_file_oneline,
                          mock_lldp):
        values1 = {'bonding/slaves': 'eth20 eth30',
                   'bonding/mode': 'something 2',
                   'carrier': '1'}
        values2 = {}
        values = [{'adj_port': 'eth2',
                   'adj_hostname': 'switch1'},
                  {'adj_port': 'eth10',
                   'adj_hostname': 'switch2'}]
        mock_lldp.return_value = values
        mock_read_from_sys.side_effect = mod_args_generator(values1)
        mock_file_oneline.side_effect = mod_args_generator(values2)
        _output = self.piface.lldp_details()
        _outputtable = _output.split('\n')
        assert_equals(_outputtable[0].split(), ['lldp'])
        assert_equals(_outputtable[2].split(), ['eth20(P)', '====', 'eth2(switch1)'])
        assert_equals(_outputtable[3].split(), ['====', 'eth10(switch2)'])
        assert_equals(_outputtable[4].split(), ['eth30(P)', '====', 'eth10(switch2)'])

    @mock.patch('netshowlib.linux.common.read_file_oneline')
    @mock.patch('netshowlib.linux.iface.Iface.read_from_sys')
    def test_bondmem_details(self, mock_read_from_sys, mock_file_oneline):
        values1 = {'bonding/slaves': 'eth20 eth30',
                   'carrier': '1',
                   'bonding/mode': 'something 2',
                   'speed': '1000'}
        values2 = {}
        mock_read_from_sys.side_effect = mod_args_generator(values1)
        mock_file_oneline.side_effect = mod_args_generator(values2)
        _output = self.piface.bondmem_details()
        _outputtable = _output.split('\n')
        assert_equals(_outputtable[0].split(), ['port', 'speed', 'link_failures'])
        assert_equals(_outputtable[2].split(), ['up', 'eth20(P)', '1G', '0'])
        assert_equals(_outputtable[3].split(), ['up', 'eth30(P)', '1G', '0'])

    @mock.patch('netshowlib.linux.common.read_file_oneline')
    @mock.patch('netshowlib.linux.iface.Iface.read_from_sys')
    def test_bond_details(self, mock_read_from_sys, mock_file_oneline):
        # with lacp
        values1 = {'bonding/mode': '802.3ad 4',
                   'bonding/xmit_hash_policy': 'layer3+4 2',
                   'bonding/min_links': '2'}
        values2 = {
            '/sys/class/net/bond0/bonding/ad_sys_priority': '65535',
            '/sys/class/net/bond0/bonding/lacp_rate': 'fast 1'
        }
        mock_read_from_sys.side_effect = mod_args_generator(values1)
        mock_file_oneline.side_effect = mod_args_generator(values2)
        _output = self.piface.bond_details()
        _outputtable = _output.split('\n')
        assert_equals(_outputtable[0], 'bond_details')
        assert_equals(_outputtable[2].split(), ['bond_mode:', 'lacp'])
        assert_equals(_outputtable[3].split(), ['load_balancing:', 'layer2+3'])
        assert_equals(_outputtable[4].split(), ['minimum_links:', '2'])
        assert_equals(_outputtable[5].split(), ['lacp_sys_priority:', '65535'])
        assert_equals(_outputtable[6].split(), ['lacp_rate:', 'fast_lacp'])
        assert_equals(len(_output.split('\n')), 7)
        # without lacp
        values1 = {'bonding/mode': 'something_else 2',
                   'bonding/xmit_hash_policy': 'layer3+4 2',
                   'bonding/min_links': '2'}
        mock_read_from_sys.side_effect = mod_args_generator(values1)
        _output = self.piface.bond_details()
        assert_equals(len(_output.split('\n')), 5)

    @mock.patch('netshowlib.linux.iface.Iface.read_from_sys')
    def test_hash_policy(self, mock_read_from_sys):
        mock_read_from_sys.return_value = 'layer3+4 1'
        assert_equals(self.piface.hash_policy, 'layer3+4')

    @mock.patch('netshowlib.linux.iface.Iface.read_from_sys')
    def test_bond_mode(self, mock_read_from_sys):
        mock_read_from_sys.return_value = '802.3ad 4'
        assert_equals(self.piface.mode, 'lacp')

    @mock.patch('netshow.linux.print_iface.linux_iface.Iface.is_access')
    @mock.patch('netshow.linux.print_iface.linux_iface.Iface.is_trunk')
    @mock.patch('netshow.linux.print_iface.linux_iface.Iface.is_l3')
    def test_port_category(self, mock_is_l3, mock_is_trunk, mock_is_access):
        # if l3
        mock_is_trunk.return_value = False
        mock_is_l3.return_value = True
        mock_is_access.return_value = False
        assert_equals(self.piface.port_category, 'bond/l3')
        # if trunk
        mock_is_l3.return_value = False
        mock_is_trunk.return_value = True
        mock_is_access.return_value = False
        assert_equals(self.piface.port_category, 'bond/trunk')
        # if access
        mock_is_l3.return_value = False
        mock_is_trunk.return_value = False
        mock_is_access.return_value = True
        assert_equals(self.piface.port_category, 'bond/access')

    @mock.patch('netshowlib.linux.iface.Iface.read_from_sys')
    @mock.patch('netshowlib.linux.bond.BondMember._parse_proc_net_bonding')
    def test_abbver_bondstate(self, mock_parse_proc, mock_read_from_sys):
        values = {'bonding/mode': '802.3ad 4'}
        mock_read_from_sys.side_effect = mod_args_generator(values)
        bondmem = linux_bond.BondMember('eth22')
        bondmem._bondstate = 1
        assert_equals(self.piface.abbrev_bondstate(bondmem), 'P')
        bondmem._bondstate = 0
        assert_equals(self.piface.abbrev_bondstate(bondmem), 'D')

    @mock.patch('netshowlib.linux.common.read_file_oneline')
    @mock.patch('netshowlib.linux.iface.Iface.read_from_sys')
    def test_print_bondmems(self, mock_read_from_sys,
                            mock_file_oneline):
        # ports up and in bond
        values = {'bonding/slaves': 'eth22 eth24',
                  'carrier': '1',
                  'bonding/mode': 'active-backup 2'}
        values2 = {}
        mock_read_from_sys.side_effect = mod_args_generator(values)
        mock_file_oneline.side_effect = mod_args_generator(values2)
        _output = self.piface.print_bondmems()
        assert_equals(_output.split(), ['bondmems:', 'eth22(UP),', 'eth24(UP)'])
        # ports up but not in bond
        values = {'bonding/slaves': 'eth22 eth24',
                  'carrier': '1',
                  'bonding/mode': '802.3ad 4'}
        values2 = {}
        mock_read_from_sys.side_effect = mod_args_generator(values)
        mock_file_oneline.side_effect = mod_args_generator(values2)
        for _bondmem in self.piface.iface.members.values():
            _bondmem._bondstate = 0
        _output = self.piface.print_bondmems()
        assert_equals(_output.split(), ['bondmems:', 'eth22(UD),', 'eth24(UD)'])
        # no ports in bond
        values = {'bonding/slaves': None}
        mock_read_from_sys.side_effect = mod_args_generator(values)
        mock_file_oneline.side_effect = mod_args_generator(values2)
        _output = self.piface.print_bondmems()
        assert_equals(_output, 'no_bond_members_found')

    @mock.patch('netshow.linux.print_bond.PrintBond.access_summary')
    @mock.patch('netshow.linux.print_bond.PrintBond.trunk_summary')
    @mock.patch('netshow.linux.print_bond.PrintBond.print_bondmems')
    def test_summary(self, mock_bondmems, mock_trunk_summary, mock_access_summary):
        mock_trunk_summary.return_value = ['trunk summary']
        mock_access_summary.return_value = ['access summary']
        mock_bondmems.return_value = 'list of bondmembers'
        mock_is_l3 = mock.MagicMock(return_value=True)
        mock_is_trunk = mock.MagicMock(return_value=False)
        mock_is_access = mock.MagicMock(return_value=False)
        self.piface.iface.is_l3 = mock_is_l3
        self.piface.iface.is_trunk = mock_is_trunk
        self.piface.iface.is_access = mock_is_access
        self.piface.iface.ip_address.ipv4 = ['10.1.1.1/24']
        _output = self.piface.summary
        assert_equals(_output, ['list of bondmembers', '10.1.1.1/24'])
        # is not l3 but is a trunk
        mock_is_l3.return_value = False
        mock_is_trunk.return_value = True
        _output = self.piface.summary
        assert_equals(_output, ['list of bondmembers', 'trunk summary'])
        # is not trunk or l3
        mock_is_trunk.return_value = False
        mock_is_access.return_value = True
        _output = self.piface.summary
        assert_equals(_output, ['list of bondmembers', 'access summary'])
        # not l3 or l2
        mock_is_access.return_value = False
        _output = self.piface.summary
        assert_equals(_output, ['list of bondmembers'])
