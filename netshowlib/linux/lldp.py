# http://pylint-messages.wikidot.com/all-codes
"""
This module defines properties and functions for collecting LLDP information
from a linux device using the ``lldpctl`` command
"""
from netshowlib.linux import common
import xml.etree.ElementTree as ElementTree
from collections import OrderedDict
import os

def _exec_lldp(ifacename=None):
    """
     exec lldp and return output from LLDP or None
     """
    lldp_output = None
    exec_str = '/usr/sbin/lldpctl -f xml'
    if ifacename:
        exec_str += ' %s' % (ifacename)
    try:
        lldp_cmd = common.exec_command(exec_str)
        lldp_output = ElementTree.fromstring(lldp_cmd)
    except common.ExecCommandException:
        pass
    return lldp_output


def cacheinfo():
    """
    Cacheinfo function for LLDP information.
    Only works for Debian based systems that default to using lldpd.
    Or Redhat based systems that user has installed lldpd.
    No current support for lldpad (redhat recommended lldp app)
    :return: hash of :class:`linux.lldp<Lldp>` objects with interface name as their keys
    """
    lldp_hash = OrderedDict()
    lldp_element = _exec_lldp()
    if lldp_element is None or not os.path.exists('/var/run/lldpd.socket'):
        return lldp_hash
    for _interface in lldp_element.iter('interface'):
        local_port = _interface.get('name')
        lldpobj = {}
        lldpobj['adj_port'] = _interface.findtext('port/id')
        lldpobj['adj_hostname'] = _interface.findtext('chassis/name')
        lldpobj['adj_mgmt_ip'] = _interface.findtext('chassis/mgmt-ip')
        lldpobj['system_descr'] = _interface.findtext('chassis/descr')
        if not lldp_hash.get(local_port):
            lldp_hash[local_port] = []
        lldp_hash[local_port].append(lldpobj)
    return lldp_hash


class Lldp(object):
    """
    lldp option.
    """
    def __init__(self, name, cache=None):
        self.ifacename = name
        self.cache = cache
        self.lldp_cache = None
        self.cacheinfo = cacheinfo

    def run(self):
        if self.cache and self.cache.lldp:
            self.lldp_cache = self.cache.lldp
        else:
            self.lldp_cache = self.cacheinfo()


        lldp_iface = self.lldp_cache.get(self.ifacename)
        if lldp_iface:
            return lldp_iface
        else:
            return None
