"""Defines methods for interacting with database."""
from flask import send_file
from ctesi import db, celery
from ctesi.core.models import Experiment, ExperimentSchema, User, UserSchema
from ctesi.core.convert import cancel_convert
import sqlalchemy as sa
import pathlib
import zipfile
import shutil
import json
import io


experiment_schema = ExperimentSchema(exclude=('user',))
full_experiment_schema = ExperimentSchema(many=True)
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


def get_all_experiments():
    query = Experiment.query.all()
    return full_experiment_schema.dump(query).data


def add_experiment(data):
    experiment = experiment_schema.load(data)
    db.session.add(experiment.data)
    db.session.commit()
    return (experiment, experiment_schema.dump(experiment.data).data)


def make_experiment_status_string(status):
    if isinstance(status, str):
        status = { 'step': status }
    return json.dumps(status)


def update_experiment_status(experiment_id, status):
    experiment = Experiment.query.get(experiment_id)
    experiment.status = make_experiment_status_string(status)
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


def delete_experiment(experiment_id, force=False):
    try:
        experiment = Experiment.query.get(experiment_id)
        experiment_serialized = get_experiment(experiment_id)

        status = experiment_serialized['status']['step']

        if force or status in ('done', 'error', 'cancelled'):
            if experiment.path.exists():
                shutil.rmtree(str(experiment.path))

            db.session.delete(experiment)
            db.session.commit()
        else:
            cancel_experiment(experiment_id)
            # setting force = True to prevent infite recursion where status is undefined
            delete_experiment(experiment_id, force=True)
    except:
        update_experiment_status(experiment_id, 'error')


def cancel_experiment(experiment_id):
    experiment = Experiment.query.get(experiment_id)
    experiment_serialized = get_experiment(experiment_id)

    if experiment.task_id:
        res = celery.control.revoke(experiment.task_id, terminate=True)
        experiment.task_id = ''
        db.session.commit()

    try:
        step = experiment_serialized['status']['step']

        if step == 'converting':
            path = str(experiment.user_id) + '/' + str(experiment_id)
            res = cancel_convert(path)

        if experiment.tmp_path.exists():
            shutil.rmtree(str(experiment.tmp_path))
    except:
        pass

    update_experiment_status(experiment_id, 'cancelled')


def get_user(user_id):
    return User.query.get(user_id)
