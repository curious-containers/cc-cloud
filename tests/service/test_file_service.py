from pytest import fixture, mark
from unittest.mock import patch, Mock
from werkzeug.datastructures import FileStorage

from cc_agency.broker.auth import Auth
from cc_cloud.service.filesystem_service import FilesystemService
from cc_cloud.service.file_service import FileService


class MockConf:
    d = {
        'upload_directory_name': 'cloud',
        'userhome_directory': '/test/users',
        'filesystem_directory': '/test/filesystems',
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

@fixture(autouse=True)
def user_ref():
    return 'testuser'


@mark.parametrize('test_path, expected_path',[
    ('some/path/file.txt', True),
    ('some/path/../file.txt', True),
    ('/some/path/file.txt', True),
    ('.file.txt', True),
    ('../some/path/file.txt', False),
    ('some/../../path/file.txt', False),
])
def test_is_secure_path(test_path, expected_path, user_ref, file_service):
    result = file_service.is_secure_path(user_ref, test_path)
    assert result == expected_path


def test_get_user_upload_directory(user_ref, file_service):
    result = file_service.get_user_upload_directory(user_ref)
    assert result == '/test/users/testuser/cloud'


@mark.parametrize('test_file, expected_file',[
    ('some/path/file.txt', '/test/users/testuser/cloud/some/path/file.txt'),
    ('/file.txt', '/test/users/testuser/cloud/file.txt')
])
def test_get_full_filepath(test_file, expected_file, user_ref, file_service):
    result = file_service.get_full_filepath(user_ref, test_file)
    assert result == expected_file


@patch('os.path.isfile', return_value=True)
@patch('os.remove', Mock())
@patch.object(FilesystemService, "exists_or_create", Mock(return_value=True))
def test_delete_file_success(user_ref, file_service):
    path = '/some/path/file.txt'
    result = file_service.delete_file(user_ref, path)
    assert result == True


@patch('os.path.isfile', return_value=True)
@patch('os.remove', Mock(side_effect=OSError()))
@patch.object(FilesystemService, "exists_or_create", Mock(return_value=True))
def test_delete_file_failure(user_ref, file_service):
    path = '/some/path/file.txt'
    result = file_service.delete_file(user_ref, path)
    assert result == False


@patch('os.path.isfile', return_value=False)
@patch('cc_cloud.service.file_service.shutil.rmtree', Mock())
@patch.object(FilesystemService, "exists_or_create", Mock(return_value=True))
def test_delete_file_success_dir(user_ref, file_service):
    path = '/some/path'
    result = file_service.delete_file(user_ref, path)
    assert result == True


@patch('os.path.isfile', return_value=False)
@patch('cc_cloud.service.file_service.shutil.rmtree', Mock(side_effect=OSError()))
@patch.object(FilesystemService, "exists_or_create", Mock(return_value=True))
def test_delete_file_failure_dir(user_ref, file_service):
    path = '/some/path'
    result = file_service.delete_file(user_ref, path)
    assert result == False
    

@patch.object(FilesystemService, "exists_or_create", Mock(return_value=True))
def test_upload_file(user_ref, file_service):
    file1 = FileStorage(filename='/some/path/file1.txt')
    file2 = FileStorage(filename='file2.txt')
    file1.save = Mock()
    file2.save = Mock()
    
    files = {
        "file1": file1,
        "file2": file2
    }
    
    file_service.upload_file(user_ref, files)

    file1.save.assert_called_once()
    file2.save.assert_called_once()


@patch.object(FilesystemService, "exists_or_create", Mock(return_value=True))
def test_download_file(user_ref, file_service):
    filepath = '/some/path/file1.txt'
    result = file_service.download_file(user_ref, filepath)
    assert result == '/test/users/testuser/cloud/some/path/file1.txt'
