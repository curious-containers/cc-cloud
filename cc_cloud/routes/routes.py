from flask import request, send_file
from cc_agency.commons.helper import create_flask_response


def cloud_routes(app, auth, cloud_service):
    """
    Creates the cloud webinterface endpoints.

    :param app: The flask app to attach to
    :type app: flask.Flask
    :param auth: The authorization module to use
    :type auth: Auth
    :param cloud_service: The cloud service module to use.
    :type cloud_service: CloudService
    """
    
    @app.route('/file', methods=['GET'])
    def download_file():
        """
        Endpoint for downloading a file.

        :param path: The path of the file to download.
        :type path: str
        :return: The file as an attachment if it exists, or an appropriate error message.
        :rtype: flask.Response
        """
        user = auth.verify_user(request.authorization, request.cookies, request.remote_addr)
        path = request.args.get('path')
        
        file = cloud_service.download_file(user, path)
        
        if not file:
            return create_flask_response("invalid path", auth, user.authentication_cookie)
        
        try:
            return send_file(file, as_attachment=True)
        except FileNotFoundError:
            return create_flask_response("file not found", auth, user.authentication_cookie)
        except IsADirectoryError:
            return create_flask_response("cannot download directorys", auth, user.authentication_cookie)
        
    
    @app.route('/file', methods=['PUT'])
    def upload_file():
        """
        Endpoint for uploading a file.

        :param files: The uploaded file(s) to be saved.
        :type files: werkzeug.datastructures.FileStorage or dict[str, werkzeug.datastructures.FileStorage]
        :return: The response indicating the success of the file upload.
        :rtype: flask.Response
        """
        user = auth.verify_user(request.authorization, request.cookies, request.remote_addr)
        
        cloud_service.upload_file(user, request.files)
        
        return create_flask_response("ok", auth, user.authentication_cookie)
    
    
    @app.route('/file', methods=['DELETE'])
    def delete_file():
        """
        Endpoint for deleting a file.

        :param path: The path of the file to delete.
        :type path: str
        :return: The response indicating the success of the file deletion.
        :rtype: flask.Response
        """
        user = auth.verify_user(request.authorization, request.cookies, request.remote_addr)
        path = request.args.get('path')
        
        deleted = cloud_service.delete_file(user, path)
        response_string = 'element deleted' if deleted else 'element not found'
        
        return create_flask_response(response_string, auth, user.authentication_cookie)
    
    
    @app.route('/public_key', methods=['PUT'])
    def add_public_key():
        """
        Endpoint for adding a public key.

        :param key: The public key to add.
        :type key: str
        :return: The response indicating the success of adding the public key.
        :rtype: flask.Response
        """
        user = auth.verify_user(request.authorization, request.cookies, request.remote_addr)
        public_key = request.args.get('key')
        
        added = cloud_service.set_local_user_authorized_key(user, public_key)
        response_string = 'ok' if added else 'public key not valid'
        
        return create_flask_response(response_string, auth, user.authentication_cookie)
    
    
    @app.route('/size', methods=['GET'])
    def get_current_size():
        """
        Endpoint for retrieving the current storage usage.

        :return: The current storage size in bytes.
        :rtype: flask.Response
        """
        user = auth.verify_user(request.authorization, request.cookies, request.remote_addr)
        
        current_size = cloud_service.get_storage_usage(user)
        
        return create_flask_response(current_size, auth, user.authentication_cookie)
    
    
    @app.route('/size_limit', methods=['GET'])
    def get_size_limit():
        """
        Endpoint for retrieving the size limit.

        :return: The size limit in bytes.
        :rtype: flask.Response
        """
        user = auth.verify_user(request.authorization, request.cookies, request.remote_addr)
        
        size_limit = cloud_service.get_size_limit(user)
                
        return create_flask_response(size_limit, auth, user.authentication_cookie)
    
    
    @app.route('/size_limit', methods=['PUT'])
    def set_size_limit():
        """
        Endpoint for setting the size limit.

        :param username: The username for which to set the size limit.
        :type username: str
        :param size: The new size limit in bytes.
        :type size: str
        :return: The response indicating the success of changing the size limit.
        :rtype: flask.Response
        """
        user = auth.verify_user(request.authorization, request.cookies, request.remote_addr)
        change_user = request.args.get('username')
        size = request.args.get('size')
        
        edited = cloud_service.set_size_limit(user, change_user, int(size))
        response_string = 'ok' if edited else 'could not change the size'
                
        return create_flask_response(response_string, auth, user.authentication_cookie)
    
    
    @app.route('/create_user', methods=['GET'])
    def create_user():
        """
        Endpoint for creating a user.

        :param username: The username to create.
        :type username: str
        :return: The response indicating the success of creating the user.
        :rtype: flask.Response
        """
        user = auth.verify_user(request.authorization, request.cookies, request.remote_addr)
        create_username = request.args.get('username')
        
        created = cloud_service.create_user(user, create_username)
        response_string = 'user created' if created else 'could not create user'
        
        return create_flask_response(response_string, auth, user.authentication_cookie)
    
    
    @app.route('/remove_user', methods=['GET'])
    def remove_user():
        """
        Endpoint for removing a user.

        :param username: The username to remove.
        :type username: str
        :return: The response indicating the success of removing the user.
        :rtype: flask.Response
        """
        user = auth.verify_user(request.authorization, request.cookies, request.remote_addr)
        remove_username = request.args.get('username')
        
        removed = cloud_service.remove_user(user, remove_username)
        response_string = 'user removed' if removed else 'could not remove user'
        
        return create_flask_response(response_string, auth, user.authentication_cookie)
        