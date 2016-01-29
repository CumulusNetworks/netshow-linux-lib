"""
Print and Analysis Module for Linux bond interfaces
"""

from netshow.linux.print_iface import PrintIface
from netshow.linux.common import _, one_line_legend, full_legend
from tabulate import tabulate


class PrintBondMember(PrintIface):
    """
    Print and Analysis Class for Linux bond member interfaces
    """
    @property
    def port_category(self):
        """
        :return: port category for a bondmem
        """
        return _('bondmem')

    @property
    def summary(self):
        """
        :return: summary info for bond members for 'netshow interfaces'
        """
        _arr = []
        _arr.append("%s: %s(%s%s)" % (_('master'),
                                      self.iface.master.name,
                                      PrintIface.abbrev_linksummary(self.iface.master),
                                      PrintBond.abbrev_bondstate(self.iface)))
        return _arr

    @property
    def state_in_bond(self):
        """
        :return: text describing the state of the port in the bond
        """
        if self.iface.bondstate == 1:
            return _('port_in_bond')
        else:
            return _('port_not_in_bond')

    def bondmem_details(self):
        """
        :return: string with output shown when netshow interfaces is issued on a \
        bond member
        """
        _header = [_('bond_details'), '']
        _master = self.iface.master
        _printbond = PrintBond(_master)
        _table = []
        _table.append([_('master_bond') + ':', _master.name])
        _table.append([_('state_in_bond') + ':', self.state_in_bond])
        _table.append([_('link_failures') + ':', self.iface.linkfailures])
        _table.append([_('bond_members') + ':', ', '.join(_master.members.keys())])
        _table.append([_('bond_mode') + ':', _printbond.mode])
        _table.append([_('load_balancing') + ':', _printbond.hash_policy])
        _table.append([_('minimum_links') + ':', _master.min_links])
        _lacp_info = self.iface.master.lacp
        if _lacp_info:
            _table.append([_('lacp_sys_priority') + ':', _master.lacp.sys_priority])
            _table.append([_('lacp_rate') + ':', _printbond.lacp_rate()])

        return tabulate(_table, _header) + self.new_line()

    def cli_output(self, show_legend=False):
        """
        cli output of the linux bond member interface
        :return: output for 'netshow interface <ifacename>'
        """
        _str = one_line_legend(show_legend)
        _str += self.cli_header()
        _str += self.bondmem_details()
        _str += self.lldp_details()
        _str += full_legend(show_legend)
        return _str


