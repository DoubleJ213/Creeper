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


__author__ = 'gmj'
__date__ = '2012-01-24'
__version__ = 'v2.0.1'

import re
import logging

from django.conf import settings
if settings.DEBUG:
    __log__ = 'v2.0.1 instance_mange,get instance list'

LOG = logging.getLogger(__name__)

#    code begin
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.forms import ValidationError

from dashboard import api
from dashboard.exceptions import Unauthorized, NotFound
from dashboard.utils.validators import has_hz
from dashboard.usage import quotas
from dashboard.authorize_manage.utils import switch_tenants
import dashboard.image_template_manage as ImageMang


class LaunchForm(forms.Form):
    name = forms.CharField(max_length=10, label=_("Server Name"))
    ins_tenant_id = forms.ChoiceField(label="Tenant")
    image_id = forms.ChoiceField(label="Image Template")

    user_data = forms.CharField(widget=forms.Textarea,
                label=_("User Data"),
                required=False)
    flavor = forms.ChoiceField(label=_("Flavor"),
                help_text=_("Size of image to launch."))

    count = forms.IntegerField(label=_("Instance Count"),
            required=True,min_value=1,initial=1,
            help_text=_("Number of instances to launch."))
    security_groups = forms.MultipleChoiceField(
            label=_("Security Groups"),required=True,
            initial=["default"],
            widget=forms.CheckboxSelectMultiple(attrs={'class':'required'}),
            help_text=_("Launch instance in these "
                    "security groups."))
    networks = forms.MultipleChoiceField(
        label=_("Aviable networks"),required=True,
        widget=forms.CheckboxSelectMultiple(attrs={'class':'required'}),
        help_text=_("Select aviable network here."))
    volume = forms.ChoiceField(label=_("Volume or Volume Snapshot"),
            required=False,
            help_text=_("Volume to boot from."))
    device_name = forms.CharField(label=_("Device Name"),
            required=False,
            initial="vda",
            help_text=_("Volume mount point (e.g. 'vda' "
                        "mounts at '/dev/vda')."))
    delete_on_terminate = forms.BooleanField(
            label=_("Delete on Terminate"),
            initial=False,
            required=False,
            help_text=_("Delete volume on instance terminate"))

    flavor_input = forms.ChoiceField(label=_("Flavor Input"),
        help_text=_("Size of image to launch."),
        required=False)
    image_min_disk =forms.ChoiceField(label=_("Flavor Input"),
        help_text=_('The minimum disk size'
                    ' required to boot the'
                    ' image. If unspecified, this'
                    ' value defaults to 0'
                    ' (no minimum).'),
        required=False)

    def __init__(self, request, *args, **kwargs):
        flavor_input_list = kwargs.pop('flavor_input_list')
        flavor_list = kwargs.pop('flavor_list')
        security_group_list = kwargs.pop('security_group_list')
        networks = kwargs.pop('networks')
        volume_list = kwargs.pop('volume_list')
        super(LaunchForm, self).__init__(*args,**kwargs)
        self.fields['flavor'].choices = flavor_list
        self.fields['security_groups'].choices = security_group_list
        if flavor_input_list is not None:
            self.fields['flavor_input'].choices = flavor_input_list
        self.fields['networks'].choices = networks
        self.fields['volume'].choices = volume_list
        tenant_choices = [('', _("Select a project"))]
        try:
            for tenant in api.tenant_list(request, admin=True):
                if tenant.enabled :
                    tenant_choices.append((tenant.id, tenant.name))
            self.fields['ins_tenant_id'].choices = tenant_choices
        except Unauthorized:
            raise
        except Exception,e:
            LOG.error('Unable to retrieve tenant list,%s ' % e)

        image_choices = []
        try:
            images = ImageMang.views.get_images_data(request) or []
            for img in images:
                parm = {'name': img.name, 'min_disk': img.min_disk,'min_ram':img.min_ram}
                image_choices.append((img.id, parm))
            self.fields['image_id'].choices = image_choices
        except Unauthorized:
            raise
        except Exception, e:
            LOG.error('Can not get image list when create instance. %s' % e)


    def clean(self):
        data = super(forms.Form, self).clean()
        tenant_id = data.get('ins_tenant_id',None)
        if not tenant_id:
            return data
        if 'name' in data:
            if re.search(r'\s',data['name']):
                msg = 'no blank space allowed during instance name'
                raise ValidationError(_(msg))
        return data


class UpdateInstanceForm(forms.Form):
    name = forms.CharField(max_length=10,required=True)
    def  __init__(self,request, instance_id,*args,**kwargs):
        super(UpdateInstanceForm,self).__init__(*args,**kwargs)
        try:
            instance = api.server_get(request, instance_id)
            self.fields['name'].initial = getattr(instance,'name',None)
        except Unauthorized:
            raise
        except NotFound:
            raise
        except Exception, e:
            LOG.error('Unable to retrieve instance list,%s ' % e)


