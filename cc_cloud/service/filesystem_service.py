import os

class FilesystemService:
    
    FILESYSTEM = 'ext4'
    FILESYSTEM_SUBFOLDER = 'filesystems'
    
    def __init__(self, conf):
        """Create a new instance of FilesystemService

        :param conf: Configuration to load values from
        :type conf: cc_agency.commons.conf.Conf
        """
        self.cc_cloud_directory = conf.d.get('cc_cloud_directory', '/var/lib/cc_cloud')
        self.upload_dir = conf.d.get('upload_directory', '/var/lib/cc_cloud/users')
        self.user_storage_limit = conf.d.get('user_storage_limit', 52428800)
        self.filesystem_dir = os.path.join(self.cc_cloud_directory, self.FILESYSTEM_SUBFOLDER)
    
    def create(self, fs_name, size=None):
        """Creates a new File image and reserves storage space for it.
        The file will be formated as a filesystem.

        :param fs_name: Creates a filesystem with the name fs_name
        :type fs_name: str
        :param size: Size of the filesystem, defaults to None
        :type size: int, optional
        """
        filepath = self.get_filepath(fs_name)
        if size == None:
            size = self.user_storage_limit
        
        try:
            os.makedirs(os.path.dirname(filepath))
            os.makedirs(self.get_mountpoint(fs_name))
        except (OSError, FileExistsError):
            pass
        with open(filepath, 'a') as file:
            file.truncate(size)
        os.system(f"mke2fs -t {self.FILESYSTEM} -F '{filepath}'")
    
    def filessystem_exists(self, fs_name):
        """Check if the filesystem already exists.

        :param fs_name: name of the filesystem
        :type fs_name: str
        :return: Returns True if the filesystem exists
        :rtype: bool
        """
        filepath = self.get_filepath(fs_name)
        return os.path.exists(filepath)
    
    def find_all_filesystems(self):
        filesystems = []
        try:
            elements = os.listdir(self.filesystem_dir)
            for el in elements:
                el_path = os.path.join(self.filesystem_dir, el)
                if os.path.isfile(el_path):
                    filesystems.append(el)
        except FileNotFoundError:
            pass
        return filesystems
    
    def delete(self, fs_name):
        """Delete the file filesystem.

        :param fs_name: Delete the filesystem with the name fs_name
        :type fs_name: str
        """
        filepath = self.get_filepath(fs_name)
        os.remove(filepath)
    
    def mount(self, fs_name):
        """Mount the filesystem.

        :param fs_name: Mount the filesystem with the name fs_name
        :type fs_name: str
        """
        filepath = self.get_filepath(fs_name)
        mountpoint = self.get_mountpoint(fs_name)
        os.system(f"mount '{filepath}' '{mountpoint}'")
    
    def umount(self, fs_name):
        """Umount the filesystem.

        :param fs_name: Umount the filesystem with the name fs_name
        :type fs_name: str
        """
        filepath = self.get_filepath(fs_name)
        os.system(f"umount '{filepath}'")
    
    def is_mounted(self, fs_name):
        """Check if the filesystem is mounted.

        :param fs_name: Check if the filesystem with the name fs_name exists
        :type fs_name: str
        :return: Return True if the filesystem is mounted
        :rtype: bool
        """
        mountpoint = self.get_mountpoint(fs_name)
        exitcode = os.system(f"mountpoint -q '{mountpoint}'") # returns 0 if the directory is a mountpoint
        return not exitcode
    
    def increse_size(self, fs_name, size):
        """Increses the size of the filesystem.

        :param fs_name: Increse size of the filesystem with the name fs_name
        :type fs_name: str
        :param size: The size of the file system is set to the specified size
        :type size: int
        """
        filepath = self.get_filepath(fs_name)
        with open(filepath, 'a') as file:
            file.truncate(size)
        lo_device = self.get_loop_device(filepath)
        os.system(f"losetup -c '{lo_device}'")
        os.system(f"resize2fs '{lo_device}'")
    
    def reduce_size(self, fs_name, size):
        """Reduces the size of the filesystem.
        !!! All data inside this filesystem will be deleted !!!

        :param fs_name: Reduce size of the filesystem with the name fs_name
        :type fs_name: str
        :param size: The size of the file system is set to the specified size
        :type size: int
        """
        if self.is_mounted(fs_name):
            self.umount(fs_name)
        self.delete(fs_name)
        self.create(fs_name, size)
    
    def get_size(self, fs_name):
        """Get the size of the filesystem.

        :param fs_name: Get size of the filesystem with the name fs_name
        :type fs_name: str
        :return: Size of filesystem
        :rtype: int
        """
        filepath = self.get_filepath(fs_name)
        return os.path.getsize(filepath)
    
    def get_loop_device(self, filepath):
        """Get the loop device of the mounted filesystem.

        :param filepath: Path to the filesystem
        :type filepath: str
        :return: Name of the loop device
        :rtype: str
        """
        output = os.popen(f"losetup -j '{filepath}'").read()
        lo_device = output.split(':', 1)[0]
        return lo_device
    
    def get_filepath(self, fs_name):
        """Get the path to the file filesystem

        :param fs_name: Get path of the filesystem with the name fs_name
        :type fs_name: str
        :return: Path to the filesystem
        :rtype: str
        """
        return os.path.join(self.filesystem_dir, fs_name)
    
    def get_mountpoint(self, fs_name):
        """Get the mountpoint for the filesystem

        :param fs_name: Get the path of the filesystem with the name fs_name
        :type fs_name: str
        :return: Path to the mountpoint
        :rtype: str
        """
        return os.path.join(self.upload_dir, fs_name)
    
    def exists_or_create(self, fs_name):
        """Checks if the filesystem already exists is mounted.
        If not a new filesystem will be created and mounted.

        :param fs_name: Check if the filesystem with the name fs_name existed and is mounted
        :type fs_name: str
        """
        if not self.filessystem_exists(fs_name):
            self.create(fs_name)
        if not self.is_mounted(fs_name):
            self.mount(fs_name)

    
    def set_permissions():
        pass
    
    