from sshpubkeys import SSHKey
from cc_cloud.service.filesystem_service import FilesystemService
from cc_cloud.service.file_service import FileService
from cc_cloud.system.local_user import LocalUser
from cc_agency.broker.auth import Auth


class CloudService:
    
    file_service: FileService
    filesystem_service: FilesystemService
    
    user_prefix = 'cloud'
    
    def __init__(self, conf, mongo):
        """Create a new instance of CloudService.
        All existing file systems of the user are automatically mounted.

        :param conf: Configuration to load values from
        :type conf: cc_agency.commons.conf.Conf
        """
        self.file_service = FileService(conf)
        self.filesystem_service = FilesystemService(conf)
        self.home_dir = conf.d.get('userhome_directory', '/var/lib/cc_cloud/home')
        self.mongo = mongo
        self.mount_filesystems()
    
    
    def mount_filesystems(self):
        """Mount all existing file systems of the users.
        """
        for fs in self.filesystem_service.find_all_filesystems():
            self.filesystem_service.exists_or_create(fs)
    
    
    def get_user_ref(self, user):
        """Combines the username with a set prefix.

        :param user: User for getting the reference.
        :type user: cc_agency.broker.auth.Auth.User
        :return: user reference
        :rtype: str
        """
        if isinstance(user, Auth.User):
            return self.user_prefix + '-' + user.username
        elif isinstance(user, str):
            return self.user_prefix + '-' + user            
    
    
    def local_user_exists_or_create(self, user):
        """Check if the local user exists. If not create a new linux user.

        :param user: create linux user based on the reference of this user
        :type user: cc_agency.broker.auth.Auth.User
        :return: user reference, instance of the created LocalUser
        :rtype: str, cc_cloud.system.local_user.LocalUser
        """
        user_ref = self.get_user_ref(user)
        local_user = LocalUser(user_ref, self.home_dir)
        if not local_user.exists():
            local_user.create()
            local_user.set_password()
            self.add_local_user_to_db(
                user.username,
                user_ref,
                local_user.secret,
                self.filesystem_service.user_storage_limit)
        return user_ref, local_user
    
    
    def add_local_user_to_db(self, username, ssh_user, ssh_password, size_limit):
        cloud_users = {
            'username': username,
            'ssh_user': ssh_user,
            'ssh_password': ssh_password,
            'size_limit': size_limit,
        }
        self.mongo.db['cloud_users'].update_one({'username': username}, {'$set': cloud_users}, upsert=True)
    
    
    def get_local_user_from_db(self, username):
        return self.mongo.db['cloud_users'].find_one({'username': username})
    
    
    ## cloud storage actions
    
    def file_action(self, user, func, *args):
        """Check if the local user and the filesystem exists. If not create
        the user and the filesystem. Then execute the given functions.

        :param user: the user for whom the file action is executed
        :type user: cc_agency.broker.auth.Auth.User
        :param func: the function to be executed
        :type func: callable
        :return: result of the method func
        """
        user_ref, _ = self.local_user_exists_or_create(user)
        self.filesystem_service.exists_or_create(user_ref)
        return func(user_ref, *args)
    
    
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
        return self.file_action(user, self.file_service.download_file, path)
    
    
    def upload_file(self, user, files):
        """Saves multiple files to the users storage.

        :param user: The user that wants to upload the files
        :type user: cc_agency.broker.auth.Auth.User
        :param files: One or multiple files that should be saved
        :type files: werkzeug.datastructures.structures.ImmutableMultiDict
        """
        self.file_action(user, self.file_service.upload_file, files)
    
    
    def delete_file(self, user, path):
        """Deletes a file or directory from the given path.

        :param user: The user that wants to delete an element
        :type user: cc_agency.broker.auth.Auth.User
        :param path: The path that will be deleted
        :type path: str
        :return: Returns True if the element was deleted
        :rtype: bool
        """
        return self.file_action(user, self.file_service.delete_file, path)
    
    
    ## local user actions
    
    def set_local_user_authorized_key(self, user, pub_key):
        """Check if the user exists. If not create the user.
        Then add the public ssh-key to the users authorized_keys file.

        :param user: user for whom the ssh-key will be added
        :type user: cc_agency.broker.auth.Auth.User
        :param pub_key: public ssh-key, that will be added to the authorized_keys file
        :type pub_key: str
        """
        try:
            ssh = SSHKey(pub_key)
            ssh.parse()
        except Exception:
            return False
        
        _, local_user = self.local_user_exists_or_create(user)
        local_user.set_authorized_key(pub_key)
        return True
    
    
    def get_storage_usage(self, user):
        """
        Get the current storage usage for a user.

        :param user: The user for whom to retrieve the storage usage.
        :type user: cc_agency.broker.auth.Auth.User
        :return: The storage usage in bytes.
        :rtype: int
        """
        user_ref = self.get_user_ref(user)
        try:
            return self.filesystem_service.get_storage_usage(user_ref)
        except TypeError:
            return 0
    
    
    def get_size_limit(self, user):
        """
        Get the size limit for a user.

        :param user: The user for whom to retrieve the size limit.
        :type user: cc_agency.broker.auth.Auth.User
        :return: The size limit in bytes.
        :rtype: int
        """
        user_ref = self.get_user_ref(user)
        return self.filesystem_service.get_size(user_ref)
    
    
    ## only for admin users
    
    def set_size_limit(self, user, change_user, size):
        """
        Set the size limit for a user.

        :param user: The user making the size limit change. Should be an admin user.
        :type user: cc_agency.broker.auth.Auth.User
        :param change_user: The user for whom the size limit will be changed.
        :type change_user: cc_agency.broker.auth.Auth.User
        :param size: The new size limit in bytes.
        :type size: int
        :return: True if the size limit was successfully changed, False otherwise.
        :rtype: bool
        """
        if not user.is_admin:
            return False
        
        db_user = self.get_local_user_from_db(change_user)
        if not db_user:
            return False
        
        change_user_ref = self.get_user_ref(change_user)
        current_size_limit = self.filesystem_service.get_size(change_user_ref)
        if size > current_size_limit:
            self.filesystem_service.increse_size(change_user_ref, size)
        elif size < current_size_limit:
            self.filesystem_service.reduce_size(change_user_ref, size)
        
        self.mongo.db['cloud_users'].update_one({'username': change_user}, {'$set': {'size_limit': size}}, upsert=True)
        
        return True
        
    
    def create_user(self, user, create_username):
        """
        Create a new user.

        :param user: The user creating the new user. Should be an admin user.
        :type user: cc_agency.broker.auth.Auth.User
        :param create_username: The username for the new user.
        :type create_username: str
        :return: True if the user was successfully created, False otherwise.
        :rtype: bool
        """
        if not user.is_admin:
            return False
        
        create_user = Auth.User(create_username, False)
        user_ref, _ = self.local_user_exists_or_create(create_user)
        self.filesystem_service.exists_or_create(user_ref)
        
        return True
    
    
    def remove_user(self, user, remove_username):
        """Delete the users (remove_username) filesystem and the local linux user.
        The action will only be performed if user is admin. 

        :param user: user who wants to perform the action
        :type user: cc_agency.broker.auth.Auth.User
        :param remove_user: the user which will be removed
        :type remove_user: cc_agency.broker.auth.Auth.User
        :return: if succeded returns true, otherwise false
        :rtype: bool
        """
        if not user.is_admin:
            return False
        
        user_ref = self.get_user_ref(remove_username)
        self.mongo.db['cloud_users'].delete_one({'username': remove_username})
        
        self.filesystem_service.umount(user_ref)
        self.filesystem_service.delete(user_ref)
        
        local_user = LocalUser(user_ref, self.home_dir)
        if local_user.exists():
            local_user.remove()
            
        return True
    
    
    
