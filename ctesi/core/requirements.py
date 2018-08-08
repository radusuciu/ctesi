"""Contains requirements for Flask-Allow."""
from flask import request
from ctesi.core.models import Experiment

def is_admin(user):
    return 'admin' in user.roles or (user.id == 1 and user.username == 'radus')

def is_own_experiment(user):
    experiment_id = request.view_args.get('experiment_id')
    experiment = Experiment.query.get(experiment_id)

    if not experiment:
        return False

    return experiment.user_id == user.id

def can_edit_experiment(user):
    return is_admin(user) or is_own_experiment(user)
