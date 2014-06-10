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


__author__ = 'shichong'
__date__ = '2013-07-19'
__version__ = 'v2.0.9'

from django.conf import settings
if settings.DEBUG:
    __log__ = 'v2.0.9 create'

import logging
LOG = logging.getLogger(__name__)

#    code begin

from django.conf.urls.defaults import patterns
from dashboard.urls import url

urlpatterns = patterns('dashboard.virtual_network_topology.views',
    url(r'^networktopology$', 'get_network_topology', name='get_network_topology', method='get'),
    url(r'^networktopology/menu$', 'get_network_topology_menu', name='get_network_topology_menu', method='get'),
    url(r'^network/networktopologyindex/$', 'networktopology_index', name='networktopology_index', method='get'),
    url(r'^network/getnetworktopologydata/$', 'get_networktopology_data', name='get_networktopology_data', method='get'),

)
