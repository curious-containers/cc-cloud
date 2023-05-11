import os

class FilesystemService:
    
    FILESYSTEM = 'ext4'
    FILESYSTEM_SUBFOLDER = 'filesystems'
    
    def __init__(self, conf):
        self.cc_cloud_directory = conf.get('cc_cloud_directory', '/var/lib/cc_cloud')
        self.upload_dir = conf.get('upload_directory', '/var/lib/cc_cloud/users')
        self.user_storage_limit = conf.get('user_storage_limit', 52428800)
        self.filesystem_dir = os.path.join(self.cc_cloud_directory, self.FILESYSTEM_SUBFOLDER)
    
    def create(self, user, size=None):
        filepath = self.get_filepath(user)
        if size == None:
            size = self.user_storage_limit
        with open(filepath, 'a') as file:
            file.truncate(size)
        os.system(f"mke2fs -t {self.FILESYSTEM} -F '{filepath}'")
        try:
            os.makedirs(self.get_mountpoint(user))
        except FileExistsError:
            pass
    
    def user_filessystem_exists(self, user):
        filepath = self.get_filepath(user)
        return os.path.exists(filepath)
    
    def delete(self, user):
        filepath = self.get_filepath(user)
        os.remove(filepath)
    
    def mount(self, user):
        filepath = self.get_filepath(user)
        mountpoint = self.get_mountpoint(user)
        os.system(f"mount '{filepath}' '{mountpoint}'")
    
    def umount(self, user):
        filepath = self.get_filepath(user)
        os.system(f"umount '{filepath}'")
    
    def is_mounted(self, user):
        mountpoint = self.get_mountpoint(user)
        exitcode = os.system(f"mountpoint -q '{mountpoint}'") # returns 0 if the directory is a mountpoint
        return not exitcode
    
    def increse_size(self, user, size):
        filepath = self.get_filepath(user)
        with open(filepath, 'a') as file:
            file.truncate(size)
        lo_device = self.get_loop_device(filepath)
        
        print(f"\n\n\n{lo_device}\n\n\n")
        
        os.system(f"losetup -c '{lo_device}'")
        os.system(f"resize2fs '{lo_device}'")
    
    def reduce_size(self, user, size):
        if self.is_mounted(user):
            self.umount(user)
        self.delete(user)
        self.create(user, size)
    
    def get_size(self, user):
        filepath = self.get_filepath(user)
        return os.path.getsize(filepath)
    
    def get_loop_device(self, filepath):
        output = os.popen(f"losetup -j '{filepath}'").read()
        lo_device = output.split(':', 1)[0]
        return lo_device
    
    def get_filepath(self, user):
        return os.path.join(self.filesystem_dir, user.username)
    
    def get_mountpoint(self, user):
        return os.path.join(self.upload_dir, user.username)
    