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
__date__ = '2013-11-19'
__version__ = 'v3.1.3'

import logging

from django.conf import settings

from .models import Role_right, Right

if settings.DEBUG:
    __log__ = 'v2.0.1 create'
LOG = logging.getLogger(__name__)


def assert_role_right(role_id, right_name):
    right = Right.objects.filter(name=right_name)
    if right:
        role_right = Role_right.objects.filter(role_id=role_id, right_key=right[0].key)

        if role_right:
            return True
        else:
            return False
    else:
        LOG.error("%s right doesn't exist!" % right_name)
        raise

