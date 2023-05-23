
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
        self.mount_filesystems()
    
    
    def mount_filesystems(self):
        for fs in self.filesystem_service.find_all_filesystems():
            self.filesystem_service.exists_or_create(fs)
    
    
    def get_user_ref(self, user):
        return self.user_prefix + '-' + user.username
    
    
    def local_user_exists_or_create(self, user):
        user_ref = self.get_user_ref(user)
        local_user = LocalUser(user_ref, self.home_dir)
        if not local_user.exists():
            local_user.create()
        return user_ref, local_user
    
    
    ## cloud storage actions
    
    def file_action(self, user, func, *args):
        user_ref, _ = self.local_user_exists_or_create(user)
        self.filesystem_service.exists_or_create(user_ref)
        return func(user_ref, *args)
    
    
    def download_file(self, user, path):
        return self.file_action(user, self.file_service.download_file, path)
    
    
    def upload_file(self, user, files):
        return self.file_action(user, self.file_service.upload_file, files)
    
    
    def delete_file(self, user, path):
        return self.file_action(user, self.file_service.delete_file, path)
    
    
    ## local user actions
    
    def set_local_user_authorized_key(self, user, pub_key):
        _, local_user = self.local_user_exists_or_create(user)
        local_user.set_authorized_key(pub_key)
    
    
    ## only for admin users
    
    def create_user():
        pass
    
    
    def remove_user(self, user, remove_user):
        if not user.is_admin:
            return False
        
        user_ref = self.get_user_ref(remove_user)
        
        self.filesystem_service.umount(user_ref)
        self.filesystem_service.delete(user_ref)
        
        local_user = LocalUser(user_ref, self.home_dir)
        if local_user.exists():
            local_user.remove()
            
        return True
    
    
    
