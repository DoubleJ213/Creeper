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


__author__ = 'liu xu '
__date__ = '2012-02-20'
__version__ = 'v2.0.1'
import md5
from datetime import datetime
import logging

LOG = logging.getLogger(__name__)

from django.conf import settings

if settings.DEBUG:
    __log__ = 'v2.0.1 create'

from django.db import models


class LoggingAction(models.Model):
    uuid = models.CharField(max_length=50,
                            default=md5.new(str(datetime.now())).hexdigest())
    module = models.CharField(max_length=50)
    event = models.CharField(max_length=50)
    create_at = models.CharField(max_length=50)
    username = models.CharField(max_length=50)
    userid = models.CharField(max_length=100)
    tenant = models.CharField(max_length=50)
    tenantid = models.CharField(max_length=100)
    content = models.CharField(max_length=512)
    is_primary = models.CharField(max_length=50)
    status = models.CharField(max_length=50)

    def __unicode__(self):
        return self.create_at
