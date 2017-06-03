"""Blueprint for API methods."""
from flask import Blueprint, request, abort, render_template, jsonify, send_file, session
from flask_login import login_required, current_user
from flask_principal import Permission, RoleNeed
from werkzeug import secure_filename
from .search import Search
from .tasks import process, cancel_task
from http import HTTPStatus
from ctesi import db
from ip2api import IP2
from .utils import validate_search_params
import config.config as config
import ctesi.upload as upload
import ctesi.api as api
import json
import pickle

admin_permission = Permission(RoleNeed('admin'))


home = Blueprint('home', __name__,
                 template_folder='templates',
                 static_folder='static')


@home.route('/')
@login_required
def render():
    if session.get('ip2_username') and session.get('ip2_cookie'):
        bootstrap = {'ip2_authd': True}

    return render_template('index.html', bootstrap=bootstrap)


@home.route('/', methods=['POST'])
@login_required
def search():
    data = json.loads(request.form.get('data'))
    search = Search(data['name'])

    login = search.login(data['ip2username'], data['ip2password'])

    if not login:
        abort(HTTPStatus.UNAUTHORIZED)

    data['name'] = secure_filename(data['name'])

    try:
        diff_mods = data['diffMods']
        search_params = validate_search_params({ 'diff_mods': diff_mods })
    except:
        search_params = None

    (experiment_model, experiment_serialized) = api.add_experiment({
        'name': data['name'],
        'user_id': current_user.get_id(),
        'experiment_type': data['type'],
        'organism': data['organism'],
        'search_params': json.dumps(search_params)
    })

    experiment = experiment_model.data
    experiment_id = experiment.experiment_id

    api.update_experiment_status(experiment_id, {'step': 'uploading', 'status': None, 'progress': None})

    # save RAW files to disk
    # path is type pathlib.Path
    try:
        name, path = upload.upload(
            request.files.getlist('files'),
            current_user.get_id(),
            data['name'],
            experiment_id
        )
    except FileExistsError:
        abort(HTTPStatus.CONFLICT)

    # continue processing in background with celery
    result = process.delay(data, search, current_user.get_id(), experiment_id, path, search_params)
    if not data['remember_ip2']:
        session.pop('ip2_username', None)
        session.pop('ip2_cookie', None)

    experiment.task_id = result.id
    db.session.commit()

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


users = Blueprint('users', __name__,
                  template_folder='templates',
                  static_folder='static')


@users.before_app_first_request
def create_user():
    db.create_all()
    db.session.commit()


api_blueprint = Blueprint('api_blueprint', __name__,
                  template_folder='templates',
                  static_folder='static')


@api_blueprint.route('/')
@login_required
def get_experiments():
    return jsonify(api.get_user_experiments(current_user.get_id()))


@api_blueprint.route('/admin')
@admin_permission.require(http_exception=404)
def get_all_experiments():
    return jsonify(api.get_all_experiments())


@api_blueprint.route('/ip2_auth', methods=['POST'])
@login_required
def ip2_auth():
    username = request.form.get('username') or session.get('ip2_username')
    password = request.form.get('password')

    # using either source for usernames since I made a mistake in designing ip2api and required a username
    # on init but not on login.. would be a breaking change if I fixed it
    ip2 = IP2(config.IP2_URL, username)

    # not using username here because I want to make sure that session and form stuff stick together
    if request.form.get('username') and password:
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
    

@api_blueprint.route('/zip/<int:experiment_id>')
@login_required
def get_experiment_zip(experiment_id):
    experiment = api.Experiment.query.get(experiment_id)

    if experiment.user_id == int(current_user.get_id()):
        memory_file = api.get_zip(experiment_id)

        return send_file(
            memory_file,
                attachment_filename='{}.zip'.format(experiment.name),
                as_attachment=True,
                mimetype='application/zip, application/octet-stream'
            )

    return 'ok'


@api_blueprint.route('/delete/<int:experiment_id>')
@login_required
def delete_experiment(experiment_id):
    experiment = api.Experiment.query.get(experiment_id)

    if experiment.user_id == int(current_user.get_id()) or current_user.has_role('admin'):
        api.delete_experiment(experiment_id, cancel_task)
        return 'ok'
    else:
        return 'insufficient permissions'
