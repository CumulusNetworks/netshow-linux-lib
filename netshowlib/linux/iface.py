# Due to namespace issues pylint fails to find netshowlib.netshowlib
# pylint: disable=E0611
# disable too many attributes message
# pylint: disable=R0902
# pylint: disable=R0904

""" Linux.iface module
This module contains the `linux.iface.Iface` class that is responsible for
collecting various information about a linux interface.
"""

import netshowlib.netshowlib as nn
import netshowlib.linux.common as common
import netshowlib.linux.ip_address as ip_address
import netshowlib.linux.lldp as lldp
import netshowlib.linux.ip_neighbor as ip_neighbor
import os
import glob
import re
from datetime import datetime

"""
Variables for port type bitmap entry
"""
L2_INT = 1
L3_INT = 2
BRIDGE_INT = 3
BOND_INT = 4
BONDMEM_INT = 5
TRUNK_INT = 6
MGMT_INT = 7
LOOPBACK_INT = 8
PHY_INT = 9
SUB_INT = 10
SVI_INT = 11
VXLAN_INT = 12

def portname_list():
    return common.portname_list()

def iface(name, cache=None):
    """
    calls on checks to determine best interface type match for the named interface

    :return: regular :class:`linux.iface <netshowlib.linux.iface.Iface>` or \
    :class:`linux bond or bond member<netshowlib.linux.bond.Bond>`  or  \
    :class:`linux bridge or bridge member <netshowlib.linux.bridge.Bridge>` \
    interface
    """
    # create test iface.
    test_iface = Iface(name, cache=cache)
    if test_iface.is_bridge():
        bridge = nn.import_module('netshowlib.linux.bridge')
        return bridge.Bridge(name, cache=cache)
    elif test_iface.is_bond():
        bond = nn.import_module('netshowlib.linux.bond')
        return bond.Bond(name, cache=cache)
    elif test_iface.is_bondmem():
        bondmem = nn.import_module('netshowlib.linux.bond')
        return bondmem.BondMember(name, cache=cache)
    elif test_iface.is_bridgemem():
        bridge = nn.import_module('netshowlib.linux.bridge')
        return bridge.BridgeMember(name, cache=cache)

    return test_iface


class Iface(object):
    """ Linux Iface attributes

    * **mac**: mac address
    * **mtu**: port MTU
    * **description**:  port description same as *alias*
    * **speed**: speed in KB
    * **linkstate**: It can be either 0(*adminDown*), 1(*Down*) or 2(*Up*). \
        Difference between *adminDown* and *Down* is that the in *adminDown* \
        state the carrier does not exist. To get into *adminDown* state \
        is the state achieved when ``ip link set down`` is executed on an interface
    * **ip_address**: This provides a list of IPv4 and IPv6 addresses \
        associated with the interface
    * **ip_addr_assign**: If the address is configured via \
        DHCP this property is set to 1
    * **ip_address**: pointer to  \
        :class:`linux.ip_address<netshowlib.linux.ip_address.Ipaddr>` \
        class instance
    * **ip_neighbor**: pointer to _address:class:`linux.ip_neighbor\
        <netshowlib.linux.ip_neighbor.IpNeighbor>` class instance
    """
    def __init__(self, name, cache=None):
        self._mac = None
        self._mtu = None
        self._name = name
        self._description = None
        self._speed = None
        self._linkstate = 0
        self._sys_path_root = common.SYS_PATH_ROOT
        self._port_type = 0
        self._ip_address = ip_address.IpAddress(name, cache)
        self._ip_neighbor = ip_neighbor.IpNeighbor(name, cache)
        self._ip_addr_assign = 0
        self._cache = cache
        self._lldp = lldp.Lldp(name, cache)

# ----------------------
# Class methods

    @classmethod
    def subint_port_regex(cls, _ifacename='.*'):
        """ regex to check if string is a subinterface port """
        return re.compile(r"%s\.\d+$" % _ifacename)

