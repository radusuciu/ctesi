"""Defines methods for interacting with database."""
from ctesi import db
from ctesi.models import Experiment, ExperimentSchema, User, UserSchema
from flask import send_file
from .convert import cancel_convert
import sqlalchemy as sa
import pathlib
import zipfile
import shutil
import json
import io


experiment_schema = ExperimentSchema()
user_schema = UserSchema()


def _get_all(model, schema):
    query = model.query.all()
    return schema.dump(query, many=True).data


def _get_all_or_one(model, schema, _id=None):
    """Helper method which returns all results if _id is undefined.
    Arguments:
        model -- SQLAlchemy Model to query against
        schema -- Marhsmallow schema to use when dumping data
        _id  -- Optional primary key to query against.
    """
    if _id:
        query = model.query.get(_id)
    else:
        query = model.query.all()

    return schema.dump(query, many=_id is None).data


def get_experiment(experiment_id=None, flat=False):
    return _get_all_or_one(Experiment, experiment_schema, experiment_id)


def get_raw_experiment(experiment_id):
    return Experiment.query.get(experiment_id)


def get_user_experiments(user_id):
    query = Experiment.query.filter_by(user_id=user_id)
    return experiment_schema.dump(query, many=True).data


def add_experiment(data):
    experiment = experiment_schema.load(data)
    db.session.add(experiment.data)
    db.session.commit()
    return (experiment, experiment_schema.dump(experiment.data).data)


def update_experiment_status(experiment_id, status):
    experiment = Experiment.query.get(experiment_id)

    if isinstance(status, str):
        status = { 'step': status }

    experiment.status = json.dumps(status)
    db.session.commit()


def get_zip(experiment_id):
    experiment = Experiment.query.get(experiment_id)

    path = pathlib.Path(experiment.path).expanduser()

    memory_file = io.BytesIO()

    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in path.rglob('*'):
            zf.write(str(f), str(f.relative_to(path)))

    memory_file.seek(0)

    return memory_file


def delete_experiment(experiment_id, cancel_task_handle, force=False):
    experiment = Experiment.query.get(experiment_id)
    experiment_serialized = get_experiment(experiment_id)

    try:
        status = experiment_serialized['status']['step']
    except:
        status = ''

    if force or status in ('done', 'error', 'cancelled'):
        try:
            shutil.rmtree(str(experiment.path))
        except FileNotFoundError:
            db.session.delete(experiment)
            db.session.commit()
        except:
            api.update_experiment_status(experiment_id, 'error')
    else:
        cancel_experiment(experiment_id, cancel_task_handle)
        # setting force = True to prevent infite recursion where status is undefined
        delete_experiment(experiment_id, cancel_task_handle, force=True)


def cancel_experiment(experiment_id, cancel_task_handle):
    experiment = Experiment.query.get(experiment_id)
    experiment_serialized = get_experiment(experiment_id)

    if experiment.task_id:
        res = cancel_task_handle(experiment.task_id)
        experiment.task_id = ''
        db.session.commit()

    try:
        step = experiment_serialized['status']['step']

        if step == 'converting':
            path = str(experiment.user_id) + '/' + str(experiment_id)
            res = cancel_convert(path)
    except:
        pass

    update_experiment_status(experiment_id, 'cancelled')


def get_user(user_id):
    return User.query.get(user_id)
