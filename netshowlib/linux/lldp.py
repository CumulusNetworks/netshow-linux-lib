# http://pylint-messages.wikidot.com/all-codes
"""
This module defines properties and functions for collecting LLDP information
from a linux device using the ``lldpctl`` command
"""
from netshowlib.linux import common
import xml.etree.ElementTree as ElementTree
from collections import OrderedDict


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
    Cacheinfo function for LLDP information
    :return: hash of :class:`linux.lldp<Lldp>` objects with interface name as their keys
    """
    lldp_hash = OrderedDict()
    lldp_element = _exec_lldp()
    if lldp_element is None:
        return lldp_hash
    for _interface in lldp_element.iter('interface'):
        local_port = _interface.get('name')
        lldpobj = {}
        lldpobj['adj_port'] = _interface.findtext('port/id')
        lldpobj['adj_hostname'] = _interface.findtext('chassis/name')
        lldpobj['adj_mgmt_ip'] = _interface.findtext('chassis/mgmt-ip')
        if not lldp_hash.get(local_port):
            lldp_hash[local_port] = []
        lldp_hash[local_port].append(lldpobj)
    return lldp_hash


def interface(ifacename, cache):
    """
    Will use the cache provided first to get lldp information. If not found
    will run :meth:`cacheinfo()` and generate new lldp information

    :param ifacename: name of the interface
    :param cache: instance of a :class:`netshowlib.linux.cache.Cache`
                  that may have LLDP information
    :return: array of lldp information regarding a single interface.
    """
    if cache:
        lldp_cache = cache.lldp
    else:
        lldp_cache = cacheinfo()

    ifacelldp = lldp_cache.get(ifacename)
    if ifacelldp:
        return ifacelldp
    else:
        return None
