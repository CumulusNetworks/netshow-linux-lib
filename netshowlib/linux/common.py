# pylint: disable=E0611
# pylint: disable=W0403
# pylint: disable=W0612
""" Linux common module
"""
import subprocess
import re
from itertools import groupby
from operator import itemgetter
from collections import OrderedDict
import os


class ExecCommandException(Exception):
    """
    Exception when a  exec command fails
    """
    pass

# ### Common Functions used in this project

SYS_PATH_ROOT = '/sys/class/net'


def portname_list():
    """
    :return: list of interface names from /sys/class/net
    """
    ifacenames = os.listdir(SYS_PATH_ROOT)
    for ifacename in ifacenames:
        if not os.path.islink(os.path.join(SYS_PATH_ROOT,
                                           ifacename)):
            ifacenames.remove(ifacename)
    return ifacenames


def sys_path(attr, iface_name):
    """
    :params attr: attribute under /sys/class/net/:meth:`name`
    :return: full path of the sysfs attribute
    """
    return '%s/%s/%s' % (SYS_PATH_ROOT, iface_name, attr)


def read_from_sys(attr, iface_name, oneline=True):
    """ reads an attribute found in thev
    ``/sys/class/net/[iface_name]/`` directory
    """
    _path = sys_path(attr, iface_name)
    if oneline:
        return read_file_oneline(_path)
    else:
        return read_file(_path)


def generate_cidr_ip(addr):
    """ generate address in CIDR format
    Example: 10.1.1.1/24 instead of 10.1.1.1 mask 255.255.255.0
    """
    _ip = addr['addr']
    mask = netmask_dot_notation_to_cidr(addr['netmask'])
    return "%s/%s" % (_ip, str(mask))


def read_symlink(filepath):
    """
    read symlink.

    :param filepath: path to the directory, file to check
    """
    try:
        return os.readlink(filepath).split('/')[-1]
    except OSError:
        return None


def check_bit(int_type, offset):
    """ copied from wiki.python.org
    if testBit is not zero, return checkBit as True
    """
    return test_bit(int_type, offset) > 0


def test_bit(int_type, offset):
    """
    * from wiki.python.org *
    :return: nonzero result, 2**offset, if the bit is 'offset' is one
    """
    mask = 1 << offset
    return int_type & mask


def set_bit(int_type, offset):
    """
    :return: an integer with the bit at 'offset' set to 1
    """
    mask = 1 << offset
    return int_type | mask


def clear_bit(int_type, offset):
    """
    :return: integer with the bit at 'offset' cleared
    """
    mask = ~(1 << offset)
    return int_type & mask


def dict_merge(list1, list2):
    """ merge two dicts by overriding content in first dict with
    content from 2nd dict. does not return a new merge dict.
    all merging takes place in the first dict.

    :param list1: original dict
    :param list2: dict to override original dict content
    """

    _keys2 = list2.keys()
    for _key in _keys2:
        try:
            list1[_key].__dict__.update(list2[_key].__dict__)
        except KeyError:
            list1[_key] = list2[_key]


# _obtained from stackoverflow
def netmask_dot_notation_to_cidr(netmask):
    """
    Example: takes '255.255.225.0' and returns '24'
    :param netmask: netmask in decimal form
    :return: netmask in CIDR format
    """
    is_ipv6 = re.match(r'\w+:', netmask)
    if is_ipv6:
        base = 16
    else:
        base = 10
    split_str = re.split('[.:]', netmask)
    split_str = ['0' if x == '' else x for x in split_str]
    return sum([bin(int(x, base)).count('1') for x in split_str])


# Copied from [ifupdown2](http://github.com/CumulusNetworks/ifupdown2) project
def read_file(filename):
    """
    read a file and return an array of lines
    """
    try:
        with open(filename, 'r') as _file:
            return _file.readlines()
    except IOError:
        return None
    return None


# copied from [ifupdown2](http://github.com/cumulusnetworks/ifupdown2) project
def read_file_oneline(filename):
    """
    reads one line files. returns content
    """
    try:
        with open(filename, 'r') as _file:
            return _file.readline().strip('\n')
    except IOError:
        return None
    return None


# copied from [ifupdown2](http://github.com/cumulusnetworks/ifupdown2) project
def exec_commandl(cmdl, cmdenv=None):
    """
    execute a command
    """
    cmd_returncode = 0
    cmdout = u''
    try:
        _ch = subprocess.Popen(cmdl,
                               stdout=subprocess.PIPE,
                               shell=False, env=cmdenv,
                               stderr=subprocess.STDOUT,
                               close_fds=True)
        cmdout = _ch.communicate()[0]
        cmd_returncode = _ch.wait()
    except OSError as _err:
        raise ExecCommandException('failed to execute cmd \'%s\' (%s)'
                                   % (' '.join(cmdl), str(_err)))
    if cmd_returncode != 0:
        raise ExecCommandException('failed to execute cmd \'%s\''
                                   % ' '.join(cmdl) + '(' + cmdout.strip('\n ') + ')')
    return cmdout.decode('utf-8')


