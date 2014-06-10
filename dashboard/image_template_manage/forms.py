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
__date__ = '2012-02-04'
__version__ = 'v2.0.1'

import logging

LOG = logging.getLogger(__name__)

from django.conf import settings

if settings.DEBUG:
    __log__ = 'v2.0.1 image_template_manage'
from django.forms import *
from django import forms
from django.utils.translation import ugettext_lazy as _

from dashboard import api
from dashboard.authorize_manage.utils import switch_tenants
from dashboard.software_manage import SOFTWARE_STATE_ACTIVE
from dashboard.software_manage.models import Software
from dashboard.usage import quotas
from dashboard.exceptions import Unauthorized


UI_DISK_FORMAT_CHOICE = [
    ('ami', _('AMI - Amazon Machine Image')),
    ('iso', _('ISO - Optical Disk Image')),
    ('qcow2', _('QCOW2 - QEMU Emulator')),
    ('raw', 'Raw'),
    ('vdi', 'VDI'),
    ('vhd', 'VHD'),
    ('vmdk', 'VMDK')
]

class LaunchImageInstanceForm(forms.Form):
    name_launch = forms.CharField(max_length=20, label=_("Instance Name"),
                                  required=False)
    tenant_id = forms.ChoiceField(label="Tenant")
    user_data = forms.CharField(widget=forms.Textarea, label=_("User Data"),
                                required=False)
    flavor = forms.ChoiceField(label=_("Flavor"),
                               help_text=_("Size of image to launch."))
    key_pair = forms.ChoiceField(label=_("Keypair"), required=False,
                                 help_text=_(
                                     "Which keypair to use for authentication."))
    count = forms.IntegerField(label=_("Instance Count"), required=False,
                               min_value=1, initial=1,
                               help_text=_("Number of instances to launch."))
    volume = forms.ChoiceField(label=_("Volume or Volume Snapshot"),
                               required=False,
                               help_text=_("Volume to boot from."))
    security_groups = forms.MultipleChoiceField(label=_("Security Groups"),
                                                required=False,
                                                initial=["default"],
                                                widget=forms.CheckboxSelectMultiple(),
                                                help_text=_(
                                                    "Launch instance in these security groups."))
    networks = forms.MultipleChoiceField(label=_("Aviable networks"),
                                         required=False,
                                         widget=forms.CheckboxSelectMultiple(),
                                         help_text=_(
                                             "Select aviable network here."))
    device_name = forms.CharField(label=_("Device Name"), required=False,
                                  initial="vda", help_text=_(
            "Volume mount point (e.g. 'vda' mounts at '/dev/vda')."))
    delete_on_terminate = forms.BooleanField(label=_("Delete on Terminate"),
                                             initial=False, required=False,
                                             help_text=_(
                                                 "Delete volume on instance terminate"))

    flavor_input = forms.ChoiceField(label=_("Flavor Input"),
                                     help_text=_("Size of image to launch."),
                                     required=False)

    def __init__(self, request, *args, **kwargs):
        flavor_input_list = kwargs.pop('flavor_input_list')
        flavor_list = kwargs.pop('flavor_list')
        key_pair_list = kwargs.pop('keypair_list')
        self.request = request
        if key_pair_list:
            key_pair_list.insert(0, ("", _("Select a keypair")))
        else:
            key_pair_list = (("", _("No keypairs available.")),)
        security_group_list = kwargs.pop('security_group_list')
        networks = kwargs.pop('networks')
        volume_list = kwargs.pop('volume_list')
        super(LaunchImageInstanceForm, self).__init__(*args, **kwargs)
        self.fields['flavor'].choices = flavor_list
        self.fields['flavor_input'].choices = flavor_input_list
        self.fields['key_pair'].choices = key_pair_list
        self.fields['security_groups'].choices = security_group_list
        self.fields['networks'].choices = networks
        self.fields['volume'].choices = volume_list
        tenant_choices = [('', _("Select a project"))]
        try:
            for tenant in api.tenant_list(request, admin=True):
                if tenant.enabled:
                    tenant_choices.append((tenant.id, tenant.name))
                self.fields['tenant_id'].choices = tenant_choices
        except Unauthorized:
            raise
        except Exception, e:
            LOG.error('Unable to retrieve tenant list,%s ' % e)

    def clean(self):
        data = super(forms.Form, self).clean()
        tenant_id = data.get('tenant_id', None)
        if 'flavor' in data:
            try:
                switch_tenants(self.request, tenant_id)
                usages = quotas.tenant_quota_usages(self.request)
            except Exception, e:
                LOG.error('can not get the usage info of tenant %s,%s' %
                          (tenant_id, e))
                return data
            if usages['instances']['used'] >= usages['instances']['quota']:
                msg = _(
                    "Exceed instances quotas of tenant,can not create instance!")
                raise ValidationError(msg)

        return data

