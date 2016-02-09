# disable docstring checking
# pylint: disable=C0111
# disable checking no-self-use
# pylint: disable=R0201
# pylint: disable=W0212
# disable invalid name
# pylint: disable=C0103
from asserts import assert_equals, mod_args_generator
import netshowlib.linux.common as common
import sys
import mock

# # Tests for common.py


@mock.patch('netshowlib.linux.iface.os.path.islink')
@mock.patch('netshowlib.linux.iface.os.listdir')
def test_port_list(mock_list_dir, mock_islink):
    values = {'/sys/class/net/bonding_masters': False,
              '/sys/class/net/eth1': True,
              '/sys/class/net/eth2': True,
              '/sys/class/net/tap1': True}
    mock_islink.side_effect = mod_args_generator(values)
    mock_list_dir.return_value = ['bonding_masters', 'eth1', 'eth2', 'tap1']
    assert_equals(common.portname_list(),
                  ['eth1', 'eth2', 'tap1'])


def test_sort_ports():
    ports = ['CEPPE_ETH22', 'BondMQO1', 'vlan115', 'swp1', 'vlan115-v0', 'BondQObb',
             'swp46.1', 'swp46.2', 'swp46.22',
             'swp46', 'swp3', 'swp33', 'swp2', 'swp22']
    _output = common.sort_ports(ports)
    assert_equals(_output,
                  ['BondMQO1', 'BondQObb', 'CEPPE_ETH22', 'swp1', 'swp2', 'swp3', 'swp22',
                   'swp33', 'swp46', 'swp46.1',
                   'swp46.2', 'swp46.22', 'vlan115', 'vlan115-v0'])

# test printing out range of numbers"


def test_group_ports_just_numbers():
    a = ['1', '2', '3', '4', '5', '10']
    assert_equals(common.create_range('', a), ['1-5', '10'])

# common - test group ports with no subifaces"


def test_group_port_no_subiface():
    a = ['swp1', 'swp2', 'swp3', 'swp4',
         'swp10', 'swp11', 'swp12', 'swp20']
    assert_equals(common.group_ports(a), ['swp1-4', 'swp10-12', 'swp20'])


def test_group_ports_where_one_does_not_have_number():
    a = ['downlink', 'downlink2', 'swp1', 'swp2', 'swp3']
    assert_equals(common.group_ports(a), ['downlink', 'downlink2', 'swp1-3'])


# test group ports with subifaces"
def test_group_port_with_subiface():
    a = ['swp1', 'swp2', 'swp3', 'swp4',
         'bond0.100', 'bond1.100', 'bond3.100',
         'swp33.100', 'swp34.100', 'swp40.100',
         'swp10', 'swp11', 'swp12', 'swp20']
    assert_equals(common.group_ports(a), ['bond0-1.100',
                                          'bond3.100',
                                          'swp33-34.100',
                                          'swp40.100',
                                          'swp1-4',
                                          'swp10-12',
                                          'swp20'])


def test_block_to_cidr_netmask():
    "common - convert block netmask to cidr"
    ipv6mask = 'ffff:ffff:ffff:ffff:ffff:ffff:ffff:fffe'
    assert_equals(common.netmask_dot_notation_to_cidr(ipv6mask), 127)
    ipv4mask = '255.255.254.0'
    assert_equals(common.netmask_dot_notation_to_cidr(ipv4mask), 23)


def test_exec_command():
    _output = common.exec_command('ls')
    if sys.version_info < (3, 0, 0):
        assert_equals(isinstance(_output, unicode), True)
    else:
        assert_equals(isinstance(_output, str), True)
