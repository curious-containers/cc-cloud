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
    
    def create(self, user, size=None):
        """Creates a new File image and reserved storage space for it.
        The file will be formated as a filesystem.

        :param user: Creates a filesystem for the user
        :type user: cc_agency.broker.auth.Auth.User
        :param size: Size of the filesystem, defaults to None
        :type size: int, optional
        """
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
        """Check if the filesystem for the user already exists.

        :param user: Check for this user
        :type user: cc_agency.broker.auth.Auth.User
        :return: Returns True if the filesystem exists
        :rtype: bool
        """
        filepath = self.get_filepath(user)
        return os.path.exists(filepath)
    
    def delete(self, user):
        """Delete the file filesystem.

        :param user: Delete the users filesystem
        :type user: cc_agency.broker.auth.Auth.User
        """
        filepath = self.get_filepath(user)
        os.remove(filepath)
    
    def mount(self, user):
        """Mount the filesystem.

        :param user: Mount the users filesystem
        :type user: cc_agency.broker.auth.Auth.User
        """
        filepath = self.get_filepath(user)
        mountpoint = self.get_mountpoint(user)
        os.system(f"mount '{filepath}' '{mountpoint}'")
    
    def umount(self, user):
        """Umount the filesystem.

        :param user: Umount the users filesystem
        :type user: cc_agency.broker.auth.Auth.User
        """
        filepath = self.get_filepath(user)
        os.system(f"umount '{filepath}'")
    
    def is_mounted(self, user):
        """Check if the filesystem is mounted.

        :param user: Check for this users filesystem
        :type user: cc_agency.broker.auth.Auth.User
        :return: Return True if the filesystem is mounted
        :rtype: bool
        """
        mountpoint = self.get_mountpoint(user)
        exitcode = os.system(f"mountpoint -q '{mountpoint}'") # returns 0 if the directory is a mountpoint
        return not exitcode
    
    def increse_size(self, user, size):
        """Increses the size of the filesystem.

        :param user: Increse size of this users filesystem
        :type user: cc_agency.broker.auth.Auth.User
        :param size: The size of the file system is set to the specified size
        :type size: int
        """
        filepath = self.get_filepath(user)
        with open(filepath, 'a') as file:
            file.truncate(size)
        lo_device = self.get_loop_device(filepath)
        os.system(f"losetup -c '{lo_device}'")
        os.system(f"resize2fs '{lo_device}'")
    
    def reduce_size(self, user, size):
        """Reduces the size of the filesystem.
        !!! All data inside this filesystem will be deleted !!!

        :param user: Reduce size of this users filesystem
        :type user: cc_agency.broker.auth.Auth.User
        :param size: The size of the file system is set to the specified size
        :type size: int
        """
        if self.is_mounted(user):
            self.umount(user)
        self.delete(user)
        self.create(user, size)
    
    def get_size(self, user):
        """Get the size of the filesystem.

        :param user: Get size of this users filesystem
        :type user: cc_agency.broker.auth.Auth.User
        :return: Size of filesystem
        :rtype: int
        """
        filepath = self.get_filepath(user)
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
    
    def get_filepath(self, user):
        """Get the path to the file filesystem of the user

        :param user: Get path of this users filesystem
        :type user: cc_agency.broker.auth.Auth.User
        :return: Path to the filesystem
        :rtype: str
        """
        return os.path.join(self.filesystem_dir, user.username)
    
    def get_mountpoint(self, user):
        """Get the mountpoint for the filesystem

        :param user: Use the filesystem of this user
        :type user: cc_agency.broker.auth.Auth.User
        :return: Path to the mountpoint
        :rtype: str
        """
        return os.path.join(self.upload_dir, user.username)
    
    def exists_or_create(self, user):
        """Checks if the user filesystem already exists is mounted.
        If not a new filesystem will be created and mounted.

        :param user: Check for this user if the filesystem existed and is mounted
        :type user: cc_agency.broker.auth.Auth.User
        """
        if not self.filesystem_service.user_filessystem_exists(user):
            self.filesystem_service.create(user)
        if not self.filesystem_service.is_mounted(user):
            self.filesystem_service.mount(user)
    