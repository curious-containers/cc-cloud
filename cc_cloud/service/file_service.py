import os
import shutil

from cc_cloud.service.filesystem_service import FilesystemService

class FileService:
    
    def __init__(self, conf):
        """Create a new instance of FileService

        :param conf: The cc-cloud configuration file
        :type conf: cc_agency.commons.conf.Conf
        """
        self.filesystem_service = FilesystemService(conf)
        self.upload_dir = conf.d.get('upload_directory', '/var/lib/cc_cloud/users')
    
    def download_file(self, user, path):
        """Checks if the user is allowed to access the file. If the path is available and
        the user is allowed the access, the absolute filepath will be returned.

        :param user: The user that wants to access the file
        :type user: cc_agency.broker.auth.Auth.User
        :param path: Path to the requested file
        :type path: str
        :return: Absolute filepath
        :rtype: str
        """
        if not self.is_secure_path(user, path):
            return None
        
        self.filesystem_exists_or_create(user)
        
        filepath = self.get_full_filepath(user, path)
        return filepath
    
    
    def upload_file(self, user, files):
        """Saves multiple files to the users storage.

        :param user: The user that wants to upload the files
        :type user: cc_agency.broker.auth.Auth.User
        :param files: One or multiple files that should be saved
        :type files: werkzeug.datastructures.structures.ImmutableMultiDict
        """
        if files:
            self.filesystem_exists_or_create(user)
            
            for filename, file in files.items():
                
                if file.filename == '':
                    continue
                if filename == '':
                    filename = file.filename
                
                if not self.is_secure_path(user, filename):
                    continue
                
                if file:
                    filepath = self.get_full_filepath(user, filename)
                    try:
                        os.makedirs(os.path.dirname(filepath))
                    except OSError:
                        pass
                    file.save(filepath)
    
    
    def delete_file(self, user, path):
        """Deletes a file or directory from the given path.

        :param user: The user that wants to delete an element.
        :type user: cc_agency.broker.auth.Auth.User
        :param path: The path that will be deleted
        :type path: str
        :return: Returns True if the element was deleted
        :rtype: bool
        """
        if not self.is_secure_path(user, path):
            return False
        
        self.filesystem_exists_or_create(user)
        
        filepath = self.get_full_filepath(user, path)
        if os.path.isfile(filepath):
            try:
                os.remove(filepath)
            except OSError:
                return False
        else:
            try:
                shutil.rmtree(filepath)
            except (OSError, FileNotFoundError):
                return False
        
        return True
    
    
    def is_secure_path(self, user, path):
        """Checks if the given path is within the users storage space.

        :param user: The user that requests to use the path
        :type user: cc_agency.broker.auth.Auth.User
        :param path: The path that will be checked
        :type path: str
        :return: Returns True if the user is allowed to use the path
        :rtype: bool
        """
        user_upload_dir = self.get_user_upload_directory(user)
        path = path.lstrip("/")
        path = os.path.join(user_upload_dir, path)
        path = os.path.abspath(path)
        commonpath = os.path.commonpath((user_upload_dir, path))
        return commonpath == user_upload_dir
    
    def get_user_upload_directory(self, user):
        """Get the path to the directory that belongs to the user.

        :param user: The user for whom the directory is returned
        :type user: cc_agency.broker.auth.Auth.User
        :return: Path to the users directory
        :rtype: str
        """
        return os.path.join(self.upload_dir, user.username)
    
    def get_full_filepath(self, user, filename):
        """Returns the filepath based on the user directory

        :param user: Filepath will be based on this user directory
        :type user: cc_agency.broker.auth.Auth.User
        :param filename: Path to the file
        :type filename: str
        :return: Absolute filepath based on the user directory
        :rtype: str
        """
        filepath = os.path.normpath(filename)
        filepath = filepath.lstrip("/")
        return os.path.join(self.get_user_upload_directory(user), filepath)
    
    def filesystem_exists_or_create(self, user):
        """Checks if the user filesystem already exists is mounted.
        If not a new filesystem will be created and mounted.

        :param user: Check for this user if the filesystem existed and is mounted.
        :type user: cc_agency.broker.auth.Auth.User
        """
        if not self.filesystem_service.user_filessystem_exists(user):
            self.filesystem_service.create(user)
        if not self.filesystem_service.is_mounted(user):
            self.filesystem_service.mount(user)