# -----------------------

    def exists(self):
        """
        :return: return true if port exists in /sys/class/net
        """
        if os.path.exists(os.path.join(self._sys_path_root, self.name)):
            return True
        return False

    def read_symlink(self, attr):
        """
        :return symlink under a /sys/class/net iface config.
        """
        return common.read_symlink(self.sys_path(attr))

    def sys_path(self, attr, iface_name=None):
        """
        :return: /sys/class/net/*self.name*/*<attr>*
        """
        if iface_name:
            return common.sys_path(attr, iface_name)
        return common.sys_path(attr, self.name)

    def read_from_sys(self, attr, oneline=True):
        """
        reads an attribute found in the
        ``/sys/class/net/[iface_name]/`` directory
        """
        return common.read_from_sys(attr, self.name, oneline)

    def get_sub_interfaces(self):
        """
        :return: list of sub interfaces of port
        """
        subints = []
        filepath = "%s/%s.*" % (self._sys_path_root, self._name)
        for _file in glob.glob(filepath):
            subints.append(_file.split('/')[-1])

        return subints

    def get_bridgemem_port_type(self):
        """
        :return: 0 if port is not a bridge member
        :return: 1 if  port is access port
        :return: 2 if port is a trunk port
        """
        _bridgemem_type = 0
        if os.path.exists(self.sys_path('brport')):
            _bridgemem_type = 1

        if not self.is_subint():
            for subint in self.get_sub_interfaces():
                if os.path.exists(self.sys_path('brport', subint)):
                    _bridgemem_type = 2
                    break
        return _bridgemem_type

    def check_port_dhcp_assignment(self, leasesfile):
        """
        sets ``self._ip_addr_assign`` to ``1`` if port is
        a DHCP enabled interface
        """
        try:
            filehandler = open(leasesfile)
            lines = filehandler.read()
            filehandler.close()
        except IOError:
            return
        lines = re.sub('\n', '', lines)
        last_lease = re.split(r'lease\s*{', lines)[-1]
        _m0 = re.search(r'expire\s+\d+\s+([0-9/]+\s+[0-9:]+)',
                        last_lease)
        if _m0:
            lease_expires_on = _m0.group(1)
        else:
            return
        fmt = '%Y/%m/%d %H:%M:%S'
        lease_expires_on = datetime.strptime(lease_expires_on, fmt)
        lease_valid = lease_expires_on > datetime.now()
        if lease_valid:
            regex = re.compile(r'fixed-address\s*([0-9.]+)' +
                               r'.*subnet-mask\s*([0-9.]+)')
            match = re.search(regex, last_lease)
            if match:
                ip_addr = match.group(1)
                smask = match.group(2)
                smask = common.netmask_dot_notation_to_cidr(smask)
                dhcpaddr = ip_addr + '/' + str(smask)
                if self.ip_address.allentries:
                    for i in self.ip_address.allentries:
                        if dhcpaddr == i:
                            self._ip_addr_assign = 1
                            return