class UpdateExistInstanceForm(forms.Form):
    name = forms.CharField(max_length=10,required=True)
    has_group = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple(),required=False)
    security_groups = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple(),
        help_text=_("Launch instance in these "
                    "security groups."))
    def  __init__(self,request, instance_id, instance_name, *args,**kwargs):
        super(UpdateExistInstanceForm,self).__init__(*args,**kwargs)
        self.fields['name'].initial = instance_name
        all_groups = []
        try:
            all_groups = api.nova.security_group_list(request)
        except Unauthorized:
            raise
        except Exception, e:
            LOG.error('Can not retrieve security group list! %s' % e)
        instance_groups = []
        ins_grp_list = []
        groups_list = []
        try:
            instance_groups = api.nova.server_security_groups(request,instance_id)
            group_name = [group.name for group in instance_groups]
            ins_grp_list = [(ins_grp.name,ins_grp.name) for ins_grp in instance_groups]
            groups_list = [(group.name, group.name) for group in all_groups if group.name not in group_name]
        except Unauthorized:
            raise
        except Exception, e:
            LOG.error('Can not retrieve instance groups.%s' % e)
        self.fields['has_group'].choices = ins_grp_list
        self.fields['has_group'].initial = [group.name for group in instance_groups]
        self.fields['security_groups'].choices = groups_list

class CreateSnapshot(forms.Form):
    tenant_id = forms.CharField(widget=forms.HiddenInput())
    snapshot_name = forms.CharField(max_length=10,label=_("Snapshot Name"),required=True)
    def __init__(self,*args,**kwargs):
        tenant_id = kwargs.pop('tenant_id')
        super(CreateSnapshot,self).__init__(*args,**kwargs)
        self.fields['tenant_id'].widget.attrs['value'] = tenant_id

    def clean(self):
        data = super(forms.Form, self).clean()
        if 'snapshot_name' in data:
            snapshot_name = data['snapshot_name']
            if re.search(r'\s', snapshot_name):
                raise ValidationError(_("No blank space allowed in snapshot name"))
        return data

class InstanceClassify(forms.Form):
    classify=forms.CharField(max_length=10,required=True)
    def __init__(self,*args,**kwargs):
        super(InstanceClassify, self).__init__(*args, **kwargs)
    def clean(self):
        data = super(forms.Form, self).clean()
        if 'classify' in data:
            classify_name = data['classify']
            if re.search(r'\s', classify_name):
                raise ValidationError(_("No blank space allowed in classify name"))
        return data

class UpdateInstanceClassify(forms.Form):
    classify_id=forms.CharField(max_length=50,required=True)
    classify_name=forms.CharField(max_length=10,required=True)
    def __init__(self,*args,**kwargs):
        super(UpdateInstanceClassify,self).__init__(*args,**kwargs)
    def clean(self):
        data = super(forms.Form, self).clean()
        if 'classify_name' in data:
            classify_name = data['classify_name']
            if re.search(r'\s', classify_name):
                raise ValidationError(_("No blank space allowed in classify name"))
        return data

class InstanceLiveMigrate(forms.Form):
    instance_id = forms.CharField(widget=forms.HiddenInput)
    host = forms.ChoiceField(label=_("Host"),required=True)
    def __init__(self,*args,**kwargs):
        instance_id = kwargs.pop('instance_id')
        hosts = kwargs.pop('compute_list')
        host_choices = [('', _("Select a compute node"))]
        if hosts:
            for nod in hosts:
                host_choices.append((nod,nod))
        super(InstanceLiveMigrate,self).__init__(*args,**kwargs)
        self.fields['instance_id'].widget.attrs['value'] = instance_id
        self.fields['host'].choices = host_choices


class InstanceLiveMigratePrepare(forms.Form):
    instance_id = forms.CharField(widget=forms.HiddenInput)
    host = forms.ChoiceField(label=_("Host"),required=True)
    def __init__(self,*args,**kwargs):
        instance_id = kwargs.pop('instance_id')
        hosts = kwargs.pop('compute_list')
        host_choices = [('', _("Select a compute node"))]
        if hosts:
            for nod in hosts:
                host_choices.append((nod.hypervisor_hostname,nod.hypervisor_hostname))
        super(InstanceLiveMigratePrepare,self).__init__(*args,**kwargs)
        self.fields['host'].choices = host_choices


class InstanceLiveMigratePrepareForm(forms.Form):
    instance_id = forms.CharField(label=_("Server Name"),required=True)
    host = forms.CharField(label=_("Host"),required=True)
    def __init__(self,*args,**kwargs):
        super(InstanceLiveMigratePrepareForm,self).__init__(*args,**kwargs)

