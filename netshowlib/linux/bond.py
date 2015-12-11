""" This module is responsible for finding properties
related to bond interface and bond member interfaces """
from collections import OrderedDict
import netshowlib.linux.iface as linux_iface
import netshowlib.linux.bridge as linux_bridge
import netshowlib.linux.lacp as lacp
import re
import io


class Bond(linux_iface.Iface):
    """ Linux Bond attributes

    * **members**: list of bond members/slaves. creates instances of \
    :class:`BondMember<netshowlib.linux.bond_member.BondMember>`
    * **bond mode**: options are

      * *balance-rr    '0'*
      * *active-backup '1'*
      * *balance-xor   '2'*
      * *balance-alb   '3'*
      * *802.3ad       '4'*
      * *balance-tlb   '5'*
      * *balance-alb   '6'*

    * **min_links**: number of minimum links
    * **hash_policy**: load balancing algorithm. options are

      * *layer2    '0'*
      * *layer3+4  '1'*

    * **lacp**: pointer to :class:`Lacp instance<netshowlib.linux.lacp.Lacp>` for this \
        bond
    * **system_mac**: Bond system mac. Packets egressing bond use this mac address.

    """
    def __init__(self, name, cache=None):
        linux_iface.Iface.__init__(self, name, cache)
        self._members = {}
        self._mode = None
        self._min_links = None
        self._hash_policy = None
        self._lacp = None
        self._system_mac = None
        self._stp = None
        self._bridge_masters = {}
        self.bridge = linux_bridge
        self._cache = cache
        self.bondmem_class = BondMember
        self.lacp_class = lacp.Lacp
        self.bondfileloc = '/proc/net/bonding'

    # -------------------

    def _parse_proc_net_bonding(self, bondfile):
        """
        parse ``/proc/net/bonding`` of this bond to get the system mac
        eventually this info will be in the kernel. I believe its
        kernel 3.18 or something. will confirm with a kernel dev.

        :param bondfile: path to /proc/net file for the bond
        """
        try:
            result = io.open(bondfile).read()
        except (ValueError, IOError):
            return
        fileio = io.StringIO(result)
        for line in fileio:
            if len(line.strip()) <= 0:
                continue
            # make all char lowercase
            line = line.lower()
            # determine mac address of the bond
            if re.match(r'system\s+identification', line):
                self._system_mac = line.split()[-1]
                continue

    # ---------------------
    # Define properties

    @property
    def stp(self):
        """
        :return: KernelStpBridgeMember instance
        """
        if not self._stp:
            self._stp = linux_bridge.KernelStpBridgeMember(self,
                                                           self._cache)
        return self._stp

    @property
    def bridge_masters(self):
        """
        :return: list of bridges associated with this port \
            and its subinterfaces.
        """
        self._bridge_masters = {}
        bridgename = self.read_symlink('brport/bridge')
        if bridgename:
            if linux_bridge.BRIDGE_CACHE.get(bridgename):
                bridgeiface = linux_bridge.BRIDGE_CACHE.get(bridgename)
            else:
                bridgeiface = self.bridge.Bridge(bridgename, cache=self._cache)
            self._bridge_masters[bridgeiface.name] = bridgeiface

        for subintname in self.get_sub_interfaces():
            subiface = linux_iface.Iface(subintname)
            bridgename = subiface.read_symlink('brport/bridge')
            if bridgename:
                if linux_bridge.BRIDGE_CACHE.get(bridgename):
                    bridgeiface = linux_bridge.BRIDGE_CACHE.get(bridgename)
                else:
                    bridgeiface = self.bridge.Bridge(bridgename, cache=self._cache)
                self._bridge_masters[bridgeiface.name] = bridgeiface

        return self._bridge_masters

    @property
    def members(self):
        """
        :return: list of bond members
        """
        fileoutput = self.read_from_sys('bonding/slaves')
        # if bond member list has changed..clear the bond members hash
        if fileoutput:
            if set(fileoutput.split()) != set(self._members.keys()):
                self._members = OrderedDict()
                for i in fileoutput.split():
                    self._members[i] = self.bondmem_class(i, master=self)
        else:
            self._members = {}

        return self._members

    @property
    def mode(self):
        """
        :return: bond mode integer. Not the name. See \
            `linux kernel driver docs <http://bit.ly/1BSyeVh>`_ for more details
        """
        self._mode = None
        fileoutput = self.read_from_sys('bonding/mode')
        if fileoutput:
            self._mode = fileoutput.split()[1]
        return self._mode

    @property
    def min_links(self):
        """
        :return: number of minimum links required to keep the bond active
        """
        self._min_links = self.read_from_sys('bonding/min_links')
        return self._min_links

    @property
    def hash_policy(self):
        """
        :return: bond load balancing policy / xmit hash policy
        """
        self._hash_policy = None
        fileoutput = self.read_from_sys('bonding/xmit_hash_policy')
        if fileoutput:
            self._hash_policy = fileoutput.split()[1]
        return self._hash_policy

    @property
    def lacp(self):
        """
        :return: :class:`linux.lacp<netshowlib.linux.lacp.Lacp>` class instance if \
            bond is in LACP mode

        """
        if self.mode == '4':
            if not self._lacp:
                self._lacp = self.lacp_class(self.name)
            return self._lacp
        return None

    @property
    def system_mac(self):
        """
        :return: bond system mac
        """
        self._system_mac = None
        bond_proc_file = "%s/%s" % (self.bondfileloc, self.name)
        self._parse_proc_net_bonding(bond_proc_file)
        return self._system_mac

    def __str__(self):
        """
        string output function for the class
        """
        return "Linux Bond Interface '%s'. Member Count: %s" % (self.name,
                                                                len(self.members.keys()))