class CreateImageAndLaunchForm(forms.Form):
    name = forms.CharField(max_length=50, label=_("Name"), required=False)
    u_uid = forms.CharField(max_length=100, label=_("Uuid"))
    image_file = forms.FileField(label="Image file", required=False)
    disk_format = forms.ChoiceField(label=_('Disk Format'), required=True,
                                    choices=UI_DISK_FORMAT_CHOICE)
    image_data = forms.ChoiceField(label=_("Image Data"), required=False)
    min_disk = forms.IntegerField(label=_("Min Disk (GB)"), help_text=_(
        'The minimum disk size required to boot the image. If unspecified, this value defaults to 0 (no minimum).'),
                                  required=False)
    min_ram = forms.IntegerField(label=_("Min Ram (MB)"), help_text=_(
        'The minimum ram size required to boot the image. If unspecified, this value defaults to 0 (no minimum).'),
                                 required=False)
    is_public = forms.BooleanField(label=_("Public"), required=False)

    name_launch = forms.CharField(max_length=20, label=_("Instance Name"),
                                  required=False)

    tenant_id = forms.ChoiceField(label="Tenant")
    user_data = forms.CharField(widget=forms.Textarea, label=_("User Data"),
                                required=False)
    flavor = forms.ChoiceField(label=_("Flavor"),
                               help_text=_("Size of image to launch."))
    key_pair = forms.ChoiceField(label=_("Keypair"), required=False,
                                 help_text=_(
                                     "Which keypair to use for authentication."))
    count = forms.IntegerField(label=_("Instance Count"), required=False,
                               min_value=1, initial=1,
                               help_text=_("Number of instances to launch."))
    volume = forms.ChoiceField(label=_("Volume or Volume Snapshot"),
                               required=False,
                               help_text=_("Volume to boot from."))
    security_groups = forms.MultipleChoiceField(label=_("Security Groups"),
                                                required=False,
                                                initial=["default"],
                                                widget=forms.CheckboxSelectMultiple(),
                                                help_text=_(
                                                    "Launch instance in these security groups."))
    networks = forms.MultipleChoiceField(label=_("Aviable networks"),
                                         required=True,
                                         widget=forms.CheckboxSelectMultiple(),
                                         help_text=_(
                                             "Select aviable network here."))
    volume = forms.ChoiceField(label=_("Volume or Volume Snapshot"),
                               required=False,
                               help_text=_("Volume to boot from."))
    device_name = forms.CharField(label=_("Device Name"), required=False,
                                  initial="vda", help_text=_(
            "Volume mount point (e.g. 'vda' mounts at '/dev/vda')."))
    delete_on_terminate = forms.BooleanField(label=_("Delete on Terminate"),
                                             initial=False, required=False,
                                             help_text=_(
                                                 "Delete volume on instance terminate"))

    def __init__(self, request, *args, **kwargs):
        flavor_list = kwargs.pop('flavor_list')
        key_pair_list = kwargs.pop('keypair_list')
        self.request = request

        if key_pair_list:
            key_pair_list.insert(0, ("", _("Select a keypair")))
        else:
            key_pair_list = (("", _("No keypairs available.")),)
        security_group_list = kwargs.pop('security_group_list')
        volume_list = kwargs.pop('volume_list')
        networks = kwargs.pop('networks')
        super(CreateImageAndLaunchForm, self).__init__(*args, **kwargs)
        software_list = [("", _("Select a Image Data"))]
        try:
            soft_wares = Software.objects.filter(classify='SystemSoftware',
                                                 status="active")
            for software in soft_wares:
                path = software.get_local_file()
                display = (path, software.name)
                software_list.append(display)
        except Exception, e:
            LOG.error('Something was wrong when get software list %s' % e)

        self.fields['image_data'].choices = software_list
        self.fields['flavor'].choices = flavor_list
        self.fields['networks'].choices = networks
        self.fields['key_pair'].choices = key_pair_list
        self.fields['security_groups'].choices = security_group_list
        self.fields['volume'].choices = volume_list
        tenant_choices = [('', _("Select a project"))]

        try:
            for tenant in api.tenant_list(request, admin=True):
                if tenant.enabled:
                    tenant_choices.append((tenant.id, tenant.name))
                self.fields['tenant_id'].choices = tenant_choices
        except Unauthorized:
            raise
        except Exception, e:
            LOG.error('Unable to retrieve tenant list,%s ' % e)

    def clean(self):
        data = super(forms.Form, self).clean()
        tenant_id = data.get('tenant_id', None)
        name_launch = data.get('name_launch', None)
        if len(name_launch) < 2:
            raise ValidationError(_("Server Name value between 2 and 10."))
        elif len(name_launch) >10:
            raise ValidationError(_("Server Name value between 2 and 10."))


        check_data(data)

        if 'flavor' in data:
            try:
                flavor_id = None
                api.flavor_get(self.request, data['flavor'])
                flavors = api.flavor_list(self.request)
                for flavor in flavors:
                    if str(flavor.id) is str(data['flavor']):
                        flavor_id = flavor
                        break
                if flavor_id is not None and flavor_id.disk < int(
                    data['min_disk']):
                    msg = 'Instance flavor disk less-than Image min disk!'
                    raise ValidationError(_(msg))
                if flavor_id is not None and flavor_id.ram < int(
                    data['min_ram']):
                    msg = 'Instance flavor ram less-than Image min ram!'
                    raise ValidationError(_(msg))
            except Unauthorized:
                raise
            except Exception, e:
                LOG.error('can not get the usage info of tenant %s,%s' %
                          (tenant_id, e))
                return data
        try:
            switch_tenants(self.request, tenant_id)
            usages = quotas.tenant_quota_usages(self.request)
        except Exception, e:
            LOG.error(
                'can not get the usage info of tenant %s,%s' % (tenant_id, e))
            return data
        if usages['instances']['used'] >= usages['instances']['quota']:
            msg = _(
                "Exceed instances quotas of tenant,can not create instance!")
            raise ValidationError(msg)

        return data

