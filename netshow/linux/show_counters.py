# pylint: disable=E0611
""" Module for printing show counter information
"""
import netshowlib.netshowlib as nn
from netshow.linux.netjson_encoder import NetEncoder
from netshow.linux import print_iface
import netshowlib.linux.cache as linux_cache
from collections import OrderedDict
import json
from tabulate import tabulate
from netshow.linux.common import _
from netshow.linux.common import legend_wrapped_cli_output


class ShowCounters(object):
    """
    Class responsible for printing out basic counter information
    """
    def __init__(self, cl):
        self.use_json = cl.get('--json') or cl.get('-j')
        self.show_all = cl.get('all')
        self.show_errors = cl.get('errors')
        self.show_up = True
        if self.show_all:
            self.show_up = False
        self.ifacelist = OrderedDict()
        self.cache = linux_cache
        self.print_iface = print_iface
        self.show_legend = False
        if cl.get('-l') or cl.get('--legend'):
            self.show_legend = True

    def run(self):
        """
        :return: basic neighbor information based on data obtained on netshow-lib
        """
        feature_cache = self.cache.Cache()
        feature_cache.run()
        for _ifacename in sorted(nn.portname_list()):
            _piface = self.print_iface.iface(_ifacename, feature_cache)
            if self.show_up and _piface.iface.linkstate < 2:
                continue
            if self.show_errors and _piface.iface.counters.total_err == 0:
                continue
            self.ifacelist[_ifacename] = _piface

        if self.use_json:
            return json.dumps(self.ifacelist,
                              cls=NetEncoder, indent=4)
        return self.print_counters()

    def print_counters(self):
        """
        :return: cli output of netshow counters
        """
        _header = ['', _('port'), _('speed'), _('mode'), '',
                   _('packets'), _('errors')]
        _table = []
        for _piface in self.ifacelist.values():
            if _piface.iface.counters:
                _rx_counters = _piface.iface.counters.get('rx')
                _tx_counters = _piface.iface.counters.get('tx')
                _table.append([_piface.linkstate, _piface.name,
                               _piface.speed, _piface.port_category,
                               _('rx'), _rx_counters.get('packets'),
                               _rx_counters.get('errors')])
                _table.append(['', '', '', '', _('tx'),
                               _tx_counters.get('packets'),
                               _tx_counters.get('errors')])

        return legend_wrapped_cli_output(tabulate(_table, _header,
                                                  floatfmt='.0f'))
