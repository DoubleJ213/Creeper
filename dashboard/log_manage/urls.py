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


__author__ = 'liu xu'
__date__ = '2013-02-20'
__version__ = 'v2.0.1'

from django.conf import settings

if settings.DEBUG:
    __log__ = 'v2.0.1 create'

import logging

LOG = logging.getLogger(__name__)

#    code begin

from django.conf.urls.defaults import patterns
from dashboard.urls import url

urlpatterns = patterns('dashboard.log_manage.views',

    # Query logs for index
    url(r'^logs/query/$', 'log_query_index', name='log_query_index', method='get'),

    url(r'^logs/(?P<uuid>[^/]+)/$', 'delete_log', name='delete_log', method='delete'),

    url(r'^logs/query/delete$', 'delete_logs_query', name='delete_logs_query', method='delete'),
    # Clean all logs for the  system.
    url(r'^logs/(?P<uuid>[^/]+)/form$', 'delete_log_form', name='delete_log_form', method='get'),
    # Get log details for one tenant.
    url(r'^logs/detail/(?P<uuid>[^/]+)/$', 'get_log_detail', name='get_log_detail', method='get'),

    url(r'^logs/export/list$', 'export_logs_list', name='export_logs_list', method='get'),

    url(r'^logs/export/count$', 'export_logs_count', name='export_logs_count', method='get'),
    url(r'^logs/query/home$', 'log_query_home_page', name='log_query_home_page', method='get'),

)