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

from django.conf import settings

if settings.DEBUG:
    __log__ = 'v2.0.5 create'

import logging

LOG = logging.getLogger(__name__)

from django.conf.urls.defaults import patterns
from dashboard.urls import url


urlpatterns = patterns('dashboard.check_manage.views',
   #get the list of task
   url(r'^tasks/$', 'get_task_list', name='get_task_list', method='get'),
   #get task form
   url(r'^tasks/(?P<task_id>[^/]+)/$', 'get_task_form', name='get_task_form', method='get'),
   #check task
   url(r'^tasks/(?P<task_id>[^/]+)/check/$', 'check_task', name='check_task', method='post'),

   # show user's task in index.html
   url(r'^tasks/list/user/$', 'get_user_task_list', name='get_user_task_list', method='get'),
   # show user's all tasks
   url(r'^tasks/list/user/all/$', 'get_user_task_list_all', name='get_user_task_list_all', method='get'),

   # show one task's detail infomation
   url(r'^tasks/(?P<task_id>[^/]+)/detail/$', 'task_detail',
               name='get_task_detail', method='get'),

   # resubmit task
   url(r'^tasks/(?P<task_id>[^/]+)/resubmit/$',
        'resubmit_task_form', name='resubmit_task_form', method='get'),
   url(r'^tasks/(?P<task_id>[^/]+)/action/resubmit$',
        'resubmit_task_action', name='resubmit_task_action', method='post'),

    # delete task
    url(r'^tasks/(?P<task_id>[^/]+)/delete/$',
        'delete_task_form', name='delete_task_form', method='get'),
    url(r'^tasks/(?P<task_id>[^/]+)/action/delete$',
        'delete_task_action', name='delete_task_action', method='delete'),


   # show one task's detail infomation
#                       url(r'^tasks/(?P<user_id>[^/]+)/detail/$', 'task_detail',
#                            name='get_task_detail', method='get'),

#                       url(r'^tasks/(?P<task_id>[^/]+)/(?P<type>reject|edit|delete|resume)/$',
#                            'task_action', name='task_action', method='get'),
#                       url(r'^taskss/resume$', 'resume_task', name='resume_task', method='post'),

#                       url(r'^taskss/delete$', 'resume_task', name='resume_task', method='post'),
   )