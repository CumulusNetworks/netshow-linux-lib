# pylint: disable-msg=E0611
"""
This module produces the cache info for Linux
"""

from netshowlib import netshowlib as nnlib


class Cache(object):
    """
    This class produces the cache info for Linux \
        networking such as ip addressing, lldp, QOS
    """
    def __init__(self):
        self.feature_list = {'ip_neighbor': 'linux',
                             'lldp': 'linux',
                             'counters': 'linux',
                             'ip_address': 'linux'}

    def run(self, features=None):
        """
        :param features:  List of features to enable. If set to ``None`` \
            cache from all features is obtained

        :return:  returns Cache instance of appropriate OS type
        """
        _featurelist = self.feature_list
        if features:
            _featurelist = features

        for _feature, _provider in _featurelist.items():
            _feature_mod = nnlib.import_module("netshowlib.%s.%s" % (_provider,
                                                                     _feature))
            self.__dict__[_feature] = _feature_mod.cacheinfo()
