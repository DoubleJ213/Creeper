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


__author__ = 'zhaolei'
__date__ = '2013-06-20'
__version__ = 'v2.0.9'

from django.conf import settings
if settings.DEBUG:
    __log__ = 'v2.0.9 create'

import logging
LOG = logging.getLogger(__name__)

#    code begin

from django.conf.urls.defaults import patterns
from dashboard.urls import url

urlpatterns = patterns('dashboard.virtual_keypairs_manage.views',
    url(r'^keypairs/keypairlist/$', 'get_project_keypairs_list', name='get_project_keypairs_list', method='get'),
    url(r'^keypairs/createkeypair/$', 'create_keypair_index', name='create_keypair_index', method='get'),
    url(r'^keypairs/keypaircreateaction/$', 'create_keypair_action', name='create_keypair_action', method='post'),
    url(r'^keypairs/importkeypair/$', 'import_keypair_index', name='import_keypair_index', method='get'),
    url(r'^keypairs/importkeypairaction/$', 'import_keypair_action', name='import_keypair_action', method='post'),
    url(r'^keypairs/(?P<keypair_name>[^/]+)/downloadindex/$', 'download_keypair_index', name='download_keypair_index', method='get'),
    url(r'^keypairs/(?P<keypair_name>[^/]+)/download/$', 'create_keypair_download', name='create_keypair_download', method='get'),
    url(r'^keypairs/(?P<keypair_name>[^/]+)/deleteindex/$', 'delete_keypair_form', name='delete_keypair_form', method='get'),
    url(r'^keypairs/(?P<keypair_name>[^/]+)/deleteaction$', 'delete_keypair_action', name='delete_keypair_action', method='delete'),
)
