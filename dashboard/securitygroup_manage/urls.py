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


__author__ = 'zhao lei'
__date__ = '2013-03-14'
__version__ = 'v2.0.1'

import logging

from django.conf import settings
from django.conf.urls.defaults import patterns
from dashboard.urls import url

if settings.DEBUG:
    __log__ = 'v2.0.1 create'



LOG = logging.getLogger(__name__)

#    code begin
urlpatterns = patterns('dashboard.securitygroup_manage.views',
    url(r'^securitygroup/projects$', 'get_securitygroup_projects',
        name='get_securitygroup_projects', method='get'),

    url(r'^securitygroup/(?P<security_group_id>[^/]+)/editgrouprules/$',
        'edit_securitygrouprules', name='edit_securitygrouprules', method='get'),

    url(r'^securitygroup/tenants/(?P<tenant_id>[^/]+)/groups/$',
        'get_securitygroup_list', name='get_securitygroup_list',  method='get'),

    url(r'^securitygroup/tenants/(?P<tenant_id>[^/]+)/creategroup/$',
        'create_securitygroup_index', name='create_securitygroup_index', method='get'),

    url(r'^securitygroup/tenants/(?P<tenant_id>[^/]+)/creategroupaction/$',
        'create_securitygroup_action', name='create_securitygroup_action', method='post'),

    url(r'^securitygroup/(?P<security_group_id>[^/]+)/deletegroupindex/$',
        'delete_securitygroup_index', name='delete_securitygroup_index', method='get'),

    url(r'^securitygroup/(?P<security_group_id>[^/]+)/deletegroupaction/$',
        'delete_securitygroup_action', name='delete_securitygroup_action', method='delete'),

    url(r'^securitygroup/(?P<security_group_id>[^/]+)/tenants/(?P<tenant_id>[^/]+)/getsecuritygroupinfo/$',
        'get_securitygroup_info', name='get_securitygroup_info', method='get'),

    url(r'^securitygroup/(?P<security_group_id>[^/]+)/tenants/(?P<tenant_id>[^/]+)/creategrouprulesindex/$',
        'create_securitygrouprules_index', name='create_securitygrouprules_index', method='get'),

    url(r'^securitygroup/(?P<security_group_id>[^/]+)/rule/(?P<rule_id>[^/]+)/deletegrouprulesindex/$',
        'delete_securitygrouprules_index', name='delete_securitygrouprules_index', method='get'),

    url(r'^securitygroup/(?P<security_group_id>[^/]+)/creategrouprulesaction/$',
        'create_securitygrouprules_action', name='create_securitygrouprules_action', method='post'),

    url(r'^securitygroup/(?P<security_group_id>[^/]+)/rule/(?P<rule_id>[^/]+)/deletegrouprulesaction/$',
        'delete_securitygrouprules_action', name='delete_securitygrouprules_action', method='delete'),

    url(r'^securitygroup/projectsmenu$',
        'get_securitygroup_projects_menu', name='get_securitygroup_projects_menu', method='get'),
)
