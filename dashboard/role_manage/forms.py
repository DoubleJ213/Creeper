__author__ = 'liuh'

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
from dashboard.exceptions import Unauthorized
from .models import *
from dashboard.utils import validators


class CreateRoleForm(forms.Form):
    """
    the form for creating a role
    """
    name = CharField(label=_("Role Name"), max_length=10, min_length=2)
    description = CharField(widget=widgets.Textarea(), required=False,
                            label=_("Description"))
    parent_role_id = ChoiceField(label="Extends Role", required=False)
    rights = CharField(
        label=_("Permission"),required=False,
        help_text=_("Launch role."))

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super(CreateRoleForm, self).__init__(*args, **kwargs)
        parent_choices = [('', _("Select a role"))]
        try:
            roles = api.keystone.role_list(self.request)
            roles = [role for role in roles if 'Member' == role.name or 'ProjectAdmin' == role.name or 'Auditor' == role.name]
            for role in roles:
                parent_choices.append((role.id, role.name))
            self.fields['parent_role_id'].choices  = parent_choices
        except Exception, exc:
            LOG.error("Error is %s" % exc)






    def clean(self):
        data = super(forms.Form, self).clean()
        if re.search(r'\s', data['name']):
            raise ValidationError(_("role name can not contain blank space!"))
        try:
            roles = api.keystone.role_list(self.request)
        except Unauthorized:
            raise
        except Exception, e:
            LOG.error('Unable to retrieve role list in create_role. %s' % e)
            return data

        for role in roles:
            if data['name'] == getattr(role, 'name', 'unknown'):
                raise ValidationError(_('role name has exist.'))

        return data



class UpdateRoleForm(forms.Form):
    role_id = CharField(label=_("Role Id"),
                        widget=TextInput(attrs={'readonly': 'readonly'}))
    name = CharField(label=_("Role Name"), max_length=10, min_length=2)
    description = CharField(widget=widgets.Textarea(), required=False,
                            label=_("Description"))
    rights = CharField(
        label=_("Permission"),required=False,
        help_text=_("Launch role."))

    def __init__(self, request, role_id, *args, **kwargs):
        super(UpdateRoleForm, self).__init__(*args, **kwargs)
        self.request = request
        try:
            role = api.keystone.role_get(request, role_id)

            name = getattr(role, 'name', None)
            description = getattr(role, 'description', None)
            rights = ''
            role_right = Role_right.objects.filter(role_id=role_id)
            for ro in role_right:
                rights += ro.right_key + ','

            self.fields['role_id'].initial = role_id
            self.fields['name'].initial = name
            self.fields['description'].initial = description
            self.fields['rights'].initial = rights
        except Unauthorized:
            raise
        except Exception, e:
            LOG.error('Error is :%s' % e)
            raise

    def clean(self):
        data = super(forms.Form, self).clean()
        if re.search(r'\s', data['name']):
            raise ValidationError(_("role name can not contain blank space!"))
        try:
            roles = api.keystone.role_list(self.request)
        except Unauthorized:
            raise
        except Exception, e:
            LOG.error('Unable to retrieve role list in create_role. %s' % e)
            return data

        for role in roles:
            if data['name'] == getattr(role, 'name', 'unknown') and data[
                                                                    'role_id'] != getattr(
                role, 'id', 'unknown'):
                raise ValidationError(_('role name has exist.'))

        return data

