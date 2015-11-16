# pylint: disable=E0611
""" Module for printing out basic linux system information
"""

from netshowlib.linux.system_summary import SystemSummary
from datetime import timedelta
import json
from netshow.linux.netjson_encoder import NetEncoder
from netshow.linux.common import _


class ShowSystem(object):
    """
    Class responsible for printing out basic linux system summary info
    """
    def __init__(self, cl):
        self.use_json = cl.get('--json') or cl.get('-j')
        self.system = SystemSummary()

    def run(self):
        """
        :return: output regarding system like OS type, etc
        """
        self.system.run()
        if self.use_json:
            return json.dumps(self,
                              cls=NetEncoder, indent=4)
        else:
            return self.cli_output()

    def cli_output(self):
        """
        print linux basic system output on a terminal
        """
        _str = ''
        _str += "%s %s\n" % (self.system.os_name,
                             self.system.version)
        _str += "%s: %s\n" % (_('build'), self.system.os_build)
        _str += "%s: %s\n" % (_('uptime'), self.uptime)
        return _str

    @property
    def uptime(self):
        """
        :return: system uptime in humanly readable form
        """
        return str(timedelta(
            seconds=int(float(self.system.uptime))))
