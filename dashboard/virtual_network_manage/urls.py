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
__date__ = '2013-06-13'
__version__ = 'v2.0.9'

import logging

from dashboard.urls import url
from django.conf import settings
from django.conf.urls.defaults import patterns

#    code begin
if settings.DEBUG:
    __log__ = 'v2.0.9 create'

LOG = logging.getLogger(__name__)

urlpatterns = patterns('dashboard.virtual_network_manage.views',

    url(r'^network/projects$', 'get_network_projects',
        name='get_network_projects', method='get'),

    url(r'^network/projectsmenu$', 'get_network_projects_menu',
        name='get_network_projects_menu', method='get'),

    url(r'^network/tenants/(?P<tenant_id>[^/]+)/networks/', 'get_tenant_networks',
        name='get_tenant_networks', method='get'),

    url(r'^network/tenants/(?P<tenant_id>[^/]+)/createnetwork/(?P<networkortopology>[^/]+)/', 'create_network_index',
        name='create_network_index', method='get'),

    url(r'^network/tenants/(?P<tenant_id>[^/]+)/createnetworkaction/', 'create_network_action',
        name='create_network_action', method='post'),

    url(r'^network/tenants/(?P<tenant_id>[^/]+)/createnetworkactiontopology/', 'create_network_action_topology',
        name='create_network_action_topology', method='post'),

    url(r'^network/tenants/(?P<tenant_id>[^/]+)/networks/(?P<network_id>[^/]+)/deletenetworkaction/$', 'delete_network_action',
        name='delete_network_action', method='delete'),

    url(r'^network/(?P<network_id>[^/]+)/tenants/(?P<tenant_id>[^/]+)/getnetworkinfo/$', 'get_network_info',
        name='get_network_info', method='get'),

    url(r'^network/(?P<network_id>[^/]+)/tenants/(?P<tenant_id>[^/]+)/editnetwork/$', 'edit_network_index',
        name='edit_network_index', method='get'),

    url(r'^network/tenants/(?P<tenant_id>[^/]+)/networks/(?P<network_id>[^/]+)/editnetworkaction/$', 'edit_network_action',
        name='edit_network_action', method='post'),

    url(r'^network/subnets/(?P<subnet_id>[^/]+)/getsubnetinfo/$', 'get_subnet_info',
        name='get_subnet_info', method='get'),

    url(r'^network/(?P<network_id>[^/]+)/createsubnet/', 'create_subnet_index',
        name='create_subnet_index', method='get'),

    url(r'^network/(?P<network_id>[^/]+)/createsubnetaction/', 'create_subnet_action',
        name='create_subnet_action', method='post'),

    url(r'^network/subnets/(?P<subnet_id>[^/]+)/editsubnet/$', 'edit_subnet_index',
        name='edit_subnet_index', method='get'),

    url(r'^network/subnets/(?P<subnet_id>[^/]+)/editsubnetaction/$', 'edit_subnet_action',
        name='edit_subnet_action', method='post'),

    url(r'^network/subnets/(?P<subnet_id>[^/]+)/deletesubnetaction/$', 'delete_subnet_action',
        name='delete_subnet_action', method='delete'),

    url(r'^network/ports/(?P<port_id>[^/]+)/getportinfo/$', 'get_port_info',
        name='get_port_info', method='get'),

    url(r'^network/(?P<network_id>[^/]+)/createport/', 'create_port_index',
        name='create_port_index', method='get'),

    url(r'^network/(?P<network_id>[^/]+)/createportaction/', 'create_port_action',
        name='create_port_action', method='post'),

    url(r'^network/ports/(?P<port_id>[^/]+)/editport/$', 'edit_port_index',
        name='edit_port_index', method='get'),

    url(r'^network/ports/(?P<port_id>[^/]+)/editportaction/$', 'edit_port_action',
        name='edit_port_action', method='post'),

    url(r'^network/ports/(?P<port_id>[^/]+)/deleteportaction/$', 'delete_port_action',
        name='delete_port_action', method='delete'),

)
