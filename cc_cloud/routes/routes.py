from flask import request, send_file
from cc_agency.commons.helper import create_flask_response


def cloud_routes(app, auth, cloud_service):
    """
    Creates the cloud webinterface endpoints.

    :param app: The flask app to attach to
    :param auth: The authorization module to use
    :type auth: Auth
    """
    
    @app.route('/file', methods=['GET'])
    def download_file():
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
        user = auth.verify_user(request.authorization, request.cookies, request.remote_addr)
        
        cloud_service.upload_file(user, request.files)
        
        return create_flask_response("ok", auth, user.authentication_cookie)
    
    
    @app.route('/file', methods=['DELETE'])
    def delete_file():
        user = auth.verify_user(request.authorization, request.cookies, request.remote_addr)
        path = request.args.get('path')
        
        deleted = cloud_service.delete_file(user, path)
        response_string = 'element deleted' if deleted else 'element not found'
        
        return create_flask_response(response_string, auth, user.authentication_cookie)
    
    
    @app.route('/public_key', methods=['PUT'])
    def add_public_key():
        user = auth.verify_user(request.authorization, request.cookies, request.remote_addr)
        public_key = request.args.get('key')
        
        added = cloud_service.set_local_user_authorized_key(user, public_key)
        response_string = 'ok' if added else 'public key not valid'
                
        return create_flask_response(response_string, auth, user.authentication_cookie)
    
    
    @app.route('/create_user', methods=['GET'])
    def create_user():
        user = auth.verify_user(request.authorization, request.cookies, request.remote_addr)
        create_username = request.args.get('username')
        
        created = cloud_service.create_user(user, create_username)
        response_string = 'user created' if created else 'could not create user'
        
        return create_flask_response(response_string, auth, user.authentication_cookie)
    
    
    @app.route('/remove_user', methods=['GET'])
    def remove_user():
        user = auth.verify_user(request.authorization, request.cookies, request.remote_addr)
        remove_username = request.args.get('username')
        
        removed = cloud_service.remove_user(user, remove_username)
        response_string = 'user removed' if removed else 'could not remove user'
        
        return create_flask_response(response_string, auth, user.authentication_cookie)
        