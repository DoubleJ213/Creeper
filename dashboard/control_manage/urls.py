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
__date__ = '2012-01-30'
__version__ = 'v2.0.1'

import logging

from django.conf import settings

if settings.DEBUG:
    __log__ = 'v2.0.1 create'

LOG = logging.getLogger(__name__)

#    code begin

from django.conf.urls.defaults import patterns
from dashboard.urls import url

urlpatterns = patterns('dashboard.control_manage.views',
    url(r'^controllers/$', 'index_controller', name='get_controller_menu',
        method='get'),

    url(r'^controllers/(?P<type>all|menu|action)/$', 'index_controller',
        name='get_controllers', method='get'),
    url(
        r'^controllers/client/projects/(?P<project_id>[^/]+)/instances/(?P<instance_id>[^/]+)/rebootinstance/$',
        'reboot_instance_client', name='reboot_instance_client', method='get'),

    url(
        r'^controllers/client/projects/(?P<project_id>[^/]+)/instances/(?P<instance_id>[^/]+)/stopinstance/$',
        'stop_instance_client', name='stop_instance_client', method='get'),

    url(
        r'^controllers/client/projects/(?P<project_id>[^/]+)/instances/(?P<instance_id>[^/]+)/unstopinstance/$',
        'unstop_instance_client', name='unstop_instance_client', method='get'),

    url(
        r'^controllers/client/projects/(?P<project_id>[^/]+)/instances/(?P<instance_id>[^/]+)/instance/status$',
        'get_client_instance_status', name='get_client_instance_status',
        method='get'),

    url(
        r'^controllers/client/projects/(?P<project_id>[^/]+)/instances/(?P<instance_id>[^/]+)/instance/task$',
        'get_client_instance_task', name='get_client_instance_task',
        method='get'),

    url(
        r'^controllers/client/projects/(?P<project_id>[^/]+)/instances/(?P<instance_id>[^/]+)/instance/power$',
        'get_client_instance_power', name='get_client_instance_power',
        method='get'),
)

