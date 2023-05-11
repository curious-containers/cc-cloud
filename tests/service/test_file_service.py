from pytest import fixture, mark
from unittest.mock import patch, Mock
from werkzeug.datastructures import FileStorage

from cc_agency.broker.auth import Auth
from cc_cloud.service.filesystem_service import FilesystemService
from cc_cloud.service.file_service import FileService


class MockConf:
    d = {
        'cc_cloud_directory': '/test',
        'upload_directory': '/test/users',
        'user_storage_limit': 52428800
    }

@fixture(autouse=True)
def file_service():
    conf = MockConf()
    return FileService(conf)

@fixture(autouse=True)
def user():
    username = 'testuser'
    is_admin = False
    return Auth.User(username=username, is_admin=is_admin)


@patch.object(FilesystemService, "user_filessystem_exists", return_value=False)
@patch.object(FilesystemService, "create")
@patch.object(FilesystemService, "is_mounted", return_value=False)
@patch.object(FilesystemService, "mount")
def test_filesystem_exists_or_create_False(mock_mount, mock_is_mounted, mock_create, mock_filesystem_exists, user, file_service):
    file_service.filesystem_exists_or_create(user)

    mock_filesystem_exists.assert_called_once_with(user)
    mock_create.assert_called_once_with(user)
    mock_is_mounted.assert_called_once_with(user)
    mock_mount.assert_called_once_with(user)


@patch.object(FilesystemService, "user_filessystem_exists", return_value=True)
@patch.object(FilesystemService, "create")
@patch.object(FilesystemService, "is_mounted", return_value=True)
@patch.object(FilesystemService, "mount")
def test_filesystem_exists_or_create_True(mock_mount, mock_is_mounted, mock_create, mock_filesystem_exists, user, file_service):
    file_service.filesystem_exists_or_create(user)

    mock_filesystem_exists.assert_called_once_with(user)
    mock_create.assert_not_called()
    mock_is_mounted.assert_called_once_with(user)
    mock_mount.assert_not_called()


@mark.parametrize('test_path, expected_path',[
    ('some/path/file.txt', True),
    ('some/path/../file.txt', True),
    ('/some/path/file.txt', True),
    ('.file.txt', True),
    ('../some/path/file.txt', False),
    ('some/../../path/file.txt', False),
])
def test_is_secure_path(test_path, expected_path, user, file_service):
    result = file_service.is_secure_path(user, test_path)
    assert result == expected_path


def test_get_user_upload_directory(user, file_service):
    result = file_service.get_user_upload_directory(user)
    assert result == '/test/users/testuser'


@mark.parametrize('test_file, expected_file',[
    ('some/path/file.txt', '/test/users/testuser/some/path/file.txt'),
    ('/file.txt', '/test/users/testuser/file.txt')
])
def test_get_full_filepath(test_file, expected_file, user, file_service):
    result = file_service.get_full_filepath(user, test_file)
    assert result == expected_file


@patch('os.path.isfile', return_value=True)
@patch('os.remove', Mock())
@patch.object(FileService, "filesystem_exists_or_create", Mock(return_value=True))
def test_delete_file_success(user, file_service):
    path = '/some/path/file.txt'
    result = file_service.delete_file(user, path)
    assert result == True


@patch('os.path.isfile', return_value=True)
@patch('os.remove', Mock(side_effect=OSError()))
@patch.object(FileService, "filesystem_exists_or_create", Mock(return_value=True))
def test_delete_file_failure(user, file_service):
    path = '/some/path/file.txt'
    result = file_service.delete_file(user, path)
    assert result == False


@patch('os.path.isfile', return_value=False)
@patch('cc_cloud.service.file_service.shutil.rmtree', Mock())
@patch.object(FileService, "filesystem_exists_or_create", Mock(return_value=True))
def test_delete_file_success_dir(user, file_service):
    path = '/some/path'
    result = file_service.delete_file(user, path)
    assert result == True


@patch('os.path.isfile', return_value=False)
@patch('cc_cloud.service.file_service.shutil.rmtree', Mock(side_effect=OSError()))
@patch.object(FileService, "filesystem_exists_or_create", Mock(return_value=True))
def test_delete_file_failure_dir(user, file_service):
    path = '/some/path'
    result = file_service.delete_file(user, path)
    assert result == False
    

@patch.object(FileService, "filesystem_exists_or_create", Mock(return_value=True))
def test_upload_file(user, file_service):
    file1 = FileStorage(filename='/some/path/file1.txt')
    file2 = FileStorage(filename='file2.txt')
    file1.save = Mock()
    file2.save = Mock()
    
    files = {
        "file1": file1,
        "file2": file2
    }
    
    file_service.upload_file(user, files)

    file1.save.assert_called_once()
    file2.save.assert_called_once()


@patch.object(FileService, "filesystem_exists_or_create", Mock(return_value=True))
def test_download_file(user, file_service):
    filepath = '/some/path/file1.txt'
    result = file_service.download_file(user, filepath)
    assert result == '/test/users/testuser/some/path/file1.txt'
