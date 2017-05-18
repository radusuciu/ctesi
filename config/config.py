"""Main configuration file for project."""

import yaml
import os
import pathlib


PROJECT_NAME = 'ctesi'
PROJECT_HOME_PATH = pathlib.Path(os.path.realpath(__file__)).parents[1]


# debug is true by default
DEBUG = bool(os.getenv('DEBUG', True))
_secrets_path = PROJECT_HOME_PATH.joinpath('config', 'secrets.yml')
_override_path = PROJECT_HOME_PATH.joinpath('config', 'secrets.override.yml')

# get our secrets
with _secrets_path.open() as f:
    _SECRETS = yaml.load(f)

# provide a mechanism for overriding some secrets
if _override_path.is_file():
    with _override_path.open() as f:
        _SECRETS.update(yaml.load(f)['services'])



INSTANCE_PATH = PROJECT_HOME_PATH.joinpath(PROJECT_NAME, 'uploads')
SEARCH_PARAMS_PATH = PROJECT_HOME_PATH.joinpath(PROJECT_NAME, 'params', 'search')

CONVERT_URL = 'http://cravattwork.scripps.edu:5001'
IP2_URL = 'http://goldfish.scripps.edu'


class _Config(object):
    """Holds flask configuration to be consumed by Flask's from_object method."""

    # SQLAlchemy
    SQLALCHEMY_DATABASE_URI = 'sqlite:////{}/ctesi.db'.format(str(PROJECT_HOME_PATH))
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask
    DEBUG = False
    SECRET_KEY = _SECRETS['flask']['SECRET_KEY']
    JSONIFY_PRETTYPRINT_REGULAR = False

    # LDAP configuration
    SECURITY_LDAP_URI = _SECRETS['ldap']['URI']
    SECURITY_LDAP_BASE_DN = _SECRETS['ldap']['BASE_DN']
    SECURITY_LDAP_SEARCH_FILTER = _SECRETS['ldap']['SEARCH_FILTER']
    SECURITY_LDAP_BIND_DN = _SECRETS['ldap']['BIND_DN']
    SECURITY_LDAP_BIND_PASSWORD = _SECRETS['ldap']['BIND_PASSWORD']
    SECURITY_LDAP_EMAIL_FIELDNAME = 'mail'

    SECURITY_MSG_USERID_NOT_PROVIDED = ('User ID not provided', 'error')
    SECURITY_MSG_LDAP_SERVER_DOWN = ("""The Scripps authentication server is down or not accessible, please try the
                                            last password you successfully used to login to this server.""", 'error')
    SECURITY_USER_IDENTITY_ATTRIBUTES = ['email', 'username']



class _DevelopmentConfig(_Config):
    """Configuration for development environment."""

    DEBUG = True


config = _DevelopmentConfig if DEBUG else _Config
