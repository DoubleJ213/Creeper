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

import os

from django.db import models


class Software(models.Model):
    """
    fields:
        uuid : the uuid of Software
        check_sum : the md5 hashcode of this software
        name : the name of software
        path : the binary package path
        flat : the type of software
        status : the status of this software
        content_type : the type of binary package
        content_total : total bytes of binary package
        content_name : origin name of binary package
        created_at : the time when software created
    """
    uuid = models.CharField(max_length=50, unique=True)
    check_sum = models.CharField(max_length=50)
    name = models.CharField(max_length=30)
    path = models.CharField(max_length=50)  # deprecated
    flat = models.CharField(max_length=10)
    status = models.CharField(max_length=10, default='')
    content_type = models.CharField(max_length=200)
    content_total = models.BigIntegerField()
    content_name = models.CharField(max_length=500)
    created_at = models.DateTimeField()
    # modify by zhaolei
    file_name = models.CharField(max_length=500)
    classify = models.CharField(max_length=50)

    # modify by zhaolei
    def get_local_file(self):
        file_name = self.file_name
        local_file_path = os.path.join(settings.MEDIA_ROOT, file_name)
        if os.path.exists(local_file_path):
            return local_file_path
        else:
            return False


class SoftwareCollect(models.Model):
    """
    fields:
        userid : the id of User
        softwareuuid : the uuid of Software
    """
    userid = models.CharField(max_length=50)
    softwareuuid = models.CharField(max_length=50)