#class CreateImageAndLaunchForm(forms.Form):
#    name = forms.CharField(max_length=50, label=_("Name"), required=False)
#    u_uid = forms.CharField(max_length=100, label=_("Uuid"))
#    image_file = forms.FileField(label="Image file", required=False)
#    disk_format = forms.ChoiceField(label=_('Disk Format'), required=True,
#                                    choices=UI_DISK_FORMAT_CHOICE)
#    image_data = forms.CharField(label=_("Image Data"), required=False)
#    min_disk = forms.IntegerField(label=_("Min Disk (GB)"), help_text=_(
#        'The minimum disk size required to boot the image. If unspecified, this value defaults to 0 (no minimum).'),
#                                  required=False)
#    min_ram = forms.IntegerField(label=_("Min Ram (MB)"), help_text=_(
#        'The minimum ram size required to boot the image. If unspecified, this value defaults to 0 (no minimum).'),
#                                 required=False)
#    is_public = forms.BooleanField(label=_("Public"), required=False)
#
#    name_launch = forms.CharField(max_length=20, label=_("Instance Name"),
#                                  required=False)
#
#    tenant_id = forms.CharField(label="Tenant")
#    user_data = forms.CharField(widget=forms.Textarea, label=_("User Data"),
#                                required=False)
#    flavor = forms.CharField(label=_("Flavor"),
#                               help_text=_("Size of image to launch."))
#    key_pair = forms.ChoiceField(label=_("Keypair"), required=False,
#                                 help_text=_(
#                                     "Which keypair to use for authentication."))
#    count = forms.IntegerField(label=_("Instance Count"), required=False,
#                               min_value=1, initial=1,
#                               help_text=_("Number of instances to launch."))
#    volume = forms.CharField(label=_("Volume or Volume Snapshot"),
#                               required=False,
#                               help_text=_("Volume to boot from."))
#    security_groups = forms.MultipleChoiceField(label=_("Security Groups"),
#                                                required=False,
#                                                initial=["default"],
#                                                widget=forms.CheckboxSelectMultiple(attrs={'class':'required'}),
#                                                help_text=_(
#                                                    "Launch instance in these security groups."))
#    networks = forms.MultipleChoiceField(label=_("Aviable networks"),
#                                         required=False,
#                                         widget=forms.CheckboxSelectMultiple(),
#                                         help_text=_(
#                                             "Select aviable network here."))
#    device_name = forms.CharField(label=_("Device Name"), required=False,
#                                  initial="vda", help_text=_(
#            "Volume mount point (e.g. 'vda' mounts at '/dev/vda')."))
#    delete_on_terminate = forms.BooleanField(label=_("Delete on Terminate"),
#                                             initial=False, required=False,
#                                             help_text=_(
#                                                 "Delete volume on instance terminate"))
#
#    def __init__(self, request, *args, **kwargs):
#        flavor_list = kwargs.pop('flavor_list')
#        key_pair_list = kwargs.pop('keypair_list')
#        self.request = request
#
#        if key_pair_list:
#            key_pair_list.insert(0, ("", _("Select a keypair")))
#        else:
#            key_pair_list = (("", _("No keypairs available.")),)
#        security_group_list = kwargs.pop('security_group_list')
#        volume_list = kwargs.pop('volume_list')
#        networks = kwargs.pop('networks')
#        software_list = [("", _("Select a Image Data"))]
#        try:
#            soft_wares = Software.objects.filter(classify='SystemSoftware',
#                                                 status=SOFTWARE_STATE_ACTIVE)
#            for software in soft_wares:
#                path = software.get_local_file()
#                display = (path, software.name)
#                software_list.append(display)
#        except Exception, e:
#            LOG.error('Something was wrong when get software list %s' % e)
#
#        super(CreateImageAndLaunchForm, self).__init__(*args, **kwargs)
#
#        self.fields['image_data'].choices = software_list
#        self.fields['flavor'].choices = flavor_list
#        self.fields['networks'].choices = networks
#        self.fields['key_pair'].choices = key_pair_list
#        self.fields['security_groups'].choices = security_group_list
#        self.fields['volume'].choices = volume_list
#        tenant_choices = [('', _("Select a project"))]
#
#        try:
#            for tenant in api.tenant_list(request, admin=True):
#                if tenant.enabled:
#                    tenant_choices.append((tenant.id, tenant.name))
#                self.fields['tenant_id'].choices = tenant_choices
#        except Unauthorized:
#            raise
#        except Exception, e:
#            LOG.error('Unable to retrieve tenant list,%s ' % e)
#
#    def clean(self):
#        data = super(forms.Form, self).clean()
#        tenant_id = data.get('tenant_id', None)
#        name_launch = data.get('name_launch', None)
#        if len(name_launch) < 2:
#            raise ValidationError(_("Server Name value between 2 and 10."))
#        elif len(name_launch) >10:
#            raise ValidationError(_("Server Name value between 2 and 10."))
#
#
#        check_data(data)
#
#        if 'flavor' in data:
#            try:
#                flavor_id = None
#                api.flavor_get(self.request, data['flavor'])
#                flavors = api.flavor_list(self.request)
#                for flavor in flavors:
#                    if str(flavor.id) is str(data['flavor']):
#                        flavor_id = flavor
#                        break
#                if flavor_id is not None and flavor_id.disk < int(
#                    data['min_disk']):
#                    msg = 'Instance flavor disk less-than Image min disk!'
#                    raise ValidationError(_(msg))
#                if flavor_id is not None and flavor_id.ram < int(
#                    data['min_ram']):
#                    msg = 'Instance flavor ram less-than Image min ram!'
#                    raise ValidationError(_(msg))
#            except Unauthorized:
#                raise
#            except Exception, e:
#                LOG.error('can not get the usage info of tenant %s,%s' %
#                          (tenant_id, e))
#                return data
#        try:
#            switch_tenants(self.request, tenant_id)
#            usages = quotas.tenant_quota_usages(self.request)
#        except Exception, e:
#            LOG.error(
#                'can not get the usage info of tenant %s,%s' % (tenant_id, e))
#            return data
#        if usages['instances']['used'] >= usages['instances']['quota']:
#            msg = _(
#                "Exceed instances quotas of tenant,can not create instance!")
#            raise ValidationError(msg)
#
#        return data

