import os
import shutil

class FileService:
    
    def __init__(self, conf):
        """Create a new instance of FileService

        :param conf: The cc-cloud configuration file
        :type conf: cc_agency.commons.conf.Conf
        """
        self.upload_directory_name = conf.d.get('upload_directory_name', 'cloud')
        self.userhome_directory = conf.d.get('userhome_directory', '/var/lib/cc_cloud/home')
    
    def download_file(self, user_ref, path):
        """Checks if the user is allowed to access the file. If the path is available and
        the user is allowed the access, the absolute filepath will be returned.

        :param user_ref: The user that wants to access the file
        :type user_ref: str
        :param path: Path to the requested file
        :type path: str
        :return: Absolute filepath
        :rtype: str
        """
        if not self.is_secure_path(user_ref, path):
            return None
        
        filepath = self.get_full_filepath(user_ref, path)
        return filepath
    
    
    def upload_file(self, user_ref, files):
        """Saves multiple files to the users storage.

        :param user_ref: The user that wants to upload the files
        :type user_ref: str
        :param files: One or multiple files that should be saved
        :type files: werkzeug.datastructures.structures.ImmutableMultiDict
        """
        if files:
            for filename, file in files.items():
                
                if file.filename == '':
                    continue
                if filename == '':
                    filename = file.filename
                
                if not self.is_secure_path(user_ref, filename):
                    continue
                
                if file:
                    filepath = self.get_full_filepath(user_ref, filename)
                    try:
                        os.makedirs(os.path.dirname(filepath))
                        os.system(f"chown -R {user_ref}:{user_ref} {self.get_user_upload_directory(user_ref)}")
                    except OSError:
                        pass
                    file.save(filepath)
                    shutil.chown(filepath, user_ref, user_ref)
    
    
    def delete_file(self, user_ref, path):
        """Deletes a file or directory from the given path.

        :param user_ref: The user that wants to delete an element.
        :type user_ref: str
        :param path: The path that will be deleted
        :type path: str
        :return: Returns True if the element was deleted
        :rtype: bool
        """
        if not self.is_secure_path(user_ref, path):
            return False
        
        filepath = self.get_full_filepath(user_ref, path)
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
    
    
    def is_secure_path(self, user_ref, path):
        """Checks if the given path is within the users storage space.

        :param user_ref: The users reference that requests to use the path
        :type user_ref: str
        :param path: The path that will be checked
        :type path: str
        :return: Returns True if the user is allowed to use the path
        :rtype: bool
        """
        user_upload_dir = self.get_user_upload_directory(user_ref)
        path = path.lstrip("/")
        path = os.path.join(user_upload_dir, path)
        path = os.path.abspath(path)
        commonpath = os.path.commonpath((user_upload_dir, path))
        return commonpath == user_upload_dir
    
    def get_user_upload_directory(self, user_ref):
        """Get the path to the directory that belongs to the user.

        :param user_ref: The users reference for whom the directory is returned
        :type user_ref: str
        :return: Path to the users directory
        :rtype: str
        """
        return os.path.join(self.userhome_directory, user_ref, self.upload_directory_name)
    
    def get_full_filepath(self, user_ref, filename):
        """Returns the filepath based on the user directory

        :param user_ref: Filepath will be based on the users directory
        :type user_ref: str
        :param filename: Path to the file
        :type filename: str
        :return: Absolute filepath based on the user directory
        :rtype: str
        """
        filepath = os.path.normpath(filename)
        filepath = filepath.lstrip("/")
        return os.path.join(self.get_user_upload_directory(user_ref), filepath)