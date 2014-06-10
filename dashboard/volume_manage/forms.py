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
__date__ = '2012-02-20'
__version__ = 'v2.0.1'

import logging

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

if settings.DEBUG:
    __log__ = 'v2.0.1 create volume'

LOG = logging.getLogger(__name__)

#    code begin

ACTIVE_STATES = ("ACTIVE",)

class CreateVolumeForm(forms.Form):
    volume_name = forms.CharField(max_length=10,min_length=2, label="Volume Name")
    volume_description = forms.CharField(widget=forms.Textarea,
        label=_("Description"), required=False)
    volume_size = forms.CharField(label="Size (GB)")
    tenant_id = forms.CharField(required=True)
    snapshot_id = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super(CreateVolumeForm, self).__init__(*args, **kwargs)

    def clean(self):
        data = super(forms.Form , self).clean()
        volume_description = data.get("volume_description" , None)
        if not volume_description or 'None' == volume_description :
            data['volume_description'] = 'None'
        return data




class UpdateVolumeForm(forms.Form):
    name = forms.CharField(max_length=10, min_length=2, label="Volume Name", required=True)
    description = forms.CharField(widget=forms.Textarea,
        label=_("Description"), required=False)


class AttachForm(forms.Form):
    instance_id = forms.ChoiceField(label="Attach to Instance")
    device = forms.CharField(label="Device Name", initial="/dev/vdc")

    def __init__(self, *args, **kwargs):
        super(AttachForm, self).__init__(*args, **kwargs)
        # populate volume_id

        #        self.fields['volume_id'] = forms.CharField(widget=forms.HiddenInput(),
        #            initial=volume_id)

        # Populate instance choices


class CreateVolumeSnapshot(forms.Form):
    name = forms.CharField(max_length=10, min_length=2, required=True)
    description = forms.CharField(max_length=100, required=False)
    volume_id = forms.CharField(required=True)
    tenant_id = forms.CharField(required=True)

    def __init__(self, *args, **kwargs):
        super(CreateVolumeSnapshot, self).__init__(*args, **kwargs)
