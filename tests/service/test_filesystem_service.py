from pytest import fixture
from unittest.mock import patch, Mock
from cc_agency.broker.auth import Auth
from cc_cloud.service.filesystem_service import FilesystemService


class FakeConf:
    d = {
        'cc_cloud_directory': '/test',
        'upload_directory': '/test/users',
        'user_storage_limit': 52428800
    }

@fixture(autouse=True)
def fs_service():
    conf = FakeConf()
    return FilesystemService(conf=conf)


@fixture(autouse=True)
def user():
    username = 'testuser'
    is_admin = False
    return Auth.User(username=username, is_admin=is_admin)


@fixture(autouse=True)
def fs_name():
    return 'testuser'


@patch('os.system')
@patch('builtins.open', create=True)
@patch('os.makedirs')
def test_create_filesystem(mock_makedirs, mock_open, mock_system, fs_service, fs_name):
    fs_service.create(fs_name)
    
    mock_open.assert_called_once_with('/test/filesystems/testuser', 'a')
    mock_system.assert_called_once_with("mke2fs -t ext4 -F '/test/filesystems/testuser'")


@patch('os.path.exists')
def test_filessystem_exists(mock_exists, fs_service, fs_name):
    fs_service.filessystem_exists(fs_name)
    mock_exists.assert_called_once_with('/test/filesystems/testuser')


@patch('os.remove')
def test_delete(mock_remove, fs_service, fs_name):
    fs_service.delete(fs_name)
    mock_remove.assert_called_once_with('/test/filesystems/testuser')


@patch('os.system')
def test_mount(mock_system, fs_service, fs_name):        
    fs_service.mount(fs_name)
    mock_system.assert_called_once_with("mount '/test/filesystems/testuser' '/test/users/testuser'")


@patch('os.system')
def test_umount(mock_system, fs_service, fs_name):
    fs_service.umount(fs_name)
    mock_system.assert_called_once_with("umount '/test/filesystems/testuser'")


@patch('os.system', Mock(return_value=0))
def test_is_mounted_when_mounted(fs_service, fs_name):
    assert fs_service.is_mounted(fs_name) == True


@patch('os.system', Mock(return_value=8120))
def test_is_mounted_when_unmounted(fs_service, fs_name):
    assert fs_service.is_mounted(fs_name) == False


@patch('os.system')
@patch('builtins.open', create=True)
def test_increase_size(mock_open, mock_system, fs_service, fs_name):
    with patch.object(fs_service, 'get_loop_device', return_value='/dev/loop0'):
        fs_service.increse_size(fs_name, 104857600)
        
        mock_open.assert_called_once_with('/test/filesystems/testuser', 'a')
        mock_system.assert_any_call("losetup -c '/dev/loop0'")
        mock_system.assert_any_call("resize2fs '/dev/loop0'")


def test_reduce_size(fs_service, fs_name):
    with patch.object(fs_service, 'is_mounted', return_value=True), \
         patch.object(fs_service, 'umount'), \
         patch.object(fs_service, 'delete'), \
         patch.object(fs_service, 'create') as mock_create:
        
        fs_service.reduce_size(fs_name, 10000)
        
        mock_create.assert_called_once_with(fs_name, 10000)


@patch('os.path.getsize', return_value=50000)
def test_get_size(mock_getsize, fs_service, fs_name):
    size = fs_service.get_size(fs_name)
    
    mock_getsize.assert_called_once_with(fs_service.get_filepath(fs_name))
    assert size == 50000


@patch('os.popen')
def test_get_loop_device(mock_popen, fs_service, fs_name):
    mock_output = Mock()
    mock_output.read.return_value = '/dev/loop0: [2080]:14859 (/var/lib/cc_cloud/filesystems/testuser)'
    mock_popen.return_value = mock_output
    
    lo_device = fs_service.get_loop_device(fs_service.get_filepath(fs_name))
    
    assert lo_device == '/dev/loop0'


def test_get_filepath(fs_service, fs_name):
    filepath = fs_service.get_filepath(fs_name)
    assert filepath == '/test/filesystems/testuser'


def test_get_mountpoint(fs_service, fs_name):
    filepath = fs_service.get_mountpoint(fs_name)
    assert filepath == '/test/users/testuser'


@patch.object(FilesystemService, "filessystem_exists", return_value=False)
@patch.object(FilesystemService, "create")
@patch.object(FilesystemService, "is_mounted", return_value=False)
@patch.object(FilesystemService, "mount")
def test_exists_or_create_False(mock_mount, mock_is_mounted, mock_create, mock_filesystem_exists, fs_service, fs_name):
    fs_service.exists_or_create(fs_name)

    mock_filesystem_exists.assert_called_once_with(fs_name)
    mock_create.assert_called_once_with(fs_name)
    mock_is_mounted.assert_called_once_with(fs_name)
    mock_mount.assert_called_once_with(fs_name)


@patch.object(FilesystemService, "filessystem_exists", return_value=True)
@patch.object(FilesystemService, "create")
@patch.object(FilesystemService, "is_mounted", return_value=True)
@patch.object(FilesystemService, "mount")
def test_filesystem_exists_or_create_True(mock_mount, mock_is_mounted, mock_create, mock_filesystem_exists, fs_service, fs_name):
    fs_service.exists_or_create(fs_name)

    mock_filesystem_exists.assert_called_once_with(fs_name)
    mock_create.assert_not_called()
    mock_is_mounted.assert_called_once_with(fs_name)
    mock_mount.assert_not_called()