# copied from [ifupdown2](http://github.com/cumulusnetworks/ifupdown2) project
def exec_command(cmd, cmdenv=None):
    """
    execute a command
    """
    return exec_commandl(cmd.split(), cmdenv)


# Example: rkey is 'swp', rgroup is 'swp2, swp3, swp10'
def create_range(rkey, rgroup):
    """
    :param rkey: if rey is *swp*,  rgroup is *"swp2, swp3, swp10"*
    create a range list given a list of ports with a common pattern
    """
    range_list = []
    if len(rgroup) == 1:
        return rgroup

    try:
        strip_key_list = sorted([int(re.sub(rkey, '', i)) for i in rgroup])
    except ValueError:
        return rgroup
    for _key, _group in groupby(enumerate(strip_key_list),
                                lambda i_x: i_x[0] - i_x[1]):
        _tmp_range = [itemgetter(1)(x) for x in _group]
        if len(_tmp_range) == 1:
            range_list.append("%s%s" %
                              (rkey, _tmp_range[0]))
        else:
            range_list.append("%s%s-%s" %
                              (rkey, _tmp_range[0], _tmp_range[-1]))

    return range_list


def grouping_func(xvar):
    """
    group ports based on 2 criteria. If name is like so
    'bond0', 'swp22', 'br-vlan22', 'vlan33', group it by
    name. So for example 'bond0', 'bond1', would be under the 'bond' group.
    2nd criteria is by vlan number. If the ports are 'swp1.100, swp2.100'
    group it by '100'. So Dict entry would be '100' -> 'swp1.100', 'swp2.100'
    """
    my_match = re.match(r'^([a-z0-9_-]+[a-z_-])\d+$', xvar.lower())
    if my_match:
        return my_match.group(1)
    my_match = re.match(r'.*\.(\d+)$', xvar.lower())
    if my_match:
        return my_match.group(1)
    return xvar.lower()


def group_iface(initial_list, group_func):
    """
    groups iface values
    """
    bvar = OrderedDict()
    gbvar = groupby(initial_list, group_func)
    for k, avar in gbvar:
        try:
            bvar[k] = bvar[k] + [str(x) for x in avar]
        except KeyError:
            bvar[k] = [str(x) for x in avar]
    return bvar


def group_ports(list_of_ports):
    """
    create group list of ports given a list of ports. Example:
    'swp1, swp2, bond0, bond1, swp3.100, swp4.100' becomes
    'swp1-2, swp3-4.100, bond0-1'
    """
    bvar = group_iface(list_of_ports, grouping_func)
    newdct = OrderedDict((key, bvar[key]) for key in sorted(bvar.keys()))
    final_list = []
    for _kvar, _var in newdct.items():
        try:
            if int(_kvar):
                strip_tag_list = [re.sub(r'\.\d+$', '', i) for i in _var]
                cvar = group_iface(strip_tag_list, grouping_func)
                for _k2, _v2 in cvar.items():
                    _tmp_arr = create_range(_k2, _v2)
                    final_list += ["%s.%s" % (i, _kvar) for i in _tmp_arr]
        except ValueError:
            final_list += create_range(_kvar, _var)
    return final_list


def munge_str(match0):
    """
    sorting by string that is int,
    produces wrong sort..so change str that
    is int into a int type
    """
    tvar = []
    if match0:
        tvar.append(match0.group(1))
        for i in range(2, 5):
            _match = match0.group(i)
            if _match:
                tvar.append(_match)
            else:
                tvar.append('')
    return tvar

def create_sort_tuple(result):
    """
    returns tuple value used for sorting. Example
    ('bond', '0', '.' , '1') converts it to
    ('bond', 0, 0, 1) for the sort
    another example
    ('vlan', '10', '-v', '0') converts to
    ('vlan', 10, 0, 0) for the sort.
    """
    new_tuple = []
    for i in result:
        try:
            new_tuple.append(int(i))
        except ValueError:
            if i == '' or i.startswith('.') or i.startswith('-'):
                new_tuple.append(0)
            else:
                new_tuple.append(i)
    return tuple(new_tuple)


# Given a port list ['swp1', 'bond10.100', 'swp3.100']
# sort it to it looks like this
# ['bond10.100', 'swp1', 'swp3.100']
def sort_ports(list_of_ports):
    """
    Given a port list ['swp1', 'bond10.100', 'swp3.100']
    sort it to it looks like this
    ['bond10.100', 'swp1', 'swp3.100']
    """
    tuple_array = []
    sorted_array = []
    for i in list_of_ports:
        _match = re.match(r'(\w+[A-Za-z])(\d+)?([.-]?v?)(\d+)?', i)
        if _match:
            tvar = munge_str(_match)
        else:
            tvar = [i]
        tuple_array.append(tuple(tvar))
    sorted_tuple_array = sorted(tuple_array, key=create_sort_tuple)
    for i in sorted_tuple_array:
        entry = []
        # join doesnt work with int type. convert int to str
        entry.append(str(i[0]))
        if len(i) > 1 and i[1] != '':
            entry.append(str(i[1]))
        if len(i) > 2 and i[2] != '':
            entry.append(str(i[2]))
            entry.append(str(i[3]))
        sorted_array.append(''.join(entry))
    return sorted_array
