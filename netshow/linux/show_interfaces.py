# pylint: disable=R0902
# pylint: disable=E0611
"""
Module for printout of 'netshow interfaces'
"""

from collections import OrderedDict
from tabulate import tabulate
import netshow.linux.print_bridge as print_bridge
import netshow.linux.print_bond as print_bond
import netshowlib.linux.cache as linux_cache
from netshowlib.linux import iface as linux_iface
import netshow.linux.print_iface as print_iface
import json
from netshow.linux.netjson_encoder import NetEncoder
from netshow.linux.common import _, legend_wrapped_cli_output


class ShowInterfaces(object):
    """ Class responsible for the 'netshow interfaces' printout for \
        the linux provider
    """
    def __init__(self, cl):
        self._ifacelist = {}
        self.show_mac = cl.get('--mac') or cl.get('-m')
        self.use_json = cl.get('--json') or cl.get('-j')
        self.show_legend = False
        if cl.get('-l') or cl.get('--legend'):
            self.show_legend = True
        self.show_all = True
        self.show_mgmt = cl.get('mgmt')
        self.show_bridge = cl.get('bridges')
        self.show_bond = cl.get('bonds')
        self.show_bondmem = cl.get('bondmems')
        self.show_access = cl.get('access')
        self.show_trunk = cl.get('trunks')
        self.show_l3 = cl.get('l3')
        self.show_l2 = cl.get('l2')
        self.single_iface = cl.get('<iface>')
        if cl.get('all') or self.single_iface is not None:
            self.show_up = False
        else:
            self.show_up = True
        if self.show_bond or self.show_bondmem \
                or self.show_access or self.show_trunk \
                or self.show_bridge or self.show_mgmt:
            self.show_all = False
        self.oneline = cl.get('--oneline') or cl.get('-1')
        self.iface_categories = ['bond', 'bondmem',
                                 'bridge', 'trunk', 'access', 'l3',
                                 'l2']
        self._initialize_ifacelist()

    def run(self):
        """
        :return: terminal output or JSON for 'netshow interfaces' for
        the linux provider
        """
        if self.single_iface:
            return self.print_single_iface()
        else:
            return self.print_many_ifaces()

    def print_single_iface(self):
        """
        :return: netshow terminal output or JSON of a single iface
        """
        feature_cache = linux_cache.Cache()
        feature_cache.run()
        _printiface = print_iface.iface(self.single_iface, feature_cache)
        if not _printiface:
            return _('interface_does_not_exist')

        if self.use_json:
            return json.dumps(_printiface,
                              cls=NetEncoder, indent=4)
        else:
            return _printiface.cli_output(show_legend=self.show_legend)

    def _initialize_ifacelist(self):
        """
        initialize hash of interface lists. so create an empty orderedDict for bridges \
            bonds, trunks, etc
        """
        for i in self.iface_categories:
            self._ifacelist[i] = OrderedDict()
        self._ifacelist['all'] = OrderedDict()
        self._ifacelist['unknown'] = OrderedDict()

    @property
    def ifacelist(self):
        """
        :return: hash of interface categories. each category containing a list of \
            iface pointers to interfaces that belong in that category. For example
           ifacelist['bridge'] points to a list of bridge Ifaces.
        """

        # ifacelist is already populated..
        # to reset set ``self._ifacelist = None``
        if len(self._ifacelist.get('all')) > 0:
            return self._ifacelist

        self._initialize_ifacelist()
        list_of_ports = sorted(linux_iface.portname_list())
        feature_cache = linux_cache.Cache()
        feature_cache.run()
        for _portname in list_of_ports:
            _printiface = print_iface.iface(_portname, feature_cache)

            if self.show_up and _printiface.iface.linkstate < 2:
                continue

            # if iface is a l2 subint bridgemem, then ignore
            if _printiface.iface.is_subint() and \
                    isinstance(_printiface, print_bridge.PrintBridgeMember):
                continue

            self._ifacelist['all'][_portname] = _printiface

            # mutual exclusive bond/bridge/bondmem/bridgemem
            if isinstance(_printiface, print_bridge.PrintBridge):
                self._ifacelist['bridge'][_portname] = _printiface
                self._ifacelist['l2'][_portname] = _printiface
            elif isinstance(_printiface, print_bond.PrintBond):
                self._ifacelist['bond'][_portname] = _printiface
            elif isinstance(_printiface, print_bridge.PrintBridgeMember):
                self._ifacelist['l2'][_portname] = _printiface
            elif isinstance(_printiface, print_bond.PrintBondMember):
                self._ifacelist['bondmem'][_portname] = _printiface
                continue

            # mutual exclusive - l3/trunk/access
            if _printiface.iface.is_l3():
                self._ifacelist['l3'][_portname] = _printiface
            elif _printiface.iface.is_trunk():
                self._ifacelist['trunk'][_portname] = _printiface
            elif _printiface.iface.is_access():
                self._ifacelist['access'][_portname] = _printiface

        return self._ifacelist

    def print_many_ifaces(self):
        """
        :return: the output of 'netshow interfaces' for many interfaces
        """
        _port_type = None
        # determine wants port subtype or just all interfaces
        # for example if user types 'netshow l2' , then 'self.show_l2' will
        # be true, and only l2 ports will be printed
        for i in self.iface_categories:
            dict_name = 'show_' + i
            if self.__dict__[dict_name]:
                _port_type = i
                break
        if not _port_type:
            _port_type = 'all'

        if self.use_json:
            return self.print_json_many_ifaces(_port_type)

        return self.print_cli_many_ifaces(_port_type)

    @property
    def summary_header(self):
        """
        :return: summary header for 'netshow interfaces'
        """
        if self.show_mac:
            return ['', _('name'), _('mac'), _('speed'),
                    _('mtu'), _('mode'), _('summary')]
        else:
            return ['', _('name'), _('speed'),
                    _('mtu'), _('mode'), _('summary')]

    def print_json_many_ifaces(self, port_type):
        """
        :return: 'netshow interface' of many interfaces in JSON output
        """
        return json.dumps(self.ifacelist.get(port_type),
                          cls=NetEncoder, indent=4)

    def print_cli_many_ifaces(self, port_type):
        """
        :return: 'netshow interface' of many interfaces in terminal output
        """
        _headers = self.summary_header
        _table = []
        for _piface in self.ifacelist.get(port_type).values():
            if self.oneline:
                _table += self.cli_append_oneline(_piface)
            else:
                _table += self.cli_append_multiline(_piface)
        return legend_wrapped_cli_output(tabulate(_table, _headers), self.show_legend)

    def cli_append_oneline(self, piface):
        """
        prints summary netshow information one line per interface
        """
        _table = []
        if self.show_mac:
            _table.append([piface.linkstate,
                           piface.name,
                           piface.iface.mac,
                           piface.speed,
                           piface.iface.mtu,
                           piface.port_category,
                           ', '.join(piface.summary)])
        else:
            _table.append([piface.linkstate,
                           piface.name,
                           piface.speed,
                           piface.iface.mtu,
                           piface.port_category,
                           ', '.join(piface.summary)])

        return _table

    def cli_append_multiline(self, piface):
        """
        prints summary netshow information multiple lines per interface
        """
        _table = []
        if self.show_mac:
            _table.append([piface.linkstate,
                           piface.iface.mac,
                           piface.name,
                           piface.speed,
                           piface.iface.mtu,
                           piface.port_category,
                           piface.summary[0]])
        else:
            _table.append([piface.linkstate,
                           piface.name,
                           piface.speed,
                           piface.iface.mtu,
                           piface.port_category,
                           piface.summary[0]])

        if len(piface.summary) > 1:
            for i in range(1, len(piface.summary)):
                if self.show_mac:
                    _table.append(['', '', '',
                                   '', '', '', piface.summary[i]])
                else:
                    _table.append(['', '',
                                   '', '', '', piface.summary[i]])

        return _table
