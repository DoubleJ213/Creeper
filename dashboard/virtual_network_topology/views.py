# Copyright 2013 Beixinyuan(Nanjing), All Rights Reserved.
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


from django import shortcuts
from django.utils import simplejson
from django.views.decorators.http import require_GET
from django.http import HttpResponse
from dashboard import api
from dashboard.exceptions import Unauthorized
from dashboard.utils import jsonutils
from django.core.urlresolvers import reverse


NETWORK_NAME_EMPTY_LENGTH = 0

@require_GET
def get_network_topology(request):
    """
    :param request:request object
    :return:view<'project_manage/index.html'>::list of tenants
    """
    return shortcuts.render(request, 'virtual_network_topology/networktopologyindex.html')

@require_GET
def get_network_topology_menu(request):
    """
    :param request:request object
    :return:view<'virtual_network_manage/networkprojectindex.html'>::list of tenants
    """
    project_menus = []
    try:
        projects = api.tenant_list(request, admin = True)
    except Unauthorized:
        raise
    except Exception , exe:
        LOG.error('Unable to retrieve project list,%s.' % exe.message)

    for project in projects:

        project_menu = {
            'project_name': project.name,
            'project_id': project.id,
            'project_enabled': project.enabled,
        }
        project_menus.append(project_menu)
    return HttpResponse(jsonutils.dumps(project_menus))

@require_GET
def networktopology_index(request):
    """
    :param request:request object
    :return:view<'virtual_network_manage/networktopology.html'>::index for edit a port
    """
    return shortcuts.render(request, 'virtual_network_topology/networktopology.html')

def add_resource_url( request,view, resources):
    tenant_id = request.user.tenant_id
    for resource in resources:
        if (resource.get('tenant_id')
            and tenant_id != resource.get('tenant_id')):
            continue
        resource['url'] = reverse(view, None, [str(resource['id'])])

def check_router_external_port( ports, router_id, network_id):
    for port in ports:
        if (port['network_id'] == network_id
            and port['device_id'] == router_id):
            return True
    return False

@require_GET
def get_networktopology_data(request):
    data = {}
    try:
        # Get nova data
        novaclient = api.nova.novaclient(request)
        servers = api.nova.server_list(request, all_tenants=True) #novaclient.servers.list()
        data['servers'] = [{'name': server.name,
                            'status': server.status,
                            'id': server.id} for server in servers]
        #    add_resource_url('horizon:project:instances:detail',
        #        data['servers'])
        # Get quantum data
        quantumclient = api.quantum.quantumclient(request)
        networks = quantumclient.list_networks()
        subnets = quantumclient.list_subnets()
        ports = quantumclient.list_ports()
        routers = quantumclient.list_routers()
        data['networks'] = sorted(networks.get('networks', []),
            key=lambda x: x.get('router:external'),
            reverse=True)
        #    add_resource_url('horizon:project:networks:detail',
        #        data['networks'])
        data['subnets'] = subnets.get('subnets', [])
        data['ports'] = ports.get('ports', [])
        #    add_resource_url('horizon:project:networks:ports:detail',
        #        data['ports'])
        data['routers'] = routers.get('routers', [])
        # user can't see port on external network. so we are
        # adding fake port based on router information
        for router in data['routers']:
            external_gateway_info = router.get('external_gateway_info')
            if not external_gateway_info:
                continue
            external_network = external_gateway_info.get(
                'network_id')
            if not external_network:
                continue
            if check_router_external_port(data['ports'],
                router['id'],
                external_network):
                continue

            fake_port = {'id': 'fake%s' % external_network,
                         'network_id': external_network,
                         'device_id': router['id'],
                         'fixed_ips': []}
            data['ports'].append(fake_port)
    except Unauthorized:
        raise
    #    add_resource_url('horizon:project:routers:detail',
    #        data['routers'])
    json_string = simplejson.dumps(data, ensure_ascii=False)
    return HttpResponse(json_string, mimetype='text/json')