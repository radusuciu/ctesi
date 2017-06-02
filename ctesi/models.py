"""Le models."""

from flask_security import UserMixin, RoleMixin
from marshmallow import Schema, fields, post_dump, pre_load, post_load
from sqlalchemy import func
from sqlalchemy.ext.hybrid import hybrid_property
from ctesi import db
import config.config as config
import pathlib
import json

Column = db.Column
relationship = db.relationship

roles_users = db.Table(
    'roles_users',
    Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    Column('role_id', db.Integer(), db.ForeignKey('role.id'))
)


class Role(db.Model, RoleMixin):
    """Simple role or database user."""

    id = Column(db.Integer(), primary_key=True)
    name = Column(db.String(80), unique=True)
    description = Column(db.String(255))


class User(db.Model, UserMixin):
    """User of proteomics database."""

    id = Column(db.Integer, primary_key=True)
    email = Column(db.String(255), unique=True)
    password = Column(db.String(255))
    active = Column(db.Boolean())
    confirmed_at = Column(db.DateTime())
    roles = relationship(
        'Role',
        secondary=roles_users,
        backref=db.backref('users', lazy='dynamic')
    )

    @hybrid_property
    def username(self):
        return self.email.split('@')[0]

    @username.expression
    def username(cls):
        return func.split_part(cls.email, '@', 1)


class UserSchema(Schema):
    """Marshmallow schema for User."""

    id = fields.Integer(dump_only=True)
    email = fields.String(dump_only=True)
    name = fields.Function(lambda obj: obj.email.split('@')[0])

    @post_dump(pass_many=True)
    def _wrap(self, data, many):
        return {'users': data} if many else data


class Experiment(db.Model):
    """Holds experimental metadata."""

    __tablename__ = 'experiment'

    experiment_id = Column(db.Integer, primary_key=True)
    name = Column(db.Text)
    description = Column(db.Text)
    date = Column(db.DateTime(), server_default=func.now())
    modified = Column(db.DateTime(), onupdate=func.now())
    user_id = Column(db.Integer, db.ForeignKey('user.id'), index=True)
    organism = Column(db.Text)
    experiment_type = Column(db.Text)
    search_params = Column(db.Text)
    quant_params = Column(db.Text)
    annotations = Column(db.Text)
    status = Column(db.Text)
    task_id = Column(db.Text)

    @hybrid_property
    def path(self):
        return config.INSTANCE_PATH.joinpath(
            'users',
            str(self.user_id),
            str(self.experiment_id)
        )

    # bidirectional many-to-one relationships corresponding to foreign keys above
    user = relationship('User', lazy='joined')


class ExperimentSchema(Schema):
    """Marshmallow schema for Experiment."""

    experiment_id = fields.Integer(dump_only=True)
    name = fields.String(required=True)
    date = fields.DateTime()
    modified = fields.DateTime()
    user_id = fields.Integer(required=True)
    experiment_type = fields.String()
    organism = fields.String()
    search_params = fields.String()
    quant_params = fields.String()
    annotations = fields.String()
    status = fields.String()
    user = fields.Nested('UserSchema', dump_only=True)

    @pre_load
    def _filter_experiment(self, data):
        return {k: v for k, v in data.items() if v is not None}

    @post_load
    def _make_experiment(self, data):
        return Experiment(**data)

    @post_dump(pass_many=False)
    def _json_status(self, data):
        if data['status']:
            data['status'] = json.loads(data['status'])
        if data['search_params']:
            data['search_params'] = json.loads(data['search_params'])

    @post_dump(pass_many=True)
    def _wrap(self, data, many):
        return {'experiments': data} if many else data
