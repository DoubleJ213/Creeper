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

__author__ = 'tangjun'
__date__ = '2012-02-17'
__version__ = 'v2.0.1'

import logging

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models

if settings.DEBUG:
    __log__ = 'v2.0.1 create'

LOG = logging.getLogger(__name__)

class Node(models.Model):
    """
     fields:
         uuid : the uuid of Node, md5 hash with the current time value when
         created
         name : the name of Node
         ip   : the ip of Node , it will be IPV4 format
         type : the type of Node, the choice is control_node,storage_node,
         compute_node
         created_at : the time when node created
    """
    uuid = models.CharField(max_length=50)
    name = models.CharField(max_length=30)
    ip = models.IPAddressField()
    passwd = models.CharField(max_length=20)
    type = models.CharField(max_length=20)
    created_at = models.DateTimeField()

    def get_values(self):
        """
        :return: dict value,which will be bounded with form
        """
        return {'uuid': self.uuid, 'name': self.name, 'ip': self.ip,
                'passwd': self.passwd, 'type': self.type}

    def toDict(self):
        """

        :return:
        """
        fields = []
        for field in self._meta.fields:
            fields.append(field.name)

        data = {}
        for attr in fields:
            data[attr] = getattr(self, attr)
        return data

    def to_simple_express(self):
        return {'id': self.uuid,
                'name': self.name,
                'ip': self.ip,
                'type': self.type,
                'link': reverse('get_host_monitor_page',
                                args=[self.uuid, '#host_id#']),
                'status_link': reverse('get_node_monitor_info_item',
                                       args=[self.uuid, 'check_status']),
        }