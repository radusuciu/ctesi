"""Defines methods for interacting with database."""
from ctesi import db
from ctesi.models import Experiment, ExperimentSchema, User, UserSchema
from flask import send_file
import sqlalchemy as sa
import pathlib
import zipfile
import shutil
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
    data = _get_all_or_one(Experiment, experiment_schema, experiment_id)

    if 'experiments' in data:
        experiments = data['experiments']
    else:
        experiments = [data]

    return data


def add_experiment(data):
    experiment = experiment_schema.load(data)
    db.session.add(experiment.data)
    db.session.commit()
    return experiment_schema.dump(experiment.data).data


def update_experiment_status(experiment_id, status):
    experiment = Experiment.query.get(experiment_id)
    experiment.status = status
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


def delete_experiment(experiment_id):
    experiment = Experiment.query.get(experiment_id)

    if experiment.status in ('done', 'cancelled'):
        shutil.rmtree(experiment.path)
        db.session.delete(experiment)
        db.session.commit()
    else:
        cancel_experiment(experiment_id)
        delete_experiment(experiment_id)


def cancel_experiment(experiment_id):
    update_experiment_status(experiment_id, 'cancelled')