# Port Category Testers
# -----------------------

    def is_bond_initial_test(self):
        """
        | sets port bitmap entry ``BOND_INT`` option if port is a bond port
        """
        self._port_type = common.clear_bit(self._port_type, BOND_INT)
        bonding_check = self.sys_path('bonding')
        if os.path.exists(bonding_check):
            self._port_type = common.set_bit(self._port_type, BOND_INT)

    def is_bridge_initial_test(self):
        """
        | sets port bitmap entry ``BRIDGE_INT`` option if port is a bridge port
        """
        self._port_type = common.clear_bit(self._port_type, BRIDGE_INT)
        self._port_type = common.clear_bit(self._port_type, L2_INT)
        if os.path.exists(self.sys_path('bridge')):
            self._port_type = common.set_bit(self._port_type, BRIDGE_INT)
            self._port_type = common.set_bit(self._port_type, L2_INT)

    def is_bondmem_initial_test(self):
        """
        | sets port bitmap entry ``BONDMEM_INT`` option if port is a bond member port
        """
        self._port_type = common.clear_bit(self._port_type, BONDMEM_INT)
        if os.path.exists(self.sys_path('master/bonding')):
            self._port_type = common.set_bit(self._port_type, BONDMEM_INT)

    def is_bridgemem_initial_test(self):
        """
        | sets port bitmap entry ``BRIDGEMEM_INT`` option if port is a bridge member port
        """
        self._port_type = common.clear_bit(self._port_type, L2_INT)
        self._port_type = common.clear_bit(self._port_type, TRUNK_INT)
        self._port_type = common.clear_bit(self._port_type, BRIDGE_INT)
        bridgemem_type = self.get_bridgemem_port_type()
        if bridgemem_type > 0:
            self._port_type = common.set_bit(self._port_type, L2_INT)
        if bridgemem_type == 2:
            self._port_type = common.set_bit(self._port_type, TRUNK_INT)

    def is_subint_initial_test(self):
        """
        :return:  sets port bitmap entry ``SUB_INT`` if port is a subinterface
        """
        self._port_type = common.clear_bit(self._port_type, SUB_INT)
        if re.match(self.subint_port_regex(), self._name):
            self._port_type = common.set_bit(self._port_type, SUB_INT)

    def is_loopback_initial_test(self):
        """
        :return: sets port bitmap entry ``LOOPBACK_INT``
        """
        self._port_type = common.clear_bit(self._port_type, LOOPBACK_INT)
        if re.match('lo', self._name):
            self._port_type = common.set_bit(self._port_type, LOOPBACK_INT)

# Port Category Checkers
# ----------------------

    def is_bridgemem(self):
        """
        :return: true if port is a bridge member
        """
        self.is_bridgemem_initial_test()
        return common.check_bit(self._port_type, L2_INT) and \
            not common.check_bit(self._port_type, BRIDGE_INT)

    def is_access(self):
        """
        :return: true if port is access port. That is a port in a bridge \
        that is not a trunk
        """
        self.is_bridgemem_initial_test()
        return common.check_bit(self._port_type, L2_INT) and \
            not common.check_bit(self._port_type, BRIDGE_INT) and \
            not common.check_bit(self._port_type, TRUNK_INT)

    def is_l2(self):
        """
        :return: true if port is l2. That is part of a bridge domain
        """
        self.is_bridge_initial_test()
        self.is_bridgemem_initial_test()
        return common.check_bit(self._port_type, L2_INT)

    def is_l3(self):
        """
        :return: True if iface has IP address
        """
        if self.ip_address.allentries:
            return True
        return False

    def is_trunk(self):
        """
        :return: true if port is a trunk. A trunk carries multiple LANs
        """
        self.is_bridgemem_initial_test()
        return common.check_bit(self._port_type, TRUNK_INT)

    def is_bond(self):
        """
        :return: true if port is a bond
        """
        self.is_bond_initial_test()
        return common.check_bit(self._port_type, BOND_INT)

    def is_bridge(self):
        """
        :return: true if port is a bridge
        """
        self.is_bridge_initial_test()
        return common.check_bit(self._port_type, BRIDGE_INT)

    def is_bondmem(self):
        """
        :return: true if port is a bondmem
        """
        self.is_bondmem_initial_test()
        return common.check_bit(self._port_type, BONDMEM_INT)

    def is_subint(self):
        """
        :return: true if port is a sub-interface
        """
        self.is_subint_initial_test()
        return common.check_bit(self._port_type, SUB_INT)

    def is_loopback(self):
        """
        :return: true if port is a sub-interface
        """
        self.is_loopback_initial_test()
        return common.check_bit(self._port_type, LOOPBACK_INT)

    def stp_state(self):
        """
        :return stp state of a particular bridge member.
        If not a bridge member returns None
        """
        _attrlocation = 'brport/bridge/bridge/stp_state'
        _path = self.sys_path(_attrlocation)
        if os.path.exists(_path):
            return self.read_from_sys(_attrlocation)
        else:
            for _name in self.get_sub_interfaces():
                _iface = self.__class__(_name)
                _subint_stp_state = _iface.stp_state()
                if _subint_stp_state:
                    return _subint_stp_state
        return None

