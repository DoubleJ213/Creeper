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
__date__ = '2012-02-18'
__version__ = 'v2.0.1'

import re
import logging

from django.conf import settings
if settings.DEBUG:
    __log__ = 'v2.0.1 hard_template_manage;add the update form'

LOG = logging.getLogger(__name__)

#    code begin
from django.forms import *
from django import forms
from django.utils.translation import ugettext_lazy as _
from dashboard import api
from dashboard.exceptions import Unauthorized

MAX_MEMORY = 2147483647
MIN_MEMORY = 0

class CreateFlavorForm(forms.Form):
    name = forms.CharField(label=_("Name"),
        max_length=10)
    vcpus = IntegerField(label=_("VCPUs"),
        help_text=_('The cpu number should be larger than 0'))

    memory_mb = IntegerField(label=_("Memory MB"),
        help_text=_("Enter integer value between 1 and 2147483647"))

    disk_gb = IntegerField(label=_("Root Disk GB"),
        help_text=_('disk_gb should be larger than 0.'))

    eph_gb = IntegerField(label=_("Ephemeral Disk GB"),
        help_text=_('The eph_gb should be between 0 and 2147483647'))


    def __init__(self,request,*args,**kwargs):
        super(CreateFlavorForm,self).__init__(*args,**kwargs)
        self.request = request

    def clean(self):
        '''Check to make sure password fields match.'''
        data = super(forms.Form, self).clean()
#        flavor_name = data['name']
#        if not has_hz(flavor_name):
#            msg = 'Flavor Name has chinese.'
#            raise ValidationError(_(msg))

        try:
            flavors = api.flavor_list(self.request)
        except Unauthorized:
            raise
        except Exception, e:
            LOG.error('Unable to retrieve user list in handle_create.%s' % e)
            return data
        if 'name' in data:
            if re.search(r'\s',data['name']):
                msg = 'no blank space allowed during flavor name'
                raise ValidationError(_(msg))
            for index in range(len(flavors)):
                if data['name'] == getattr(flavors[index],'name','unknown'):
                    msg = 'flavor name has exist.'
                    raise ValidationError(_(msg))
        if 'vcpus' in data:
            if data['vcpus'] <= MIN_MEMORY:
                msg = _("cores should be larger than 0.")
                raise ValidationError(msg)
        if 'memory_mb' in data:
            if data['memory_mb'] <= MIN_MEMORY or data['memory_mb'] > MAX_MEMORY:
                msg = _("ram should be larger than 0 and less than 2147483647")
                raise ValidationError(msg)
        if 'disk_gb' in data:
            if data['disk_gb'] <= MIN_MEMORY:
                msg = _("disk_gb should be larger than 0.")
                raise ValidationError(msg)
        if 'eph_gb' in data:
            if data['eph_gb'] < MIN_MEMORY or data['eph_gb'] > MAX_MEMORY:
                msg = _("eph_gb should be larger than or equal to 0 and less than 2147483647.")
                raise ValidationError(msg)
        return data






