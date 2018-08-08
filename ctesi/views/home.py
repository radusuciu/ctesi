from flask import Blueprint, request, render_template, jsonify, send_file, session
from flask_login import login_required, current_user
from flask_principal import Permission, RoleNeed
from http import HTTPStatus
from ctesi import db
from ctesi.core.tasks import process
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


@home.route('/zip/<int:experiment_id>')
def get_experiment_zip(experiment_id):
    experiment = api.Experiment.query.get(experiment_id)

    # if experiment.user_id == int(current_user.get_id()):
    memory_file = api.get_zip(experiment_id)

    return send_file(
        memory_file,
        attachment_filename='{}.zip'.format(experiment.name),
        as_attachment=True,
        mimetype='application/zip, application/octet-stream'
    )

    return 'ok'