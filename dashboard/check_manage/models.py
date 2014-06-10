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
__date__ = '2013-11-08'
__version__ = 'v3.1.3'

from django.db import models

PENDING = 'Pending'
APPROVE = 'Approve'
REJECT = 'Reject'
EXPIRED = 'Expired'

LEVEL_ONE = 1

class Task(models.Model):
    uuid = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=50)
    user_id = models.CharField(max_length=100)
    user_name = models.CharField(max_length=50)
    project_id = models.CharField(max_length=100)
    token_id = models.CharField(max_length=100)
    api = models.CharField(max_length=100)
    args = models.CharField(max_length=2048)
    kwargs = models.CharField(max_length=2048)
    creeper_args = models.CharField(max_length=2048)
    submit_time = models.DateTimeField()
    check_time = models.DateTimeField(null=True, blank=True)
    expire_time = models.DateTimeField()
    status = models.CharField(max_length=20, default=PENDING)
    level = models.IntegerField(default=LEVEL_ONE)
    user_comment = models.CharField(max_length=200, blank=True)
    check_comment = models.CharField(max_length=200, blank=True)
    deleted = models.BooleanField(default=False)
    resume_num = models.IntegerField(default=0)
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = 'task_check'
        ordering = ['expire_time']