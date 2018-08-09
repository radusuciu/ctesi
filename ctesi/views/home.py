from flask import Blueprint, render_template, send_file, session, current_app
from flask_login import current_user
from flask_allows import requires
from ctesi.core.requirements import is_admin, can_edit_experiment
import ctesi.api as api


home = Blueprint('home', __name__,
                 template_folder='templates',
                 static_folder='static')

@home.before_request
def is_logged_in():
    if not current_user.is_authenticated:
        return current_app.login_manager.unauthorized()


@home.route('/')
def render():
    bootstrap = None

    if session.get('ip2_username') and session.get('ip2_cookie'):
        bootstrap = {'ip2_authd': True}

    return render_template('index.html', bootstrap=bootstrap)


@home.route('/status')
def status():
    user_id = current_user.get_id()
    return render_template('status.html', user=user_id)


@home.route('/admin')
@requires(is_admin)
def admin():
    user_id = current_user.get_id()
    return render_template('admin.html', user=user_id)


@home.route('/zip/<int:experiment_id>')
@requires(can_edit_experiment)
def get_experiment_zip(experiment_id):
    experiment = api.Experiment.query.get(experiment_id)
    memory_file = api.get_zip(experiment_id)

    return send_file(
        memory_file,
        attachment_filename='{}.zip'.format(experiment.name),
        as_attachment=True,
        mimetype='application/zip, application/octet-stream'
    )

    return 'ok'