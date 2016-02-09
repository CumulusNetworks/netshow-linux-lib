# http://pylint-messages.wikidot.com/all-codes
"""
This module collects basic counters from the device
"""
from netshowlib.linux import common
import os

def cacheinfo():
    """
    Cacheinfo function for Basic counter information
    Basic counters are defined in the IfaceCounters class.
    :return: hash of basic interface counters
    """
    pass

def gen_method(stat):
    """ generate methods that collect various stats from /sys/class/net
    """
    def _method(self):
        return common.read_from_sys(os.path.join('statistics', stat),
                                    self.name, True)
    return _method

class IfaceCounters(object):
    """
    Basic Iface counters
    Dynamically generated Functions:
        rx_bytes() - all receive bytes
        rx_packets() - all receive packets
        tx_bytes() - all transmitted bytes
        tx_packets() - all transmitted packets
        tx_errors() - all transmit errors
        rx_errors() - all receive errors
    """
    def __init__(self, name, cache=None):
        self.name = name
        self.cache = cache

    def read_from_sys(self, attr, oneline=True):
        """
        reads an attribute found in the
        ``/sys/class/net/[iface_name]/statistics`` directory
        """
        return common.read_from_sys(attr, self.name, oneline)

    def run(self):
        if self.cache:
            return self.cache.counters.get(self.name)
        else:
            self.cache = cacheinfo()
            return self.cache.get(self.name)



for stat in ['rx_bytes', 'tx_bytes', 'rx_packets', 'tx_packets',
             'tx_errors', 'rx_errors']:
    _method = gen_method(stat)
    setattr(IfaceCounters, stat, _method)
