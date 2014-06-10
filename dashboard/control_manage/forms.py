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
__date__ = '2012-01-17'
__version__ = 'v2.0.1'

import logging

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.forms import *

from dashboard import api
from dashboard.utils import validators
from dashboard.exceptions import Unauthorized

from .models import Controller

if settings.DEBUG:
    __log__ = 'v2.0.1 create'

LOG = logging.getLogger(__name__)

#    code begin

class ControllerCreateSnapshot(forms.Form):
    tenant_id = CharField(widget=HiddenInput())
    snapshot_name = CharField(max_length="20", label=_("Snapshot Name"),
        required=True)

    def __init__(self, *args, **kwargs):
        tenant_id = kwargs.pop('tenant_id')
        super(ControllerCreateSnapshot, self).__init__(*args, **kwargs)
        self.fields['tenant_id'].widget.attrs['value'] = tenant_id