#Just as an argument
#begin
DATA_NUMBER_DISK_ZERO = 0
DATA_NUMBER_DISK_MAX = 30
DATA_NUMBER_DISK_MIN = 15
DATA_NUMBER_RAM_MAX = 16384
DATA_NUMBER_RAM_MIN = 512
#end

def check_data(data):
    path = data['image_data']
    min_disk = DATA_NUMBER_DISK_ZERO
    min_ram = DATA_NUMBER_DISK_ZERO
    try:
        if data['min_disk'] >= DATA_NUMBER_DISK_ZERO:
            min_disk = int(data['min_disk'])
        if data['min_ram'] >= DATA_NUMBER_DISK_ZERO:
            min_ram = int(data['min_ram'])
    except Exception, exc:
        LOG.error(exc)
        msg = 'The ram(min_ram) format or disk(min_disk) format wrong'
        raise ValidationError(_(msg))


    if min_disk < DATA_NUMBER_DISK_MIN or  min_disk > DATA_NUMBER_DISK_MAX:
        msg = 'Image min_disk not between 15 and 30.'
        raise ValidationError(_(msg))
    if min_ram < DATA_NUMBER_RAM_MIN or min_ram > DATA_NUMBER_RAM_MAX:
        msg = 'Image min_ram not between 512 and 16384.'
        raise ValidationError(_(msg))
    if path == 'False':
        msg = 'Image Path file depletion'
        raise ValidationError(_(msg))


