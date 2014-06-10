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
__date__ = '2013-03-02'
__version__ = 'v2.0.1'

import logging

from django.conf import settings
from django.core.urlresolvers import reverse

from dashboard import api
from dashboard.api import server_list
from dashboard.authorize_manage.utils import switch_tenants
from dashboard.exceptions import Unauthorized

if settings.DEBUG:
    __log__ = 'v2.0.1 create , common function for instance_manage'

LOG = logging.getLogger(__name__)

def get_instances(request):
    instances = []
    try:
        instances = api.nova.server_list(request, all_tenants=True)
    except Unauthorized:
        raise
    except Exception, e:
        LOG.error('The method get_instances raise exception:%s' % e)
    return instances

def get_instance_simple_express(instance, host_uuid):
    id = getattr(instance,'id','unknown')
    return ({'id':id,
             'name':getattr(instance,'name','unknown'),
             'pid':host_uuid,
             'status':getattr(instance,'status','unknown'),
             'type':'compute',
             'link':reverse('get_instance_monitor_page',args=[id]),
             'status_link':reverse('get_instance_status',args=[id]),
             })

def get_instance_simple_express_tenant(instance, tenant_id):
    id = getattr(instance,'id','unknown')
    return ({'id':id,
             'name':getattr(instance,'name','unknown'),
             'status':getattr(instance,'status','unknown'),
             'type':'compute',
             'link':reverse('get_instance_detail_with_tenant_switch',args=[tenant_id, id]),
             })

def get_instances_simple_express(instances, tenant_id):
    host_tree = []
    for instance in instances:
        host_tree.append(get_instance_simple_express_tenant(instance, tenant_id))
    return host_tree

def get_authorized_instances(request, tenant_id):
    instances = None
    if switch_tenants(request, tenant_id):
        instances = server_list(request)
    return instances

#def switch_tenant(request, tenant_id):
#    if request.user.tenant_id != tenant_id:
#        return switch_tenants(request,tenant_id)
#    else:
#        return True

UMASK_USB = 1
UMASK_AUDIO = 2

UMASK_MAP = {'USB': UMASK_USB,
             'AUDIO': UMASK_AUDIO}

def get_mask(value):
    mask = {}
    for k, v in UMASK_MAP.items():
        mask[k] =  bool(v & value)
    return mask
