
from cc_cloud.service.filesystem_service import FilesystemService
from cc_cloud.service.file_service import FileService
from cc_cloud.system.local_user import LocalUser


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
        return self.user_prefix + '-' + user.username
    
    
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
        _, local_user = self.local_user_exists_or_create(user)
        local_user.set_authorized_key(pub_key)
    
    
    ## only for admin users
    
    def create_user(self, user, create_user):
        if not user.is_admin:
            return False
        
        user_ref, _ = self.local_user_exists_or_create(create_user)
        self.filesystem_service.exists_or_create(user_ref)
        
        return True
    
    
    def remove_user(self, user, remove_user):
        """Delete the users (remove_user) filesystem and the local linux user.
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
        
        user_ref = self.get_user_ref(remove_user)
        
        self.mongo.db['cloud_users'].delete_one({'username': remove_user.username})
        
        self.filesystem_service.umount(user_ref)
        self.filesystem_service.delete(user_ref)
        
        local_user = LocalUser(user_ref, self.home_dir)
        if local_user.exists():
            local_user.remove()
            
        return True
    
    
    
