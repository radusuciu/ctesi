"""Backend for a proteomics database."""
from flask import Flask, jsonify, make_response, render_template
from ctesi.ldap import LDAPUserDatastore, LDAPLoginForm
from http import HTTPStatus
from redis import StrictRedis
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security
from flask_migrate import Migrate
from flask_login import current_user
from flask_allows import Allows
from celery import Celery
import config.config as config

app = Flask(__name__)
app.config.from_object(config.config)
allows = Allows(app=app, identity_loader=lambda: current_user)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

celery = Celery()
celery.config_from_object(config.CeleryConfig)

redis = StrictRedis(host='redis')

# Register blueprints
from ctesi.views import home, users, api_blueprint
app.register_blueprint(home)
app.register_blueprint(users)
app.register_blueprint(api_blueprint, url_prefix='/api')


# Setup Flask-Security with LDAP goodness
from ctesi.core.models import User, Role
user_datastore = LDAPUserDatastore(db, User, Role)
security = Security(app, user_datastore, login_form=LDAPLoginForm)

@app.errorhandler(HTTPStatus.UNAUTHORIZED)
@app.errorhandler(HTTPStatus.NOT_FOUND)
def error(error):
    return render_template('error.html', error=error), error.code