# Properties
# -------------
    @property
    def name(self):
        """
        :return: interface name
        """
        return self._name

    @property
    def mac(self):
        """
        :return: port mac address
        """
        if not self._mac:
            self._mac = self.read_from_sys('address')
        return self._mac

    @property
    def mtu(self):
        """
        :return:  port MTU
        """
        if not self._mtu:
            self._mtu = self.read_from_sys('mtu')
        return self._mtu

    @property
    def description(self):
        """
        :return: interface description / alias
        """
        if not self._description:
            self._description = self.read_from_sys('ifalias')
        return self._description

    @property
    def speed(self):
        """
        :return: port speed in MB
        """
        if not self._speed:
            try:
                self._speed = self.read_from_sys('speed')
            except ValueError:
                self._speed = None
        return self._speed

    @property
    def linkstate(self):
        """
        |  *"adminDown"* means carrier does not exist.
        |  *"Down"* means carrier exist but L2 protocols are down.
        |  *"Dormant"* means that the port is UP but dormant.

        :return:  0(adminDown), 1(Down), 2(Up), 3(Dormant)
        :rtype: int
        """
        _carrier = self.read_from_sys('carrier')
        _operstate = self.read_from_sys('operstate')
        if _operstate and _operstate == 'dormant':
            self._linkstate = 3
        elif _carrier:
            self._linkstate = 1 if _carrier == '0' else 2
        else:
            self._linkstate = 0
        return self._linkstate

    @property
    def lldp(self):
        """
        gets LLDP information from cache or system, depending \
        if cache is provided. Example

        .. code-block:: python

        here is my example TODO

        :return: array of hash entries that contain lldp information
        """
        return self._lldp.run()

    @property
    def ip_address(self):
        """
        gets IP address from cache or system, depending on whether \
        a cache is provided

        :return: :class:`Ipaddr instance specific to this interface \
            <netshowlib.linux.ip_address.Ipaddr>`
        """
        self._ip_address.run()
        return self._ip_address

    @property
    def ip_neighbor(self):
        """
        get list of IP neighbor entries from cache or from system  \
        associated with this interface

        :return:  :class:`linux.ip_neighbor instance
        <netshowlib.linux.ip_neighbor.IpNeighbor>`
        """
        self._ip_neighbor.run()
        return self._ip_neighbor

    @property
    def ip_addr_assign(self):
        """
        :return: ``1`` if port is DHCP enabled else returns ``0``
        """
        leasesfile = '/var/lib/dhcp/dhclient.%s.leases' % (self.name)
        self.check_port_dhcp_assignment(leasesfile)
        return self._ip_addr_assign

    @property
    def vlan_list(self):
        """
        :return: list that first has the name of the
        untagged vlan followed by a list \
        of vlans the trunk supports
        :return: empty list if no vlan list found.
        """
        _vlanlist = {}
        if self.is_bridgemem() or self.is_bond():
            for _bridge in self.bridge_masters.values():
                _vlan_tag = _bridge.vlan_tag
                if _bridge.untagged_members.get(self.name):
                    _vlanlist[_bridge.name] = ['0']
                else:
                    _vlanlist[_bridge.name] = _vlan_tag
        return _vlanlist

    @property
    def native_vlan(self):
        """
        Get the name of the native vlan of the trunk port
        """
        # if vlan list is empty..which is should not be!
        if not self.vlan_list:
            return []
        _vlanlist = self.vlan_list
        return [_bridgename for _bridgename, _vlanid in _vlanlist.items()
                if len(_vlanid) == 1 and int(_vlanid[0]) == 0]
