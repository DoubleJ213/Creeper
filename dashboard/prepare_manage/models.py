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


__author__ = 'liuhuan'
__date__ = '2013-08-19'
__version__ = 'v3.1.2'

import logging

LOG = logging.getLogger(__name__)

from django.conf import settings

if settings.DEBUG:
    __log__ = 'v2.0.8 create'
from django.db import models



class NeedToDo(models.Model):
    id = models.AutoField(max_length=20, primary_key=True)
    need_uuid = models.CharField(max_length=50)
    title = models.CharField(max_length=100)
    parameters = models.CharField(max_length=100)
    content = models.CharField(max_length=200)
    work_func = models.CharField(max_length=500)
    status = models.CharField(max_length=50)      ##new,doing,done,closed
    category = models.CharField(max_length=50)
    role = models.CharField(max_length=50)
    tenant_id = models.CharField(max_length=50)
    prepare_id = models.CharField(max_length=50)

    class Meta:
        db_table = 'need_to_do'
#