class LaunchImagePrepareForm(forms.Form):
    name = forms.CharField(max_length=50, label=_("Name"))
    disk_format = forms.ChoiceField(label=_('Disk Format'), required=True,
                                    choices=UI_DISK_FORMAT_CHOICE)
    image_data = forms.ChoiceField(label=_("Image Data"))
    min_disk = forms.IntegerField(label=_("Min Disk (GB)"), help_text=_(
        'The minimum disk size required to boot the image. If unspecified, this value defaults to 0 (no minimum)'),
                                  required=False)
    min_ram = forms.IntegerField(label=_("Min Ram (MB)"), help_text=_(
        'The minimum ram size required to boot the image. If unspecified, this value defaults to 0 (no minimum).'),
                                 required=False)
    is_public = forms.BooleanField(label=_("Public"), required=False)
    img_tenant_id = forms.CharField(label="Tenant")

    name_launch = forms.CharField(max_length=20, label=_("Instance Name"),
                                  required=False)
    tenant_id = forms.CharField(label="Tenant")
    user_data = forms.CharField(widget=forms.Textarea, label=_("User Data"),
                                required=False)
    flavor = forms.CharField(label=_("Flavor"),
                             help_text=_("Size of image to launch."))
    key_pair = forms.CharField(label=_("Keypair"), required=False,
                               help_text=_(
                                   "Which keypair to use for authentication."))
    count = forms.IntegerField(label=_("Instance Count"), required=False,
                               min_value=1, initial=1,
                               help_text=_("Number of instances to launch."))
    #    security_groups = forms.MultipleChoiceField(label=_("Security Groups"),
    #                                                required=False,
    #                                                initial=["default"],
    #                                                help_text=_(
    #                                                    "Launch instance in these security groups."))
    security_groups = forms.MultipleChoiceField(
        label=_("Security Groups"),required=True,
        initial=["default"],
        widget=forms.CheckboxSelectMultiple(attrs={'class':'required'}),
        help_text=_("Launch instance in these "
                    "security groups."))
    networks = forms.MultipleChoiceField(label=_("Aviable networks"),
                                         required=True,
                                         widget=forms.CheckboxSelectMultiple(),
                                         help_text=_(
                                             "Select aviable network here."))
    volume = forms.CharField(label=_("Volume or Volume Snapshot"),
                             required=False,
                             help_text=_("Volume to boot from."))

    flavor_input = forms.CharField(label=_("Flavor Input"),
                                   help_text=_("Size of image to launch."),
                                   required=False)

    def __init__(self, request, *args, **kwargs):
        flavor_input_list = kwargs.pop('flavor_input_list')
        flavor_list = kwargs.pop('flavor_list')
        key_pair_list = kwargs.pop('keypair_list')
        self.request = request
        if key_pair_list:
            key_pair_list.insert(0, ("", _("Select a keypair")))
        else:
            key_pair_list = (("", _("No keypairs available.")),)
        security_group_list = kwargs.pop('security_group_list')
        networks = kwargs.pop('networks')
        volume_list = kwargs.pop('volume_list')
        super(LaunchImagePrepareForm, self).__init__(*args, **kwargs)
        tenant_choices = [('', _("Select a project"))]
        try:
            for tenant in api.tenant_list(self.request, admin=True):
                if tenant.enabled:
                    tenant_choices.append((tenant.id, tenant.name))
        except Unauthorized:
            raise
        except Exception, e:
            LOG.error('Unable to retrieve tenant list,%s ' % e)
        software_list = [("", _("Select a Image Data"))]
        try:
            soft_wares = Software.objects.filter(classify='SystemSoftware',
                                                 status=SOFTWARE_STATE_ACTIVE)
            for software in soft_wares:
                path = software.get_local_file()
                display = (path, software.name)
                software_list.append(display)
        except Exception, e:
            LOG.error('Something was wrong when get software list %s' % e)
        self.fields['flavor'].choices = flavor_list
        self.fields['flavor_input'].choices = flavor_input_list
        self.fields['key_pair'].choices = key_pair_list
        self.fields['security_groups'].choices = security_group_list
        self.fields['networks'].choices = networks
        self.fields['volume'].choices = volume_list
        self.fields['image_data'].choices = software_list
        self.fields['img_tenant_id'].choices = tenant_choices

    def clean(self):
        data = super(forms.Form, self).clean()
        tenant_id = data.get('tenant_id', None)

        check_data(data)

        if 'flavor' in data:
            try:
                switch_tenants(self.request, tenant_id)
                usages = quotas.tenant_quota_usages(self.request)
            except Exception, e:
                LOG.error('can not get the usage info of tenant %s,%s' %
                          (tenant_id, e))
                return data
            if usages['instances']['used'] >= usages['instances']['quota']:
                msg = _(
                    "Exceed instances quotas of tenant,can not create instance!")
                raise ValidationError(msg)

        return data

