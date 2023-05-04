import os

from flask import request, send_from_directory
from werkzeug.utils import secure_filename
from cc_agency.commons.helper import create_flask_response


def cloud_routes(app, mongo, auth):
    """
    Creates the cloud webinterface endpoints.

    :param app: The flask app to attach to
    :param mongo: The mongo client
    :type mongo: Mongo
    :param auth: The authorization module to use
    :type auth: Auth
    """
    
    @app.route('/file', methods=['GET'])
    def download_file():
        user = auth.verify_user(request.authorization, request.cookies, request.remote_addr)
        path = request.args.get('path')
        
        print(is_secure_path(app.config['UPLOAD_FOLDER'], path))
        
        #TODO: send_from_directory limit dir to user space in upload_folder
        
        return send_from_directory(app.config['UPLOAD_FOLDER'], path, as_attachment=True)
        #return create_flask_response("ok", auth, user.authentication_cookie)
    
    @app.route('/file', methods=['PUT'])
    def upload_file():
        user = auth.verify_user(request.authorization, request.cookies, request.remote_addr)
        
        print(f"files: {request.files}")
        if request.files:
            for filename, file in request.files.items():
                if file.filename == '':
                    print('No selected file')
                if filename == '':
                    filename = file.filename
                
                if file:
                    filename = secure_filename(filename)
                    print(filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            print("no file in request")
        
        return create_flask_response("ok", auth, user.authentication_cookie)
    
    @app.route('/file', methods=['DELETE'])
    def delete_file():
        user = auth.verify_user(request.authorization, request.cookies, request.remote_addr)
        path = request.args.get('path')
        
        filename = secure_filename(path)
        filename = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        try:
            print(filename)
            os.remove(filename)
        except OSError:
            pass
        
        return create_flask_response("ok", auth, user.authentication_cookie)
    
    
    def is_secure_path(basedir, path):
        path = path.lstrip("/")
        path = os.path.join(basedir, path)
        path = os.path.abspath(path)
        commonpath = os.path.commonpath((basedir, path))
        return commonpath == basedir
        