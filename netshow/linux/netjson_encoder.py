# pylint: disable=E0202
"""
Module for Converting python class attributes into JSON
"""
from json import JSONEncoder


class NetEncoder(JSONEncoder):
    """
    NetEncoder is my custom JSONEncoder class that prints out
    the json output of any PrintIface Class or subclass.
    """
    def default(self, obj):
        # print out properties
        property_names = [_p for _p in dir(obj.__class__) if isinstance(
            getattr(obj.__class__, _p), property)]
        _hash = {}
        for _property in property_names:
            if _property == 'bridge_masters':
                continue
            _hash[_property] = getattr(obj, _property)
        if hasattr(obj, 'bridge_masters'):
            _hash['bridge_masters'] = obj.bridge_masters.keys()
        if hasattr(obj, 'state'):
            _hash['state'] = obj.state.keys()
        if hasattr(obj, 'members'):
        #    _hash['members'] = obj.members.keys()
             _hash['members'] = {}
             for (_k, _v) in obj.members.items():
                if hasattr(_v, '_master'):
                    _v.__dict__.pop('_master')
                if hasattr(_v, 'bond_class'):
                    _v.__dict__.pop('bond_class')
                _hash['members'][_k] = _v
        if hasattr(obj, 'iface'):
            _hash['iface_obj'] = obj.iface
        if hasattr(obj, 'system'):
            _hash['system_obj'] = obj.system
            _hash['system_dict'] = obj.system.__dict__

        return _hash
