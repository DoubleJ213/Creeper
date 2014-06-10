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


import logging
import re

from django.conf import settings
from django.forms import *
from django.utils.translation import ugettext_lazy as _

from dashboard import api
from dashboard.authorize_manage import ROLE_ADMIN, ROLE_PROJECTADMIN
from dashboard.authorize_manage.utils import get_user_role_name
from dashboard.exceptions import Unauthorized

if settings.DEBUG:
    __log__ = 'v2.0.1 create'

LOG = logging.getLogger(__name__)


#    code begin
MAX_INT = 2147483647

class CreateTenantForm(forms.Form):
    """
    the form for creating a tenant
    """
    name = CharField(label=_("Project Name"), max_length=10, min_length=2)
    description = CharField(label=_("Project Description"),
                            required=False, widget=Textarea)
    enabled = BooleanField(label=_("Enabled"),
                            required=False, initial=True)

    def clean(self):
        data = super(forms.Form, self).clean()
        if 'name' not in data:
            return data
        if re.search(r'\s', data['name']):
            raise ValidationError(_("project name can not contain blank space"))
        return data


class UpdateTenantForm(forms.Form):
    """
    the form for updating a tenant
    """
    id = CharField(label=_("ID"),
        widget=TextInput(attrs={'readonly': 'readonly'}))
    name = CharField(label=_("Name"), max_length=10, min_length=2)
    description = CharField(
        widget=widgets.Textarea(),
        required=False,
        label=_("Description"))
    enabled = BooleanField(required=False, label=_("Enabled"))

    def __init__(self, request, tenant_id, *args, **kwargs):
        super(UpdateTenantForm,self).__init__(*args, **kwargs)
        try:
            obj = api.keystone.tenant_get(request, tenant_id, admin=True)
            self.fields['id'].initial = obj.id
            self.fields['name'].initial = obj.name
            self.fields['description'].initial = obj.description
            self.fields['enabled'].initial = obj.enabled
        except Unauthorized:
            raise
        except Exception, e:
            LOG.error('Unable to get tenant %s. %s' % (tenant_id, e))

    def clean(self):
        data = super(forms.Form, self).clean()
        if 'name' not in data:
            return data
        if re.search(r'\s', data['name']):
            raise ValidationError(_("project name can not contain blank space"))
        return data


class UpdateQuotasForm(forms.Form):
    """
    the form for updating the quotas of a tenant
    """
    tenant_id = CharField(label=_("ID (name)"),
        widget=TextInput(attrs={'readonly': 'readonly'}))
    tenant_name = CharField(label=_("name"),
        widget=TextInput(attrs={'readonly': 'readonly'}))
    cores = IntegerField(label=_("VCPUs"))
    instances = IntegerField(label=_("Instances"))
    volumes = IntegerField(label=_("Volumes"))
    gigabytes = IntegerField(label=_("Gigabytes"))
    ram = IntegerField(label=_("RAM (in MB)"))
    floating_ips = IntegerField(label=_("Floating IPs"))
    security_groups = IntegerField(label=_("Security Groups"))
    security_group_rules = IntegerField(label=_("Security Group Rules"))

    def __init__(self, request, tenant_id, *args, **kwargs):
        super(UpdateQuotasForm,self).__init__(*args, **kwargs)
        try:
            tenant = api.keystone.tenant_get(request, tenant_id, admin=True)
            quotas = api.nova.nova_tenant_quota_get(request, tenant_id)
            quotas2 = api.cinder.cinder_tenant_quota_get(request, tenant_id)
            quotasItems = {}
            for item in quotas:
                quotasItems[item.name] = item.limit
            for item in quotas2:
                quotasItems[item.name] = item.limit
            #quotas initial
            self.fields['tenant_id'].initial = tenant_id
            self.fields['tenant_name'].initial = getattr(tenant, 'name', 'unknown')
            self.fields['volumes'].initial = self.getQuotasItem(quotasItems, 'volumes', '0')
            self.fields['gigabytes'].initial = self.getQuotasItem(quotasItems, 'gigabytes', '0')
            self.fields['ram'].initial = self.getQuotasItem(quotasItems, 'ram', '0')
            self.fields['floating_ips'].initial = self.getQuotasItem(quotasItems, 'floating_ips', '0')
            self.fields['instances'].initial = self.getQuotasItem(quotasItems, 'instances', '0')
            self.fields['cores'].initial = self.getQuotasItem(quotasItems, 'cores', '0')
            self.fields['security_groups'].initial = self.getQuotasItem(quotasItems, 'security_groups', '0')
            self.fields['security_group_rules'].initial = self.getQuotasItem(quotasItems,
                'security_group_rules', '0')
        except Unauthorized:
            raise
        except Exception, e:
            LOG.error('Unable to get tenant %s. %s' % (tenant_id, e))

    def clean(self):
        """Check to make sure input fields match."""
        data = super(forms.Form, self).clean()
        if ('volumes' not in data) or ('gigabytes' not in data) \
                or ('ram' not in data) or ('floating_ips' not in data) \
                or ('instances' not in data) or ('cores' not in data) \
                or  ('security_groups' not in data) or ('security_group_rules' not in data):
            return data

        if data['volumes'] < 0:
            msg = _("volumes should be larger than or equal to 0.")
            raise ValidationError(msg)
        if data['gigabytes'] <= 0:
            msg = _("gigabytes should be larger than 0.")
            raise ValidationError(msg)
        if data['ram'] <= 0:
            msg = _("ram should be larger than 0.")
            raise ValidationError(msg)
        if data['floating_ips'] <= 0:
            msg = _("floating_ips should be larger than 0.")
            raise ValidationError(msg)
        if data['instances'] < 0:
            msg = _("instances should be larger than or equal to 0.")
            raise ValidationError(msg)
        if data['cores'] <= 0:
            msg = _("cores should be larger than 0.")
            raise ValidationError(msg)
        if data['security_groups'] <= 0:
            msg = _("security_groups should be larger than 0.")
            raise ValidationError(msg)
        if data['security_group_rules'] <= 0:
            msg = _("security_groups_rules should be larger than 0.")
            raise ValidationError(msg)
        if  data['volumes'] > MAX_INT or data['gigabytes'] > MAX_INT \
                or data['ram'] > MAX_INT or data['floating_ips'] > MAX_INT \
                or data['instances'] > MAX_INT or data['cores'] > MAX_INT \
                or data['security_groups'] > MAX_INT or data['security_group_rules'] > MAX_INT:
            msg = _("input value should be less than or equal to 2147483647.")
            raise ValidationError(msg)
        return data

    def getQuotasItem(self, obj, item_name, default):
        return_val = default
        if obj and obj != {}:
            try:
                item_value = obj[item_name]
                if item_value:
                    return_val = item_value
            except Exception, e:
                pass
        return return_val


