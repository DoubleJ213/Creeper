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
__date__ = '2012-01-31'
__version__ = 'v2.0.1'

import logging

from dashboard.utils.i18n import get_text

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models

if settings.DEBUG:
    __log__ = 'v2.0.1 create'

LOG = logging.getLogger(__name__)

#    code begin



class Controller(models.Model):
    """
         The Model of Controller
         columns:
         label_name : the name of action which will show in view
         action_name : the name of action which will be controlled, for exmaples 'create_user'
         action_type : the type of action , value in ['menu'|'action']
         role        : the id of role , from keystone
         parent_id   : the parent_id of this action
    """
    label_name = models.CharField(max_length=30)
    action_name = models.CharField(max_length=30)
    action_type = models.CharField(max_length=10)
    role = models.CharField(max_length=50)
    token = models.CharField(max_length=50)
    parent_id = models.IntegerField()

    def toDict(self):
        fields = []
        for field in self._meta.fields:
            fields.append(field.name)

        d = {}
        for attr in fields:
            if attr == 'action_name':
                try:
                    d[attr] = reverse(getattr(self,attr))
                except:
                    d[attr] = getattr(self,attr)
            else:
                d[attr] = get_text(getattr(self,attr))
        return d
