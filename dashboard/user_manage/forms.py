# Copyright 2012 Beixinyuan(Nanjing), All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


__author__ = 'liu xu'
__date__ = '2013-02-05'
__version__ = 'v2.0.1'

from django.conf import settings
if settings.DEBUG:
    __log__ = 'v2.0.1 create'

import logging
LOG = logging.getLogger(__name__)

#    code begin
import re

from django import forms
from django.forms import *
from django.utils.translation import ugettext_lazy as _

from dashboard import api
from dashboard.authorize_manage import ROLE_ADMIN, ROLE_PROJECTADMIN
from dashboard.authorize_manage.utils import get_user_role_name
from dashboard.exceptions import Unauthorized
from dashboard.utils import validators


class CreateUserForm(forms.Form):
    """
    the form for creating a user
    """
    name = CharField(label=_("User Name"), max_length=10, min_length=2)
    email = EmailField(label=_("email"))
    password = RegexField(
        label=_("Password"),
        widget=PasswordInput(render_value=False),
        regex=validators.password_validator(),
        error_messages={'invalid': validators.password_validator_msg()})
    confirm_password = CharField(
        label=_("Confirm Password"),
        required=False,
        widget=PasswordInput(render_value=False))
    tenant_id = ChoiceField(label=_("Primary Project"), required=True)
    role_id = ChoiceField(label=_("Role"))

    def __init__(self, request, *args, **kwargs):
        super(CreateUserForm, self).__init__(*args, **kwargs)
        self.request = request

        roles = []
        role_choices = []
        try:
            roles = api.keystone.role_list(request)
        except Unauthorized:
            raise
        except Exception, e:
            LOG.error("Unable to retrieve user roles. %s" % e)

        for role in roles:
            if role.name != ROLE_ADMIN and role.enabled:
                role_choices.append((role.id, role.name))
#            if role.name == ROLE_PROJECTADMIN:
#                if get_user_role_name(request) == ROLE_ADMIN:
#                    role_choices.append((role.id, role.name))
#            elif role.name != ROLE_ADMIN:
#                role_choices.insert(0, (role.id, role.name))

        self.fields['role_id'].choices = role_choices

        tenant_choices = [('', _("Select a project"))]
        for tenant in api.tenant_list(request, admin=True):
            if tenant.enabled:
                tenant_choices.append((tenant.id, tenant.name))
        self.fields['tenant_id'].choices = tenant_choices

    def clean(self):
        """Check to make sure password fields match."""
        data = super(forms.Form, self).clean()

        if ('password' not in data) or ('name' not in data) or ('email' not in data):
            return data

        if re.search(r'\s', data['password']):
            raise ValidationError(_("no blank space allowed during password"))
        if data['password'] != data.get('confirm_password', None):
            raise ValidationError(_('Passwords do not match.'))

        if re.search(r'\s', data['name']):
            raise ValidationError(_('no blank space allowed during user name'))
        if not validators.has_hz(data['email']):
            raise ValidationError(_('Email Name has chinese.'))

        try:
            users = api.keystone.user_list(self.request)
        except Unauthorized:
            raise
        except Exception, e:
            LOG.error('Unable to retrieve user list in handle_create. %s' % e)
            return data

        for user in users:
            if data['name'] == getattr(user, 'name', 'unknown'):
                raise ValidationError(_('username has exist.'))
            if data['email'] == getattr(user, 'email', 'unknown'):
                raise ValidationError(_('email has exist.'))

        return data


