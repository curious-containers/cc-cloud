import os
import shutil

class FileManager:
    
    def __init__(self, conf):
        self.upload_folder = '/home/dominik/cloud'
    
    def download_file(self, user, path):        
        if not self.is_secure_path(user, path):
            return None
        
        filepath = self.get_full_filepath(user, path)
        return filepath
    
    
    def upload_file(self, user, files):
        # TODO:
        # check users upload limit (storage size)
        
        if files:
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
        user_upload_folder = self.get_user_upload_folder(user)
        path = path.lstrip("/")
        path = os.path.join(user_upload_folder, path)
        path = os.path.abspath(path)
        commonpath = os.path.commonpath((user_upload_folder, path))
        return commonpath == user_upload_folder
    
    def get_user_upload_folder(self, user):
        return os.path.join(self.upload_folder, user.username)
    
    def get_full_filepath(self, user, filename):
        filepath = os.path.normpath(filename)
        filepath = filepath.lstrip("/")
        return os.path.join(self.get_user_upload_folder(user), filepath)