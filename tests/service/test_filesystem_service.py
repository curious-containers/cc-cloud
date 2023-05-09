from unittest.mock import Mock
from unittest.mock import patch

from cc_agency.broker.auth import Auth
from cc_agency.commons.conf import Conf
from cc_agency.commons.db import Mongo

from cc_cloud.service.filesystem_service import FilesystemService


conf = Conf('dev/cc-agency.yml')
mongo = Mongo(conf)
auth = Auth(conf, mongo)
user = Auth.User('test_user', False)

file_service = FilesystemService('')

@patch('cc_cloud.service.filesystem_service.os.system')
def test_mount(mock_system):
    file_service.mount(user)
    mock_system.assert_called_once_with("mount '/var/lib/cc_cloud/filesystems/test_user' '/var/lib/cc_cloud/users/test_user'")

@patch('cc_cloud.service.filesystem_service.os.system')
def test_umount(mock_system):
    file_service.umount(user)
    mock_system.assert_called_once_with("umount '/var/lib/cc_cloud/filesystems/test_user'")

