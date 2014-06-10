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
from django.conf.urls.defaults import patterns

from dashboard.urls import url

if settings.DEBUG:
    __log__ = 'v2.0.1 create'

LOG = logging.getLogger(__name__)

urlpatterns = patterns('dashboard.monitor_manage.views',

                       url(r'^$', 'index', name='monitor_manage_index',
                           method='get'),
                       # ajax get monitor usage list
                       url(r'^monitors/usage/$', 'get_system_usage',
                           name='get_system_usage', method='get'),
                       # ajax get monitor usage list
                       url(r'^monitors/usage/(?P<tenant_id>[^/]+)/details/$',
                           'get_tenant_usage_details',
                           name='get_tenant_usage_details', method='get'),
                       # ajax get monitor hosts tree
                       url(r'^monitors/hosts/tree$', 'get_host_tree',
                           name='get_host_tree', method='get'),
                       # ajax get monitor hosts page
                       url(
                           r'^monitors/host/(?P<node_uuid>[^/]+)/page/('
                           r'?P<host_id>[^/]+)/$',
                           'get_host_monitor_page',
                           name='get_host_monitor_page', method='get'),
                       # ajax get monitor instances page
                       url(r'^monitors/instance/(?P<instance_id>[^/]+)/page$',
                           'get_instance_monitor_page',
                           name='get_instance_monitor_page', method='get'),

                       url(r'^monitors/instance/top/$', 'monitor_manage_top',
                           name='monitor_manage_top', method='get'),
                       url(r'^monitors/hardware/info/$', 'get_hardware_info',
                           name='get_hardware_info', method='get'),
                       url(r'^monitors/facility/info/$', 'get_facility_info',
                           name='get_facility_info', method='get'),
                       url(r'^monitors/strategy/$', 'update_threshold_strategy',
                           name='update_threshold_strategy',
                           method='post')
)
