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

from django.conf import settings

if settings.DEBUG:
    __log__ = 'v2.0.9 create'

import logging

LOG = logging.getLogger(__name__)

#    code begin

from django.conf.urls.defaults import patterns
from dashboard.urls import url

urlpatterns = patterns('dashboard.virtual_router_manage.views',

    url(r'^routers$',
        'get_routers_projects', name='get_routers_projects', method='get'),

    url(r'^routers/routersmenu$',
        'get_routers_projects_menu', name='get_routers_projects_menu', method='get'),

    url(r'^routers/tenants/(?P<tenant_id>[^/]+)/projects/$',
        'get_routers_projects_list', name='get_routers_projects_list',method='get'),

    url(r'^routers/(?P<router_project_id>[^/]+)/tenants/(?P<tenant_id>[^/]+)/getRouterProjectInfo/$',
        'get_routerprojectinfo', name='get_routerprojectinfo', method='get'),

    url(r'^routers/(?P<routerproject_id>[^/]+)/deleteprojectaction/$',
        'delete_routerproject_action', name='delete_routerproject_action', method='delete'),

    url(r'^routers/(?P<routerproject_id>[^/]+)/tenants/(?P<tenant_id>[^/]+)/createRouterProjectDetail/$',
        'create_routerprojectdetail', name='create_routerprojectdetail', method='get'),

    url(r'^routers/(?P<routerproject_id>[^/]+)/interfaces/(?P<interface_id>[^/]+)/deleteRouterIFaction/$',
        'delete_routerif_action', name='delete_routerif_action', method='delete'),

    url(r'^routers/(?P<router_id>[^/]+)/createinterfaceaction/',
        'create_interface_action',  name='create_interface_action', method='post'),

    url(r'^routers/(?P<router_id>[^/]+)/createGatewayDetail/$',
        'create_gateway_detail', name='create_gateway_detail', method='get'),

    url(r'^routers/(?P<router_id>[^/]+)/createGatewayAction/$',
        'create_gateway_action', name='create_gateway_action',  method='post'),

    url(r'^routers/(?P<router_id>[^/]+)/delete_gateway_action/$',
        'delete_gateway_action', name='delete_gateway_action', method='delete'),

    url(r'^routers/tenants/(?P<tenant_id>[^/]+)/createRouterDetail/(?P<routerortopology>[^/]+)$',
        'create_router_detail', name='create_router_detail', method='get'),

    url(r'^routers/tenants/(?P<tenant_id>[^/]+)/createRouterAction/$',
        'create_router_action', name='create_router_action', method='post'),

    url(r'^routers/tenants/(?P<tenant_id>[^/]+)/createRouterActionTopology/$',
        'create_router_action_topology', name='create_router_action_topology',  method='post'),

)
