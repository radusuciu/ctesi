from flask import Blueprint, request, render_template, jsonify, session
from flask_login import login_required, current_user
from flask_principal import Permission, RoleNeed
from werkzeug import secure_filename
from http import HTTPStatus
from ctesi import db
from ctesi.core.tasks import process
from ctesi.utils import validate_search_params
import ctesi.core.upload as upload
import ctesi.api as api
import json


admin_permission = Permission(RoleNeed('admin'))

home = Blueprint('home', __name__,
                 template_folder='templates',
                 static_folder='static')


@home.route('/')
@login_required
def render():
    bootstrap = None

    if session.get('ip2_username') and session.get('ip2_cookie'):
        bootstrap = {'ip2_authd': True}

    return render_template('index.html', bootstrap=bootstrap)


@home.route('/', methods=['POST'])
@login_required
def search():
    data = json.loads(request.form.get('data'))
    data['name'] = secure_filename(data['name'])

    search_params = validate_search_params({ 'diff_mods': data.get('diffMods') })

    (experiment_model, experiment_serialized) = api.add_experiment({
        'name': data['name'],
        'user_id': current_user.get_id(),
        'experiment_type': data['type'],
        'organism': data['organism'],
        'status': api.make_experiment_status_string('uploading'),
        'search_params': json.dumps(search_params) or None
    })

    experiment_id = experiment_model.data.experiment_id

    # save RAW files to disk
    (name, temp_path) = upload.upload(
        request.files.getlist('files'),
        current_user.get_id(),
        data['name'],
        experiment_id
    )

    # continue processing in background with celery
    result = process(
        experiment_id,
        session['ip2_username'],
        session['ip2_cookie'],
        temp_path=temp_path,
        user_id=current_user.get_id(),
        send_email=json.loads(data['email'])
    )

    if not data['remember_ip2']:
        session.pop('ip2_username', None)
        session.pop('ip2_cookie', None)

    return jsonify(experiment_serialized)


@home.route('/status')
@login_required
def status():
    user_id = current_user.get_id()
    return render_template('status.html', user=user_id)


@home.route('/admin')
@admin_permission.require(http_exception=404)
def admin():
    user_id = current_user.get_id()
    return render_template('admin.html', user=user_id)