class AddProjectUserForm(forms.Form):
    """
    the form for adding a user to a tenant
    """
    tenant_id = CharField(widget=widgets.HiddenInput())
    user_id = ChoiceField(label=_("Available User"))
    role_id = ChoiceField(label=_("Role"))

    def __init__(self, request, tenant_id, *args, **kwargs):
        super(AddProjectUserForm, self).__init__(*args, **kwargs)
        role_choices = []
        users = []
        roles = []
        try:
            exist_users = []
            tenants = api.keystone.tenant_list_not_filter(request, admin=True)
            for tenant in tenants:
                tenant_users = api.keystone.user_list(request, tenant.id)
                exist_users.extend(tenant_users)
            users = api.keystone.user_list_not_filter(request)
            roles = api.keystone.role_list(request)
            for user in exist_users:
                if user in users:
                    users.remove(user)
        except Unauthorized:
            raise
        except Exception, e:
            LOG.error(e)

        for role in roles:
            if role.name != ROLE_ADMIN and role.enabled:
                role_choices.append((role.id, role.name))
#            if role.name == ROLE_PROJECTADMIN:
#                role_choices.append((role.id, role.name))
#            elif role.name != ROLE_ADMIN:
#                role_choices.insert(0, (role.id, role.name))

        self.fields['role_id'].choices = role_choices
        user_choices = [(user.id, user.name) for user in users]
        self.fields['user_id'].choices = user_choices
        self.fields['tenant_id'].widget.attrs['value'] = tenant_id


class EditProjectUserForm(forms.Form):
    """
    the form for updating the the role of a user on one tenant
    """
    tenant_id = CharField(widget=widgets.HiddenInput())
    user_id = CharField(widget=widgets.HiddenInput())
    role_id = ChoiceField(label=_("Role"))

    def __init__(self, request, tenant_id, user_id, *args, **kwargs):
        super(EditProjectUserForm, self).__init__(*args, **kwargs)
        role_choices = []
        try:
            roles = api.keystone.role_list(request)
            for role in roles:
                if role.name != ROLE_ADMIN and role.enabled:
                    role_choices.append((role.id, role.name))
#                if role.name == ROLE_PROJECTADMIN:
#                    if get_user_role_name(request) == ROLE_ADMIN:
#                        role_choices.append((role.id, role.name))
#                elif role.name != ROLE_ADMIN:
#                    role_choices.insert(0, (role.id, role.name))
            self.fields['role_id'].choices = role_choices
            self.fields['user_id'].widget.attrs['value'] = user_id
            self.fields['tenant_id'].widget.attrs['value'] = tenant_id
        except Unauthorized:
            raise
        except Exception, e:
            LOG.error(e)
