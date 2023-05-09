import os
import shutil

from cc_cloud.service.filesystem_service import FilesystemService

class FileService:
    
    def __init__(self, conf):
        self.filesystem_service = FilesystemService(conf)
        self.upload_dir = '/var/lib/cc_cloud/users'
    
    def download_file(self, user, path):
        if not self.is_secure_path(user, path):
            return None
        
        self.filesystem_exists_or_create(user)
        
        filepath = self.get_full_filepath(user, path)
        return filepath
    
    
    def upload_file(self, user, files):
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
        user_upload_dir = self.get_user_upload_directory(user)
        path = path.lstrip("/")
        path = os.path.join(user_upload_dir, path)
        path = os.path.abspath(path)
        commonpath = os.path.commonpath((user_upload_dir, path))
        return commonpath == user_upload_dir
    
    def get_user_upload_directory(self, user):
        return os.path.join(self.upload_dir, user.username)
    
    def get_full_filepath(self, user, filename):
        filepath = os.path.normpath(filename)
        filepath = filepath.lstrip("/")
        return os.path.join(self.get_user_upload_directory(user), filepath)
    
    def filesystem_exists_or_create(self, user):
        if not self.filesystem_service.user_filessystem_exists(user):
            self.filesystem_service.create(user)
        if not self.filesystem_service.is_mounted(user):
            self.filesystem_service.mount(user)