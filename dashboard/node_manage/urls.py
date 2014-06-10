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

urlpatterns = patterns('dashboard.node_manage.views',
                       #get node list
                       url(r'^nodes/$', 'index_node', name='get_node_index',
                           method='get'),
                       #get table of node create
                       url(r'^nodes/new/$', 'create_node', name='create_node',
                           method='get'),
                       #create action for node
                       url(r'^nodes/$', 'create_node_action',
                           name='create_node_action', method='post'),
                       #delete action for node
                       url(r'^nodes/(?P<node_uuid>[^/]+)/delete$',
                           'delete_node_form', name='delete_node_form',
                           method='get'),

                       url(r'^nodes/(?P<node_uuid>[^/]+)/$', 'delete_node',
                           name='delete_node', method='delete'),
                       #get table of node edit
                       url(r'^nodes/(?P<node_uuid>[^/]+)/edit$', 'update_node',
                           name='update_node', method='get'),
                       #edit action for node
                       url(r'^nodes/(?P<node_uuid>[^/]+)/$',
                           'update_node_action', name='update_node_action',
                           method='post'),
                       #get monitor information
                       url(
                           r'^nodes/(?P<node_uuid>[^/]+)/monitor_infos/('
                           r'?P<host_id>[^/]+)$',
                           'get_node_monitor_info_item',
                           name='get_node_monitor_info_item', method='get'),
                       #get monitor information
                       url(r'^nodes/status$', 'get_all_hosts_status',
                           name='get_all_hosts_status', method='get'),
                       #get host meta data
                       url(r'^nodes/metadata', 'get_host_metadata',
                           name='get_host_metadata', method='get'),
)
