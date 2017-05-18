"""Blueprint for API methods."""
from flask import Blueprint, request, abort, render_template, jsonify, send_file
from flask_login import login_required, current_user
from werkzeug import secure_filename
from .search import Search
from .tasks import process
from http import HTTPStatus
from ctesi import db
import ctesi.upload as upload
import ctesi.api as api
import json


home = Blueprint('home', __name__,
                 template_folder='templates',
                 static_folder='static')


@home.route('/')
@login_required
def render():
    return render_template('index.html')


@home.route('/', methods=['POST'])
@login_required
def search():
    data = json.loads(request.form.get('data'))
    search = Search(data['name'])

    login = search.login(data['ip2username'], data['ip2password'])

    if not login:
        abort(HTTPStatus.UNAUTHORIZED)

    data['name'] = secure_filename(data['name'])

    experiment = api.add_experiment({
        'name': data['name'],
        'user_id': current_user.get_id(),
        'experiment_type': data['type'],
        'organism': data['organism'],
        'status': 'uploading'
    })

    experiment_id = experiment['experiment_id']

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
    process.delay(data, search, current_user.get_id(), experiment_id, path)

    return jsonify(experiment)


@home.route('/status')
@login_required
def status():
    user_id = current_user.get_id()
    return render_template('status.html', user=user_id)


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
    return jsonify(api.get_experiment())

@api_blueprint.route('/<int:experiment_id>')
@login_required
def get_experiment(experiment_id):
    return jsonify(api.get_experiment(experiment_id))

@api_blueprint.route('/status/<int:experiment_id>')
@login_required
def set_experiment_status(experiment_id):
    experiment = api.Experiment.query.get(experiment_id)
    experiment.status = request.args['status']
    db.session.commit()
    return jsonify(api.experiment_schema.dump(experiment))


@api_blueprint.route('/add')
@login_required
def add_experiment():
    print(request.args)
    return jsonify(API.add_experiment(request.args.to_dict()))

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

    if experiment.user_id == int(current_user.get_id()):
        api.delete_experiment(experiment_id)
        return 'ok'
    else:
        return 'insufficient permissions'


