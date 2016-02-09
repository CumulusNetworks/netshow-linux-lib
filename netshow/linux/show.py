# print() is required for py3 not py2. so need to disable C0325
# pylint: disable=C0325
"""
Usage:
    netshow system [--json | -j ]
    netshow lldp [--json | -j | -l | --legend]
    netshow interface [<iface>] [all] [--mac | -m ] [--oneline | -1 | --json | -j | -l | --legend ]
    netshow access [all] [--mac | -m ] [--oneline | -1  | --json | -j | -l | --legend ]
    netshow bridges [all] [--mac | -m ] [--oneline | -1  | --json | -j | -l | --legend ]
    netshow bonds [all] [--mac | -m ] [--oneline | -1  | --json | -j | -l | --legend ]
    netshow bondmems [all] [--mac | -m ] [--oneline | -1  | --json | -j | -l | --legend ]
    netshow l2 [all] [--mac | -m ] [--oneline | -1  | --json | -j | -l | --legend ]
    netshow l3 [all] [--mac | -m ] [--oneline | -1  | --json | -j | -l | --legend ]
    netshow trunks [all] [--mac | -m ] [--oneline | -1  | --json | -j | -l | --legend ]
    netshow counters [errors] [all]
    netshow (--version | -V)


Help:
    * default is to show intefaces only in the UP state.
    interface                 summary info of all interfaces
    access                    summary of physical ports with l2 or l3 config
    bonds                     summary of bonds
    bondmems                  summary of bond members
    bridges                   summary of ports with bridge members
    l3                        summary of ports with an IP.
    l2                        summary of access, trunk and bridge interfaces
    trunks                    summary of trunk interfaces
    lldp                      physical device neighbor information
    interface <iface>         list summary of a single interface
    system                    system information
    counters                  basic interface counters


Options:
    all        show all ports include those are down or admin down
    --mac      show inteface MAC in output
    --version  netshow software version
    --oneline  output each entry on one line
    -1         alias for --oneline
    --json     print output in json
    -l         alias for --legend
    --legend   print legend key explaining abbreviations
"""
import sys
from network_docopt import NetworkDocopt
from netshow.netshow import print_version
from netshow.linux.show_system import ShowSystem
from netshow.linux.show_interfaces import ShowInterfaces
from netshow.linux.show_neighbors import ShowNeighbors
from netshow.linux.show_counters import ShowCounters


def interface_related(_nd):
    """
    return: True if option inputed requires ShowInterfaces() to be activated
    """
    for _entry in ['access', 'bridges', 'bonds', 'bondmems',
                   'mgmt', 'l2', 'l3', 'phy', 'trunks', 'interface']:
        if _nd.get(_entry):
            return True
    return False


def run():
    """ run cumulus netshow version """
    if sys.argv[-1] == 'options':
        print_options = True
        sys.argv = sys.argv[0:-1]
    else:
        print_options = False

    _nd = NetworkDocopt(__doc__)
    if print_options:
        _nd.print_options()
    else:
        if interface_related(_nd):
            _showint = ShowInterfaces(_nd)
            print(_showint.run())
        elif _nd.get('system'):
            _showsys = ShowSystem(_nd)
            print(_showsys.run())
        elif _nd.get('lldp'):
            _shownei = ShowNeighbors(_nd)
            print(_shownei.run())
        elif _nd.get('counters'):
            _showcounters = ShowCounters(_nd)
            print(_showcounters.run())
        elif _nd.get('--version') or _nd.get('-V'):
            print(print_version())
        else:
            print(__doc__)
