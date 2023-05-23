
from cc_cloud.service.filesystem_service import FilesystemService
from cc_cloud.service.file_service import FileService
from cc_cloud.system.local_user import LocalUser


class CloudService:
    
    file_service: FileService
    filesystem_service: FilesystemService
    
    user_prefix = 'cloud'
    
    def __init__(self, conf):
        self.file_service = FileService(conf)
        self.filesystem_service = FilesystemService(conf)
        self.home_dir = '/var/lib/cc_cloud/home'
        self.startup()
    
    
    def startup(self):
        for fs in self.filesystem_service.find_all_filesystems():
            self.filesystem_service.exists_or_create(fs)
    
    
    def get_user_ref(self, user):
        return self.user_prefix + '-' + user.username
    
    
    ## for every user
    
    def file_action(self, user, func, *args):
        user_ref = self.get_user_ref(user)
        local_user = LocalUser(user_ref, self.home_dir)
        if not local_user.exists():
            local_user.create()
        self.filesystem_service.exists_or_create(user_ref)
        return func(user_ref, *args)
    
    
    def download_file(self, user, path):
        return self.file_action(user, self.file_service.download_file, path)
    
    
    def upload_file(self, user, files):
        return self.file_action(user, self.file_service.upload_file, files)
    
    
    def delete_file(self, user, path):
        return self.file_action(user, self.file_service.delete_file, path)
    
    
    ## only for admin users
    
    def create_user():
        pass
    
    
    def remove_user():
        pass
    
    
    
