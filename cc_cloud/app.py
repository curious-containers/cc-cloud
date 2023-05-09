from argparse import ArgumentParser

from flask import Flask, jsonify, request

from cc_agency.commons.helper import create_flask_response
from cc_agency.version import VERSION as AGENCY_VERSION
from cc_agency.commons.conf import Conf
from cc_agency.commons.db import Mongo
from cc_agency.broker.auth import Auth

from cc_cloud.version import VERSION as CLOUD_VERSION
from cc_cloud.service.file_service import FileService
from cc_cloud.routes.routes import cloud_routes


DESCRIPTION = 'CC-Cloud webinterface'

app = Flask('cc-cloud')
app.config['UPLOAD_FOLDER'] = '/home/user/cloud'
application = app

parser = ArgumentParser(description=DESCRIPTION)
parser.add_argument(
    '-c', '--conf-file', action='store', type=str, metavar='CONF_FILE',
    help='CONF_FILE (yaml) as local path.'
)
args = parser.parse_args()

conf = Conf(args.conf_file)
mongo = Mongo(conf)
auth = Auth(conf, mongo)
file_manager = FileService(conf)

@app.route('/', methods=['GET'])
def get_root():
    return jsonify({'Hello': 'World'})


@app.route('/version', methods=['GET'])
def get_version():
    user = auth.verify_user(request.authorization, request.cookies, request.remote_addr)

    return create_flask_response(
        {
            'agencyVersion': AGENCY_VERSION,
            'cloudVersion': CLOUD_VERSION
        },
        auth,
        user.authentication_cookie
    )
    
cloud_routes(app, auth, file_manager)