class UpdateUserForm(forms.Form):
    """the form for updating a user"""
    name = CharField(label=_("User Name"), max_length=10, min_length=2)
    email = EmailField(label=_("Email"))
    enabled = BooleanField(required=False, label=_("Enabled"))

    def __init__(self, request, u_id, *args, **kwargs):
        super(UpdateUserForm, self).__init__(*args, **kwargs)
        self.request = request

        try:
            obj = api.user_get(request, u_id, admin=True)
            self.fields['name'].initial = getattr(obj, 'name', 'unknown')
            self.fields['email'].initial = getattr(obj, 'email', 'unknown')
            self.fields['enabled'].initial = obj.enabled
        except Unauthorized:
            raise
        except Exception, e:
            LOG.error("Unable to retrieve user %s. %s" % (u_id, e))

    def clean(self):
        """Check to make sure password fields match."""
        data = super(forms.Form, self).clean()
        if ('name' not in data) or ('email' not in data):
            return data

        own_name = self.fields['name'].initial
        own_email = self.fields['email'].initial

        if re.search(r'\s', data['name']):
            raise ValidationError(_('no blank space allowed during user name'))
        if not validators.has_hz(data['email']):
            raise ValidationError(_('Email Name has chinese.'))

        try:
            users = api.keystone.user_list(self.request)
        except Unauthorized:
            raise
        except Exception, e:
            LOG.error('Unable to retrieve user list. %s' % e)
            return data

        for user in users:
            if data['name'] == getattr(user, 'name', 'unknown') \
                    and data['name'] != own_name:
                raise ValidationError(_('username has exist.'))
            if data['email'] == getattr(user, 'email', 'unknown') \
                    and data['email'] != own_email:
                raise ValidationError(_('email has exist.'))

        return data


class UpdateUserPasswordForm(forms.Form):
    """
    the form for updating a user

    """
    name = CharField(label=_("User Name"), max_length=10, min_length=2)
    password = RegexField(label=_("Password"),
        widget=PasswordInput(render_value=False),
        regex=validators.password_validator(),
        required=False,
        error_messages={'invalid':
                            validators.password_validator_msg()})
    confirm_password = CharField(
        label=_("Confirm Password"),
        widget=PasswordInput(render_value=False),
        required=False)

    def __init__(self, request, u_id, *args, **kwargs):
        super(UpdateUserPasswordForm, self).__init__(*args, **kwargs)
        # name initial
        try:
            user = api.user_get(request, u_id, admin=True)
            self.fields['name'].initial = getattr(user, 'name', 'unknown')
        except Unauthorized:
            raise
        except Exception, e:
            msg = "Unable to retrieve user %s. %s" % (u_id, e)
            LOG.error(msg)

    def clean(self):
        """Check to make sure password fields match."""
        data = super(forms.Form, self).clean()
        if ('password' in data) and ('confirm_password' in data):
            if re.search(r'\s', data['password']):
                msg = 'no blank space allowed during password'
                raise ValidationError(_(msg))
            if data['password'] != data.get('confirm_password', None):
                raise ValidationError(_('Passwords do not match.'))
        return data


class ChangePasswordForm(forms.Form):

    oldpassword = RegexField(label=_("OldPassword"),
        widget=PasswordInput(render_value=False),
        regex=validators.password_validator(),
        required=True,
        error_messages={'invalid':
                            validators.password_validator_msg()})

    password = RegexField(label=_("Password"),
        widget=PasswordInput(render_value=False),
        regex=validators.password_validator(),
        required=True,
        error_messages={'invalid':
                            validators.password_validator_msg()})
    confirm_password = CharField(
        label=_("Confirm Password"),
        widget=PasswordInput(render_value=False),
        required=True)

    def __init__(self, request, user_id, *args, **kwargs):
        super(ChangePasswordForm, self).__init__(*args, **kwargs)
        self.request = request
        self.user_id = user_id

    def clean(self):
        """Check to make sure password fields match."""
        data = super(forms.Form, self).clean()
        if ('password' in data) and ('confirm_password' in data) and ('oldpassword' in data):
            if re.search(r'\s', data['password']):
                msg = 'no blank space allowed during password'
                raise ValidationError(_(msg))
            if data['password'] != data.get('confirm_password', None):
                raise ValidationError(_('Passwords do not match.'))
        return data
