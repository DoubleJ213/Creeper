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


__author__ = 'lishiquan'
__date__ = '2013-06-08'
__version__ = 'v2.0.9'

from django.conf import settings
if settings.DEBUG:
    __log__ = 'v2.0.9 create'

import logging
LOG = logging.getLogger(__name__)

#    code begin

from django.conf.urls.defaults import patterns
from dashboard.urls import url

urlpatterns = patterns('dashboard.virtual_address_manage.views',

    url(r'^virtualaddress/tenants/(?P<tenant_id>[^/]+)/floatingips/$',
        'get_floating_ips_list', name='get_floating_ips_list', method='get'),

    url(r'^virtualaddress/groupslist/$',
        'get_floating_ips_address', name='get_floating_ips_address', method='get'),

    url(r'^virtualaddress/groupslistips/$',
        'get_securitygroup_ips_list', name='get_securitygroup_ips_list', method='get'),

    url(r'^virtualaddress/tenants/(?P<tenant_id>[^/]+)/allocateip/$',
        'allocate_ip_index', name='allocate_ip_index', method='get'),

    url(r'^virtualaddress/tenants/(?P<tenant_id>[^/]+)/allocateipaction/$',
        'allocate_ip_action', name='allocate_ip_action', method='post'),

    url(r'^virtualaddress/(?P<ip_id>[^/]+)/releaseip/$',
        'release_ip_index', name='release_ip_index', method='get'),

    url(r'^virtualaddress/(?P<ip_id>[^/]+)/releaseipaction/$',
        'release_ip_action', name='release_ip_action', method='delete'),

    url(r'^virtualaddress/(?P<ip_id>[^/]+)/associateip/$',
        'associate_ip_index', name='associate_ip_index', method='get'),

    url(r'^virtualaddress/(?P<ip_id>[^/]+)/associateipaction/$',
        'associate_ip_action', name='associate_ip_action', method='post'),

    url(r'^virtualaddress/(?P<ip_id>[^/]+)/instance/(?P<instance_id>[^/]+)/disassociateip/$',
        'disassociate_ip_index', name='disassociate_ip_index', method='get'),

    url(r'^virtualaddress/(?P<ip_id>[^/]+)/instance/(?P<instance_id>[^/]+)/disassociateaction/$',
        'disassociate_ip_action', name='disassociate_ip_action', method='post'),

    url(r'^virtualaddress/tenants/(?P<tenant_id>[^/]+)/(?P<floating_ip>[^/]+)/floatingipsodd/$',
        'get_floating_ips_odd', name='get_floating_ips_odd', method='get'),

    url(r'^virtualaddress/floatingipinfo/$',
        'get_floatingip_count_info', name='get_floatingip_count_info', method='get'),

    url(r'^virtualaddress/releasefips/$',
        'release_fips', name='release_fips', method='delete'),
)
