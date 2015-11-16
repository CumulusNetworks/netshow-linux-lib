# http://pylint-messages.wikidot.com/all-codes
# attribute defined outside init
# pylint: disable=W0201
# pylint: disable=R0913
# disable unused argument
# pylint: disable=W0613
# disable docstring checking
# pylint: disable=C0111
# disable checking no-self-use
# pylint: disable=R0201
# pylint: disable=W0212
# disable invalid name
# pylint: disable=C0103
# pylint: disable=F0401
# pylint: disable=E0611
# pylint: disable=W0611

from asserts import assert_equals
import netshow.linux.show_system as show_system
import mock
import io
import json


class TestShowSystem(object):

    @mock.patch('netshowlib.linux.system_summary.common.exec_command')
    def test_show_system_run_json_output(self, mock_command):
        mock_output = io.open('tests/test_netshow/lsb_release.txt').read()
        mock_command.return_value = mock_output
        test_system = show_system.ShowSystem({'--json': ''})
        test_system.use_json = True
        output = test_system.run()
        osname = json.loads(output).get('system_dict').get('os_name')
        assert_equals(osname, 'Debian')

#    def test_show_system_run_no_json():
#        test_system = show_system.SystemSummary()
#        test_system.use_json = False
#        output = test_system.run()
#        assert_equals('', output)