class BondMember(linux_iface.Iface):
    """ Linux Bond Member Attributes

    * **master**: pointer to :class:`Bond<netshowlib.linux.bond.Bond>` instance \
        that this interface belongs to. This can be provided in the ``__init__`` \
        function
    * **linkfailures**: bond driver reports number of times bond member flaps
    * **bondstate**: returns whether bond member is active (1) or inactive(0) in a bond \
        **irrespective** of its carrier/linkstate status. What this means is that \
        the link can be up, but not in the bond.
    Examples:

    .. code-block:: python

        import netshowlib.netshowlib as nn

        # bond member info should be normally obtained from
        # first calling the bond and then running the members
        # property.
        bond0 = nn.bond.Bond('bond0')
        print len(bond0.members.keys())
        >> 2

        # on the rare case you know the bond member but want to get
        # bond master information you can.
        bondmem = nn.bond_member.BondMember('eth1')
        print bondmem.master
        >> Linux Bond Interface 'bond0'. Member Count: 1

    """
    def __init__(self, name, cache=None, master=None):
        linux_iface.Iface.__init__(self, name, cache)
        self._master = master
        self._linkfailures = 0
        self._bondstate = None
        self.bond_class = Bond
        self.bondfileloc = '/proc/net/bonding'
    # -------------------
    # Get link failure count.
    # determine if member is in bond by checking agg ID
    # parse /proc/net/bonding to get this info
    # J Toppins informed me that this is most generic way to get
    # bonding info across multiple linux platforms.
    # grabbing it from /sys/class/net is not super reliable
    # eventually everything can be grabbed from netlink, which will be done
    # in a future release.

    def _parse_proc_net_bonding(self):
        """
        parse /proc/net/bonding to get link failure and agg_id info
        """
        # open proc/net/bonding
        if not self.master:
            return

        bondfile = "%s/%s" % (self.bondfileloc, self.master.name)
        try:
            result = io.open(bondfile).read()
        except (ValueError, IOError):
            return
        bondslavename = None
        fileio = io.StringIO(result)
        master_agg_id = None
        for line in fileio:
            if len(line.strip()) <= 0:
                continue
            # make all char lowercase
            line = line.lower()
            # get bondslave name
            if re.match(r'slave\s+interface', line):
                bondslavename = line.split()[-1]
                continue
            elif re.match(r'\s+aggregator\s+id', line):
                master_agg_id = line.split()[-1]
                continue
            elif re.match(r'aggregator\s+id', line):
                if bondslavename == self.name:
                    agg_id = line.split()[2]
                    _state = 1 if master_agg_id == agg_id else 0
                    self._bondstate = _state
            elif re.match(r'link\s+failure', line):
                _count = line.split()[-1]
                if bondslavename == self.name:
                    self._linkfailures = int(_count)

    # -------------------

    # Define properties

    @property
    def master(self):
        """
        :return: pointer to  :class:`Bond<netshowlib.linux.bond.Bond>` instance that \
        this interface belongs to
        """
        if hasattr(self, '_master'):
            if not self._master:
                bondname = self.read_symlink('master')
                self._master = self.bond_class(bondname)
            return self._master

    @property
    def bondstate(self):
        """
        :return: state of interface in the bond. can be 0(inactive) or 1(active)
        """
        # if LACP check /proc/net/bonding for agg matching state
        if self.master and self.master.mode == '4':
            self._parse_proc_net_bonding()
        else:
            self._bondstate = 1 if self.linkstate == 2 else 0

        return self._bondstate

    @property
    def linkfailures(self):
        """
        number of mii transitions bond member reports while the bond is active
        this counter cannot be cleared. will reset when the bond is reinitialized
        via the ifdown/ifup process

        :return: number of mii transitions
        """
        self._parse_proc_net_bonding()
        return self._linkfailures
