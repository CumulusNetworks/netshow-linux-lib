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
from asserts import assert_equals, mod_args_generator


@mock.patch('netshowlib.linux.lldp.os.path.exists')
def test_when_lldp_daemon_is_not_running(mock_lldp_running):
    mock_lldp_running.return_value = False
    lldp_hash = linux_lldp.cacheinfo()
    assert_equals(lldp_hash, {})


# test lldp info for many interfaces
@mock.patch('netshowlib.linux.lldp.os.path.exists')
@mock.patch('netshowlib.linux.lldp._exec_lldp')
def test_cacheinfo(mock_lldp, mock_lldp_running):
    mock_lldp_running.return_value = True
    lldp_out = open('tests/test_netshowlib/lldp_output.txt').read()
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
                   'adj_mgmt_ip': '192.168.0.15',
                   'system_descr': 'Cumulus Linux'})


@mock.patch('netshowlib.linux.lldp.common.exec_command')
def test_get_running_exec_lldp(mock_lldp):
    lldp_out = open('tests/test_netshowlib/lldp_output.txt').read()
    mock_lldp.return_value = lldp_out
    linux_lldp._exec_lldp()
    mock_lldp.assert_called_with('/usr/sbin/lldpctl -f xml')


@mock.patch('netshowlib.linux.lldp.os.path.exists')
@mock.patch('netshowlib.linux.lldp.common.exec_command')
def test_using_lldp_obj(mock_lldp, mock_exists):
    mock_exists.return_value = True
    lldp_out = open('tests/test_netshowlib/lldp_output.txt').read()
    mock_lldp.return_value = lldp_out
    _output = linux_lldp.Lldp('eth2').run()
    assert_equals(_output, [{'adj_hostname': 'right',
                             'adj_port': 'swp2',
                             'adj_mgmt_ip': '192.168.0.15',
                             'system_descr': 'Cumulus Linux'}])
