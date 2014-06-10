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


__author__ = 'tangjun'
__date__ = '2012-02-20'
__version__ = 'v2.0.1'

from django.conf import settings
if settings.DEBUG:
    __log__ = 'v2.0.1 create'

import logging
LOG = logging.getLogger(__name__)

#    code begin
import re

from django.forms import *
from django.utils.translation import ugettext_lazy as _

from dashboard.software_manage import SOFTWARE_FLATS, SOFTWARE_CLASSIFY

from .models import Software


class SoftwareForm(forms.Form):

    name = CharField(label=_("Label Name"), max_length=10, min_length=2)
    flat = ChoiceField(label=_("flat"))
    file = FileField()
    classify = CharField(label=_("Classify"), max_length=30)

    def __init__(self, request, *args, **kwargs):
        super(SoftwareForm, self).__init__(*args, **kwargs)

        self.fields['flat'].choices = SOFTWARE_FLATS
        self.fields['classify'].choices = SOFTWARE_CLASSIFY

    def clean(self):
        data = super(forms.Form, self).clean()
        if ('file' not in data) or ('name' not in data):
            return data

        file_name = data['file']._name
        software_name = data['name']

        if re.search(r'\s', software_name):
            raise ValidationError(_("no blank space allowed during software name"))
        if re.search(r'\s', file_name):
            raise ValidationError(_("no blank space allowed during the upload file name"))

        software = Software.objects.filter(name=software_name)
        if software:
            raise ValidationError(_("software name has exist!"))

        return data
