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


class TestPrintBond(object):
    def setup(self):
        iface = linux_bond.Bond('eth22')
        self.piface = print_bond.PrintBond(iface)


    @mock.patch('netshow.linux.print_iface.linux_iface.Iface.is_l3')
    def test_port_category(self, mock_is_l3):
        # if l3
        mock_is_l3.return_value = True
        assert_equals(self.piface.port_category, 'bond/l3')
        # if not l3
        mock_is_l3.return_value = False
        assert_equals(self.piface.port_category, 'bond/l2')

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

