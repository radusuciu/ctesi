"""Provides Flask-Security login forms for usage with LDAP auth backend."""

import ldap3
from werkzeug.local import LocalProxy
from flask import request, current_app
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from flask_security.forms import Form, NextFormMixin, get_form_field_label
from flask_security.utils import config_value, get_message, verify_and_update_password, encrypt_password
from flask_security.confirmable import requires_confirmation
from ldap3.core.exceptions import LDAPExceptionError
from ctesi.core.exceptions import UserNotFoundInLDAP

_datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)


class LDAPLoginForm(Form, NextFormMixin):
    """Login form for LDAP users."""

    email = StringField('User ID')
    password = PasswordField(get_form_field_label('password'))
    remember = BooleanField(get_form_field_label('remember_me'))
    submit = SubmitField(get_form_field_label('login'))

    def __init__(self, *args, **kwargs):
        """Init new LDAP login form."""
        super(LDAPLoginForm, self).__init__(*args, **kwargs)
        self._args = args
        self._kwargs = kwargs
        if not self.next.data:
            self.next.data = request.args.get('next', '')
        self.remember.default = config_value('DEFAULT_REMEMBER_ME')

    def validate(self):
        """Validate LDAP logins against AD."""
        if not super(LDAPLoginForm, self).validate():
            return False

        if self.email.data.strip() == '':
            self.email.errors.append(get_message('USERID_NOT_PROVIDED')[0])
            return False

        if self.password.data.strip() == '':
            self.password.errors.append(
                get_message('PASSWORD_NOT_PROVIDED')[0]
            )
            return False

        try:
            # first we try authenticating against ldap
            user_dn, ldap_data = _datastore.query_ldap_user(self.email.data)

            if not _datastore.verify_password(user_dn, self.password.data):
                self.password.errors.append(get_message('INVALID_PASSWORD')[0])
                return False

            ldap_email = ldap_data[config_value('LDAP_EMAIL_FIELDNAME')].value
            password = encrypt_password(self.password.data)

            if _datastore.find_user(email=ldap_email):
                self.user = _datastore.get_user(ldap_email)
                # note that this is being stored per user login
                self.user.password = password
            else:
                self.user = _datastore.create_user(email=ldap_email, password=password)
                _datastore.commit()
        except LDAPExceptionError:
            self.email.errors.append(get_message('LDAP_SERVER_DOWN')[0])
            return self._try_local_auth()
        except UserNotFoundInLDAP:
            return self._try_local_auth()

        return True

    def _try_local_auth(self):
        self.user = _datastore.get_user(self.email.data)

        if not self.user:
            self.email.errors.append(get_message('USER_DOES_NOT_EXIST')[0])
            return False
        if not self.user.password:
            self.password.errors.append(get_message('PASSWORD_NOT_SET')[0])
            return False
        if not verify_and_update_password(self.password.data, self.user):
            self.password.errors.append(get_message('INVALID_PASSWORD')[0])
            return False
        if requires_confirmation(self.user):
            self.email.errors.append(get_message('CONFIRMATION_REQUIRED')[0])
            return False
        if not self.user.is_active:
            self.email.errors.append(get_message('DISABLED_ACCOUNT')[0])
            return False

        return True
