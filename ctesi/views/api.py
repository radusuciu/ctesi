from flask import Blueprint, abort, jsonify, request, session
from flask_login import login_required, current_user
from flask_principal import Permission, RoleNeed
from werkzeug import secure_filename
from ctesi.core.tasks import process
from ctesi.utils import validate_search_params
from ctesi import celery as celery_app
from http import HTTPStatus
from ip2api import IP2
import config.config as config
import ctesi.api as api
import pickle
import json
import hashlib


admin_permission = Permission(RoleNeed('admin'))

api_blueprint = Blueprint('api_blueprint', __name__,
                  template_folder='templates',
                  static_folder='static')


@api_blueprint.route('/')
@login_required
def get_experiments():
    experiments = api.get_user_experiments(current_user.get_id())
    experiments['hash'] = hashlib.sha1(json.dumps(experiments, sort_keys=True).encode('utf-8')).hexdigest()
    return jsonify(experiments)


@api_blueprint.route('/admin')
@admin_permission.require(http_exception=404)
def get_all_experiments():
    return jsonify(api.get_all_experiments())


@api_blueprint.route('/experiment', methods=['POST'])
@login_required
def new_experiment():
    data = request.json
    data['name'] = secure_filename(data['name'])

    search_params = validate_search_params({
        'diff_mods': data.get('diffMods'),
        'options': data.get('options')
    })

    (experiment_model, experiment_serialized) = api.add_experiment({
        'name': data['name'],
        'user_id': current_user.get_id(),
        'experiment_type': data['type'],
        'organism': data['organism'],
        'status': api.make_experiment_status_string('incomplete'),
        'search_params': json.dumps(search_params) or None
    })

    return jsonify({'experiment_id': experiment_model.data.experiment_id})


@api_blueprint.route('/upload_file/<int:experiment_id>', methods=['POST'])
@login_required
def add_file(experiment_id):
    experiment = api.get_raw_experiment(experiment_id)
    api.update_experiment_status(experiment_id, 'uploading')

    file = request.files.getlist('files')[0]
    filename = secure_filename(file.filename)
    filepath = experiment.tmp_path.joinpath(filename)
    # making sure we use lowercase extension
    filepath = filepath.with_suffix(filepath.suffix.lower())

    # only allow .raw extension
    if filepath.suffix == '.raw':
        experiment.tmp_path.mkdir(exist_ok=True, parents=True)
        file.save(str(filepath))

    return 'ok'


@api_blueprint.route('/process/<int:experiment_id>')
def process_experiment(experiment_id):
    result = process(
        experiment_id,
        session['ip2_username'],
        session['ip2_cookie'],
        temp_path='temp',
        user_id=current_user.get_id(),
        send_email=True
    )

    # if not data['remember_ip2']:
    #     session.pop('ip2_username', None)
    #     session.pop('ip2_cookie', None)

    return 'ok'


@api_blueprint.route('/status/<int:experiment_id>')
def status(experiment_id):
    experiment = api.get_raw_experiment(experiment_id)
    task = celery_app.AsyncResult(experiment.task_id)
    return task.state


@api_blueprint.route('/ip2_auth', methods=['POST'])
@login_required
def ip2_auth():
    username = request.json.get('username') or session.get('ip2_username')
    password = request.json.get('password')

    # using either source for usernames since I made a mistake in designing ip2api and required a username
    # on init but not on login.. would be a breaking change if I fixed it
    ip2 = IP2(config.IP2_URL, username)

    # not using username here because I want to make sure that session and form stuff stick together
    if request.json.get('username') and password:
        ip2.login(password)
    elif session.get('ip2_username') and session.get('ip2_cookie'):
        ip2.cookie_login(pickle.loads(session['ip2_cookie']))

    # note that the session is not cleared here, but in the search method
    if ip2.logged_in:
        session['ip2_username'] = ip2.username
        session['ip2_cookie'] = pickle.dumps(ip2._cookies)
        return jsonify(ip2.logged_in)
    else:
        abort(HTTPStatus.UNAUTHORIZED)


@api_blueprint.route('/rerun/<int:experiment_id>/<string:step>')
@login_required
def rerun_processing(experiment_id, step):
    steps = ['convert', 'search', 'cimage']

    if step not in steps:
        return 'invalid step'

    experiment = api.get_raw_experiment(experiment_id)

    if experiment.task_id:
        api.cancel_experiment(experiment_id)

    if ip2_auth() and (experiment.user_id == int(current_user.get_id()) or current_user.has_role('admin')):
        result = process(
            experiment_id,
            session['ip2_username'],
            session['ip2_cookie'],
            user_id=current_user.get_id(),
            from_step=step
        )

    return 'ok'


@api_blueprint.route('/delete/<int:experiment_id>')
@login_required
def delete_experiment(experiment_id):
    experiment = api.Experiment.query.get(experiment_id)

    if experiment.user_id == int(current_user.get_id()) or current_user.has_role('admin'):
        api.delete_experiment(experiment_id)
        return 'ok'
    else:
        return 'insufficient permissions'
