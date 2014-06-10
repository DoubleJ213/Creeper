"""
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
"""

__author__ = 'sunyu'
__date__ = '2013-11-12'
__version__ = 'v3.1.3'

from django.conf import settings

if settings.DEBUG:
    __log__ = 'v2.0.1 create'

import logging

LOG = logging.getLogger(__name__)

#    code begin
from django import forms
from django.forms import *
from django.utils.translation import ugettext_lazy as _


class TaskCheckForm(forms.Form):
    task_id = CharField(label=_('Task id'),required=True)
    check_comment = CharField(label=_('Check Comment'),
                              widget=widgets.Textarea(), required=False)

    def __init__(self, request, task_id, *args, **kwargs):
        super(TaskCheckForm, self).__init__(*args, **kwargs)
        self.request = request

    def clean(self):
        data = super(forms.Form, self).clean()

        return data