class PrintBond(PrintIface):
    """
    Print and Analysis Class for Linux bond interfaces
    """
    @property
    def port_category(self):
        """
        :return: port category for a bond
        """
        if self.iface.is_l3():
            return _('bond/l3')
        elif self.iface.is_trunk():
            return _('bond/trunk')
        elif self.iface.is_access():
            return _('bond/access')
        else:
            return _('bond')

    @property
    def summary(self):
        """
        :return: summary info for bonds for 'netshow interfaces'
        """
        _arr = []
        _arr.append(self.print_bondmems())
        _arr += PrintIface.summary.fget(self)
        if self.iface.is_trunk():
            _arr += self.trunk_summary()
        elif self.iface.is_access():
            _arr += self.access_summary()
        # remove empty entries
        return [_x for _x in _arr if _x]

    @property
    def hash_policy(self):
        """
        :return: hash policy for bond
        """
        _hash_policy = self.iface.hash_policy
        if _hash_policy == '1':
            return _('layer3+4')
        elif _hash_policy == '2':
            return _('layer2+3')
        elif _hash_policy == '0':
            return _('layer2')
        else:
            return _('unknown')

    @property
    def mode(self):
        """
        :return: name of the bond mode
        """
        _mode = self.iface.mode
        if _mode == '4':
            return _('lacp')
        elif _mode == '3':
            return _('broadcast')
        elif _mode == '2':
            return _('balance-xor')
        elif _mode == '1':
            return _('active-backup')
        elif _mode == '0':
            return _('balance-rr')
        else:
            return _('unknown')

    @classmethod
    def abbrev_bondstate(cls, bondmem):
        """
        :param bondmem: :class:`netshowlib.linux.BondMember` instance
        :return: 'P' if bondmem in bond
        :return: 'N' if bondmem is not in bond
        """
        if bondmem.bondstate == 1:
            return _('P')
        else:
            return _('N')

    def print_bondmems(self):
        """
        :return: bondmember list when showing summary in netshow interfaces \
            for the bond interface
        """
        _arr = []
        for _bondmem in self.iface.members.values():
            _arr.append("%s(%s%s)" % (_bondmem.name,
                                      self.abbrev_linksummary(_bondmem),
                                      self.abbrev_bondstate(_bondmem)))
        if len(_arr) > 0:
            return ': '.join([_('bondmems'), ', '.join(sorted(_arr))])
        else:
            return _('no_bond_members_found')

    def lacp_rate(self):
        """
        :return: lacp rate in plain english
        """
        _lacp = self.iface.lacp
        if _lacp:
            if _lacp.rate == '1':
                return _('fast_lacp')
            elif _lacp.rate == '0':
                return _('slow_lacp')
            else:
                return _('unknown')

    def bond_details(self):
        """
        print out table with bond details for netshow interface [ifacename]
        """
        _header = [_('bond_details'), '']
        _table = []
        _table.append([_('bond_mode') + ':', self.mode])
        _table.append([_('load_balancing') + ':', self.hash_policy])
        _table.append([_('minimum_links') + ':', self.iface.min_links])
        _lacp_info = self.iface.lacp
        if _lacp_info:
            _table.append([_('lacp_sys_priority') + ':', self.iface.lacp.sys_priority])
            _table.append([_('lacp_rate') + ':', self.lacp_rate()])
        return tabulate(_table, _header) + self.new_line()

    def bondmem_details(self):
        """
        print out table with bond member summary info for netshow interface [ifacename]
        for bond interface
        """
        _header = ['', _('port'), _('speed'), _('link_failures')]
        _table = []
        _bondmembers = self.iface.members.values()
        if len(_bondmembers) == 0:
            return _('no_bond_members_found')

        for _bondmem in _bondmembers:
            _printbondmem = PrintBondMember(_bondmem)
            _table.append([_printbondmem.linkstate,
                           "%s(%s)" % (_printbondmem.name,
                                       self.abbrev_bondstate(_bondmem)),
                           _printbondmem.speed,
                           _bondmem.linkfailures])

        return tabulate(_table, _header) + self.new_line()

    def lldp_details(self):
        """
        :return: lldp info for the bond members
        """
        _header = [_('lldp'), '', '']
        _table = []
        for _bondmem in self.iface.members.values():
            lldp_output = _bondmem.lldp
            if not lldp_output:
                continue
            _table.append(["%s(%s)" % (_bondmem.name,
                                       self.abbrev_bondstate(_bondmem)),
                           '====',
                           "%s(%s)" % (lldp_output[0].get('adj_port'),
                                       lldp_output[0].get('adj_hostname'))])
            del lldp_output[0]
            for _entry in lldp_output:
                _table.append(['', '====',
                               "%s(%s)" % (_entry.get('adj_port'),
                                           _entry.get('adj_hostname'))])

        if len(_table) > 0:
            return tabulate(_table, _header)
        else:
            return _('no_lldp_entries')

    def cli_output(self):
        """
        cli output of the linux bond interface
        :return: output for 'netshow interface <ifacename>'
        """
        _str = self.cli_header()
        _str += self.bond_details()
        _ip_details = self.ip_details()
        if _ip_details:
            _str += _ip_details
        _str += self.bondmem_details()
        _bridgemem_info = self.bridgemem_details()
        if _bridgemem_info:
            _str += _bridgemem_info
        _str += self.lldp_details()
        return _str