class LaunchImageAndInstanceForm(forms.Form):
    name = forms.CharField(max_length=50, label=_("Name"))
    disk_format = forms.CharField(label=_('Disk Format'), required=True)
    image_data = forms.CharField(label=_("Image Data"))
    min_disk = forms.IntegerField(label=_("Min Disk (GB)"), help_text=_(
        'The minimum disk size required to boot the image. If unspecified, this value defaults to 0 (no minimum)'),
                                  required=False)
    min_ram = forms.IntegerField(label=_("Min Ram (MB)"), help_text=_(
        'The minimum ram size required to boot the image. If unspecified, this value defaults to 0 (no minimum).'),
                                 required=False)
    is_public = forms.BooleanField(label=_("Public"), required=False)
    img_tenant_id = forms.CharField(label="Tenant")

    name_launch = forms.CharField(max_length=20, label=_("Instance Name"),
                                  required=False)
    tenant_id = forms.CharField(label="Tenant")
    user_data = forms.CharField(widget=forms.Textarea, label=_("User Data"),
                                required=False)
    flavor = forms.CharField(label=_("Flavor"),
                               help_text=_("Size of image to launch."))
    key_pair = forms.CharField(label=_("Keypair"), required=False,
                                 help_text=_(
                                     "Which keypair to use for authentication."))
    count = forms.IntegerField(label=_("Instance Count"), required=False,
                               min_value=1, initial=1,
                               help_text=_("Number of instances to launch."))
    volume = forms.CharField(label=_("Volume or Volume Snapshot"),
                               required=False,
                               help_text=_("Volume to boot from."))
