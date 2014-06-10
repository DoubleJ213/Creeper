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
__date__ = '2012-01-24'
__version__ = 'v2.0.1'

from django.conf import settings
if settings.DEBUG:
    __log__ = 'v2.0.1 create'

import logging
LOG = logging.getLogger(__name__)

#    code begin

from django.conf.urls.defaults import patterns
from dashboard.urls import url
# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('dashboard.authorize_manage.views',
    url(r'^permit/$', 'authorize_permit', name='authorize_permit', method='post'),
    url(r'^permit/$', 'get_permit_view', name='get_permit_view', method='get'),
    url(r'^tips/$', 'show_permit_tips', name='show_permit_tips', method='get'),
    url(r'^login/$', 'authorize_login', name='authorize_login', method='post'),
    url(r'^logout/$', 'authorize_logout', name='authorize_logout', method='get'),
    url(r'^loginclientindex/$', 'get_login_client_view', name='get_login_client_view', method='get'),
    url(r'^loginclient/$', 'authorize_client_login', name='authorize_client_login', method='post'),
    url(r'^clientlogout/$', 'authorize_client_logout', name='authorize_client_logout', method='get'),
    url(r'^clientinstances$', 'get_client_instances', name='get_client_instances', method='get'),
)
