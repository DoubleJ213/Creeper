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
__date__ = '2013-10-21'
__version__ = 'v3.1.3'

from django.db import models

class Right(models.Model):
    """
    The Model of Right
    columns:
    key : the key of right
    name : the name of right
    created_at : time that right was created
    enabled : the right is or is not available
    depends : the key of right depended
    mutex : the key of right mutex
    description : description of right
    """
    key = models.CharField(max_length=10, db_index=True, unique=True)
    name = models.CharField(max_length=100, db_index=True, unique=True)
    parent_id = models.IntegerField()
    created_at = models.DateTimeField()
    enabled = models.BooleanField()
    depends = models.TextField(blank=True)
    mutex = models.TextField(blank=True)
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = 'rights'


class Role_right(models.Model):
    """
    The Model for Role_right
    columns:
    role_id : the id of role
    right_key : the key of right
    """
    role_id = models.CharField(max_length=64)
    right_key = models.CharField(max_length=10)

    class Meta:
        db_table = 'role_right'