#    security_groups = forms.MultipleChoiceField(label=_("Security Groups"),
#                                                required=False,
#                                                initial=["default"],
#                                                help_text=_(
#                                                    "Launch instance in these security groups."))
    security_groups = forms.MultipleChoiceField(
                                            label=_("Security Groups"),required=True,
                                            initial=["default"],
                                            widget=forms.CheckboxSelectMultiple(attrs={'class':'required'}),
                                            help_text=_("Launch instance in these "
                                             "security groups."))
    networks = forms.CharField(label=_("Aviable networks"),
                                         required=False,
                                         help_text=_(
                                             "Select aviable network here."))
    volume = forms.CharField(label=_("Volume or Volume Snapshot"),
                               required=False,
                               help_text=_("Volume to boot from."))

    flavor_input = forms.CharField(label=_("Flavor Input"),
                                     help_text=_("Size of image to launch."),
                                     required=False)

    def __init__(self,request, *args, **kwargs):
        self.request = request
        flavor_input_list = kwargs.pop('flavor_input_list')
        flavor_list = kwargs.pop('flavor_list')
        key_pair_list = kwargs.pop('keypair_list')

        if key_pair_list:
            key_pair_list.insert(0, ("", _("Select a keypair")))
        else:
            key_pair_list = (("", _("No keypairs available.")),)
        security_group_list = kwargs.pop('security_group_list')
        volume_list = kwargs.pop('volume_list')
        networks = kwargs.pop('networks')
        super(LaunchImageAndInstanceForm, self).__init__(*args, **kwargs)
        tenant_choices = [('', _("Select a project"))]

        try:
            for tenant in api.tenant_list(self.request, admin=True):
                if tenant.enabled:
                    tenant_choices.append((tenant.id, tenant.name))
        except Unauthorized:
            raise
        except Exception, e:
            LOG.error('Unable to retrieve tenant list,%s ' % e)
        software_list = [("", _("Select a Image Data"))]
        try:
            soft_wares = Software.objects.filter(classify='SystemSoftware',
                                                 status=SOFTWARE_STATE_ACTIVE)
            for software in soft_wares:
                path = software.get_local_file()
                display = (path, software.name)
                software_list.append(display)
        except Exception, e:
            LOG.error('Something was wrong when get software list %s' % e)
        self.fields['flavor'].choices = flavor_list
        self.fields['key_pair'].choices = key_pair_list
        self.fields['security_groups'].choices = security_group_list
        self.fields['volume'].choices = volume_list
        self.fields['image_data'].choices = software_list
        self.fields['networks'].choices = networks
        self.fields['img_tenant_id'].choices = tenant_choices

    def clean(self):
        data = super(forms.Form, self).clean()
        tenant_id = data.get('tenant_id', None)

        check_data(data)
        data['networks'] = self.request.POST.getlist("networks")

        if 'flavor' in data:
            try:
                switch_tenants(self.request, tenant_id)
                usages = quotas.tenant_quota_usages(self.request)
            except Exception, e:
                LOG.error('can not get the usage info of tenant %s,%s' %
                          (tenant_id, e))
                return data
            if usages['instances']['used'] >= usages['instances']['quota']:
                msg = _(
                    "Exceed instances quotas of tenant,can not create instance!")
                raise ValidationError(msg)

        return data

