import secrets
import os
import pwd

class LocalUser:
    
    def __init__(self, username, base_dir = '/var/lib/cc_cloud/home', secret_length = 30):
        """Create a new instance of LocalUser.

        :param username: name of the local Linux user
        :type username: str
        :param base_dir: path to the home directory, defaults to '/var/lib/cc_cloud/home'
        :type base_dir: str, optional
        :param secret_length: length of the generated user password, defaults to 30
        :type secret_length: int, optional
        """
        self.username = username
        self.base_dir = base_dir
        self.secret_length = secret_length
    
    
    def create(self):
        """Creates a Linux user account with a randomly generated password and
        sets up the home directory. The user's shell is disabled (set to '/bin/false').
        """
        try:
            os.makedirs(self.base_dir)
        except FileExistsError:
            pass
        os.system(f"useradd {self.username} --base-dir {self.base_dir} --shell=/bin/false --create-home")
    
    
    def remove(self):
        """Removes a Linux user account.
        """
        os.system(f"killall -u {self.username}")
        os.system(f"userdel -r {self.username}")
        
    
    def set_password(self, password = None):
        """Sets the password for the user.

        :param password: The password to set. If not provided, a random password will be generated.
        :type password: str, optional
        """
        if password:
            self.secret = password
        else:
            self.secret = self.generate_random_secret()
        os.system(f"echo '{self.username}:{self.secret}' | chpasswd")
    
    
    def generate_random_secret(self):
        """Creates a random secet with the length of secret_length.

        :return: random secret string
        :rtype: str
        """
        return secrets.token_urlsafe(self.secret_length)
    
    
    def exists(self):
        """Checks if a Linux user exists.

        :return: True if the user exists, False otherwise
        :rtype: bool
        """
        try:
            pwd.getpwnam(self.username)
        except KeyError:
            return False
        return True
    
    
    def set_authorized_key(self, key):
        """Adds the key to the user's authorized_keys file. If a key already
        exists in the file, it will be overwritten.

        :param key: public ssh-key, that will be added to the authorized_keys file
        :type key: str
        """
        key_dir = os.path.join(self.base_dir, self.username)
        os.system(f"mkdir -p {key_dir}/.ssh && echo '{key}' > {key_dir}/.ssh/authorized_keys")
        os.system(f"chmod 700 {key_dir}/.ssh")
        os.system(f"chmod 600 {key_dir}/.ssh/authorized_keys")
        os.system(f"chown -R {self.username}:{self.username} {key_dir}/.ssh")
        
        