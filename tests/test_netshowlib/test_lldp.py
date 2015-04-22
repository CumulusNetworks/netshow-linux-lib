""" Linux Lldp module tests
"""
# disable docstring checking
# pylint: disable=C0111
# disable checking no-self-use
# pylint: disable=R0201
# pylint: disable=W0212
# pylint: disable=W0201
# pylint: disable=F0401
import netshowlib.linux.lldp as linux_lldp
import xml.etree.ElementTree as ET
import mock
from asserts import assert_equals
from nose.tools import set_trace


# test lldp info for many interfaces
@mock.patch('netshowlib.linux.lldp._exec_lldp')
def test_cacheinfo(mock_lldp):
    lldp_out = open('tests/linux_tests/lldp_output.txt').read()
    mock_lldp.return_value = ET.fromstring(lldp_out)
    lldp_hash = linux_lldp.cacheinfo()
    # confirm correct number of lldp enabled ports
    assert_equals(len(lldp_hash), 2)
    # confirm that port with multiple lldp entries are there
    assert_equals(len(lldp_hash.get('eth1')), 2)
    # confirm contents of lldp entry
    assert_equals(lldp_hash.get('eth2')[0],
                  {'adj_hostname': 'right',
                   'adj_port': 'swp2',
                   'adj_mgmt_ip': '192.168.0.15'})


@mock.patch('netshowlib.linux.lldp.exec_command')
def test_get_running_exec_lldp(mock_lldp):
    lldp_out = open('tests/linux_tests/lldp_output.txt').read()
    mock_lldp.return_value = lldp_out
    linux_lldp._exec_lldp()
    mock_lldp.assert_called_with('/usr/sbin/lldpctl -f xml')