class CreateImageForm(forms.Form):
    u_uid = forms.CharField(max_length=100, label=_("Uuid"))
    name = forms.CharField(max_length=50, label=_("Name"))
    disk_format = forms.ChoiceField(label=_('Disk Format'), required=True,
                                    choices=UI_DISK_FORMAT_CHOICE)
    image_data = forms.ChoiceField(label=_("Image Data"))
    min_disk = forms.IntegerField(label=_("Min Disk (GB)"), help_text=_(
        'The minimum disk size required to boot the image. If unspecified, this value defaults to 0 (no minimum)'),
                                  required=False)
    min_ram = forms.IntegerField(label=_("Min Ram (MB)"), help_text=_(
        'The minimum ram size required to boot the image. If unspecified, this value defaults to 0 (no minimum).'),
                                 required=False)
    is_public = forms.BooleanField(label=_("Public"), required=False)
    img_tenant_id = forms.ChoiceField(label="Tenant")

    def __init__(self, request, *args, **kwargs):
        self.request = request
        tenant_choices = [('', _("Select a project"))]
        try:
            for tenant in api.tenant_list(self.request, admin=True):
                if tenant.enabled:
                    tenant_choices.append((tenant.id, tenant.name))
        except Unauthorized:
            raise
        except Exception, e:
            LOG.error('Unable to retrieve tenant list,%s ' % e)
        software_list = [("", _("Select a Image Data"))]
        try:
            soft_wares = Software.objects.filter(classify='SystemSoftware',
                                                 status=SOFTWARE_STATE_ACTIVE)
            for software in soft_wares:
                path = software.get_local_file()
                display = (path, software.name)
                software_list.append(display)
        except Exception, e:
            LOG.error('Something was wrong when get software list %s' % e)
        super(CreateImageForm, self).__init__(*args, **kwargs)
        self.fields['image_data'].choices = software_list
        self.fields['img_tenant_id'].choices = tenant_choices


    def clean(self):
        data = super(forms.Form, self).clean()
        tenant_id = data.get('img_tenant_id', None)
        name = data.get('name', None)
        if len(name) < 2:
            raise ValidationError(_("Image Name value between 2 and 10."))
        elif len(name) >10:
            raise ValidationError(_("Image Name value between 2 and 10."))
        check_data(data)

        try:
            usages = quotas.tenant_quota_usages(self.request)
        except Exception, e:
            LOG.error(
                'can not get the usage info of tenant %s,%s' % (tenant_id, e))
            return data
        if usages['instances']['used'] >= usages['instances']['quota']:
            msg = _(
                "Exceed instances quotas of tenant,can not create instance!")
            raise ValidationError(msg)

        return data


class UpdateImageForm(forms.Form):
    image_id = forms.CharField(widget=forms.HiddenInput())
    name = forms.CharField(max_length=50, label=_("Name"))
    disk_format = forms.CharField(label=_("Disk Format"),
                                  widget=forms.TextInput(
                                      attrs={'readonly': 'readonly'}))
    disk_format_list = forms.ChoiceField(label=_('Disk Format'), required=False,
                                         choices=UI_DISK_FORMAT_CHOICE)
    min_disk = forms.IntegerField(label=_("Min Disk (GB)"), help_text=_(
        'The minimum disk size required to boot the image. If unspecified, this value defaults to 0 (no minimum)'),
                                  required=False)
    min_ram = forms.IntegerField(label=_("Min Ram (MB)"), help_text=_(
        'The minimum ram size required to boot the image. If unspecified, this value defaults to 0 (no minimum).'),
                                 required=False)
    enabled = forms.BooleanField(label=_("Public"), required=False)

    def __init__(self, request, image_id, *args, **kwargs):
        super(UpdateImageForm, self).__init__(*args, **kwargs)
        try:
            image = api.image_get(request, image_id)

            name = getattr(image, 'name', None)
            disk_format = getattr(image, 'disk_format', None)
            min_disk = getattr(image, 'min_disk', None)
            min_ram = getattr(image, 'min_ram', None)
            enabled = getattr(image, 'is_public', None)

            self.fields['image_id'].initial = image_id
            self.fields['name'].initial = name
            self.fields['disk_format'].initial = disk_format
            self.fields['min_disk'].initial = min_disk
            self.fields['min_ram'].initial = min_ram
            self.fields['enabled'].initial = enabled
        except Unauthorized:
            raise
        except Exception, e:
            LOG.error('Error is :%s' % e)
            raise
    def clean(self):
        data = super(forms.Form, self).clean()

        min_disk = DATA_NUMBER_DISK_ZERO
        min_ram = DATA_NUMBER_DISK_ZERO
        try:
            if data['min_disk'] >= DATA_NUMBER_DISK_ZERO:
                min_disk = int(data['min_disk'])
            if data['min_ram'] >= DATA_NUMBER_DISK_ZERO:
                min_ram = int(data['min_ram'])
        except Exception, exc:
            LOG.error(exc)
            msg = 'The ram(min_ram) format or disk(min_disk) format wrong'
            raise ValidationError(_(msg))
        return data
