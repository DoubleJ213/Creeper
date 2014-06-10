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
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.http import HttpResponse

from dashboard import api
from dashboard.authorize_manage.utils import switch_tenants
from dashboard.exceptions import Unauthorized
from dashboard.exceptions import LicenseForbidden
from dashboard.utils import jsonutils, ui_response, UIResponse, Pagenation
from dashboard.utils.ui import UI_RESPONSE_DWZ_ERROR, UI_RESPONSE_DWZ_SUCCESS, UI_RESPONSE_ERROR
from dashboard.utils.i18n import get_text
from dashboard.utils.ui import check_permission
from .forms import CreateNetwork, UpdateNetwork, CreateSubnet, CreatePort, UpdatePort,UpdateSubnet

NETWORK_NAME_EMPTY_LENGTH = 0

@require_GET
def get_network_projects(request):
    """
    :param request:request object
    :return:view<'project_manage/index.html'>::list of tenants
    """
    return shortcuts.render(request, 'virtual_network_manage/networkprojectindex.html')

@require_GET
def get_network_projects_menu(request):
    """
    :param request:request object
    :return:view<'virtual_network_manage/networkprojectindex.html'>::list of tenants
    """
    project_menus = []
    projects = []
    try:
        projects = api.tenant_list(request, admin = True)
    except Unauthorized:
        raise
    except Exception , exe:
        LOG.error('Unable to retrieve project list,%s.' % exe.message)
    for project in projects:
        networks = []
        if project.enabled:
            try:
                networklist = api.quantum.network_list_for_tenant(request, project.id)
            except Unauthorized:
                raise
            if networklist:
                for network in networklist:
                    network_obj = {'network_name':network.name,
                                   'network_id':network.id,
                                   'network_tenant':network.tenant_id == project.id
                    }
                    networks.append(network_obj)

        project_menu = {
            'project_name': project.name,
            'project_id': project.id,
            'project_enabled': project.enabled,
            'project_network': networks
        }
        project_menus.append(project_menu)
    return HttpResponse(jsonutils.dumps(project_menus))


@require_GET
@Pagenation('virtual_network_manage/network_list.html')
def get_tenant_networks(request, tenant_id):
    """
    :param request:request object, tenant_id
    :return:view<'virtual_network_manage/network_list.html'>::list of networks
    """
    args = {}
    networklist = []
    tenant_choices = []
    try:
        networklist = api.quantum.network_list_for_tenant(request, tenant_id)
        tenants = api.tenant_list_not_filter(request, admin = True)
        for tenant in tenants:
            tenant_choices.append((tenant.id, tenant.name))
    except Unauthorized:
        raise
    except Exception , exe:
        LOG.error('Unable to retrieve network list.Error:%s' % exe.message)

    args['list'] = []
    args['networklist'] = networklist
    args['tenants'] = tenant_choices
    args['tenant_id'] = tenant_id

    return args


@require_GET
def create_network_index(request, tenant_id, networkortopology):
    """
    :param request:request object, tenant_id
    :return:view<'virtual_network_manage/network_create.html'>::create index of network
    """
    form = CreateNetwork(request,tenant_id)
    return shortcuts.render(request, 'virtual_network_manage/network_create.html',
                            {'form': form, 'tenant_id':tenant_id, 'gotoflag' : networkortopology})

@check_permission('Create Network')
@require_POST
@UIResponse('Virtual NetWork Manage', 'get_network_projects')
def create_network_action(request, tenant_id):
    """
    :param request:request object, tenant_id
    :return:view<'virtual_network_manage/networkprojectindex.html'>::create action of network
    """
    form =  CreateNetwork(request,tenant_id , request.POST)
    if form.is_valid():
        data = form.cleaned_data
        switch_tenants(request, tenant_id)
        try:
            params = {'name': data['name'],
                      'tenant_id': data['tenant_id'],
                      'admin_state_up': data['admin_state'],
                      'shared': data['shared'],
                      'router:external': data['external']}
            api.quantum.network_create(request, **params)
        except Unauthorized:
            raise
        except LicenseForbidden:
            raise
        except Exception , exe:
            msg = 'Failed to create network'
            LOG.error("Failed to create network,the error is %s" % exe.message)
            return HttpResponse({"message":msg, "statusCode":UI_RESPONSE_DWZ_ERROR}, status = UI_RESPONSE_ERROR)

        return HttpResponse({"message" : "Create network successfully!",
                             "statusCode" : UI_RESPONSE_DWZ_SUCCESS ,
                             "object_name" : data['name']}, status = UI_RESPONSE_DWZ_SUCCESS)
    else:
        return HttpResponse({"form":form, "message":"", "statusCode":UI_RESPONSE_DWZ_ERROR}, status = UI_RESPONSE_ERROR)


@require_POST
@UIResponse('Virtual NetWork Topology', 'get_network_topology')
def create_network_action_topology(request, tenant_id):
    """
    :param request:request object, tenant_id
    :return:view<'virtual_network_manage/networkprojectindex.html'>::create action of network
    """
    form =  CreateNetwork(request,tenant_id , request.POST)
    if form.is_valid():
        data = form.cleaned_data
        switch_tenants(request, tenant_id)
        try:
            params = {'name': data['name'],
                      'tenant_id': data['tenant_id'],
                      'admin_state_up': data['admin_state'],
                      'shared': data['shared'],
                      'router:external': data['external']}
            api.quantum.network_create(request, **params)
        except Unauthorized:
            raise
        except Exception , exe:
            msg = 'Failed to create network'
            LOG.error("Failed to create network,the error is %s" % exe.message)
            return HttpResponse({"message":msg, "statusCode":UI_RESPONSE_DWZ_ERROR}, status = UI_RESPONSE_ERROR)
        return HttpResponse({"message":"Create network successfully!",
                             "statusCode":UI_RESPONSE_DWZ_SUCCESS ,
                             "object_name":data['name']}, status = UI_RESPONSE_DWZ_SUCCESS)
    else:
        return HttpResponse({"form":form, "message":"", "statusCode":UI_RESPONSE_DWZ_ERROR}, status = UI_RESPONSE_ERROR)


@check_permission('Delete NetWork')
@require_http_methods(['DELETE'])
@UIResponse('Virtual NetWork Manage', 'get_network_projects')
def delete_network_action(request, tenant_id, network_id):
    """
    :param request:request object, tenant_id, network_id
    :return:view<'virtual_network_manage/networkprojectindex.html'>::delete action of network
    """
    try:
        switch_tenants(request, tenant_id)
        network = api.quantum.network_get(request, network_id)
        api.quantum.network_delete(request, network_id)
    except Unauthorized:
        raise
    except Exception , exe:
        if exe.message.find('There are one or more ports still in use on the network') != -1:
            msg = get_text('Error! There are one or more ports still in use on the network.')
        else:
            msg = 'Unable to delete network.'
        LOG.error('Unable to delete network,the error is %s' % exe.message)
        return HttpResponse({ "message":msg, "statusCode":UI_RESPONSE_DWZ_ERROR }, status = UI_RESPONSE_ERROR)

    return HttpResponse({"message":"delete network successfully!",
                         "statusCode":UI_RESPONSE_DWZ_SUCCESS ,
                         "object_name":getattr(network, 'name', 'unknown')}, status = UI_RESPONSE_DWZ_SUCCESS)

@require_GET
def get_network_info(request, tenant_id, network_id):
    """
    :param request:request object, tenant_id, network_id
    :return:view<'virtual_network_manage/networkinfo.html'>::get a network info
    """
    try:
        switch_tenants(request, tenant_id)
        network = api.quantum.network_get(request, network_id)
        network.set_id_as_name_if_empty(length = NETWORK_NAME_EMPTY_LENGTH)

        ports = api.quantum.port_list(request, network_id = network_id)

        for p in ports:
            p.set_id_as_name_if_empty()

        subnets = api.quantum.subnet_list(request,
             network_id = network.id)

        for s in subnets:
            s.set_id_as_name_if_empty()

        tenant_choices = []
        tenants = api.tenant_list_not_filter(request, admin = True)
        for tenant in tenants:
            tenant_choices.append((tenant.id, tenant.name))

        return shortcuts.render(request, 'virtual_network_manage/networkinfo.html', {'network': network, 'subnets':subnets, "ports":ports, "tenants":tenant_choices})
    except Unauthorized:
        raise
    except Exception , exe:
        msg = 'get network info error.'
        LOG.error('get network info error,the error is %s' % exe.message)
        return HttpResponse(jsonutils.dumps(ui_response(message = msg)))

@require_GET
def edit_network_index(request, tenant_id, network_id):
    """
    :param request:request object, tenant_id, network_id
    :return:view<'virtual_network_manage/network_edit.html'>::index edit a network info
    """
    form = UpdateNetwork(request, tenant_id,network_id)
    try:
        network = api.quantum.network_get(request, network_id)
    except Unauthorized:
        raise
    except Exception , exe:
        LOG.error('get network info error,the error is %s' % exe.message)
    return shortcuts.render(request, 'virtual_network_manage/network_edit.html', {'form': form,
                                                                                  'network':network,
                                                                                  'tenant_id': tenant_id,
                                                                                  'network_id': network_id})
@check_permission('Edit NetWork')
@require_POST
@UIResponse('Virtual NetWork Manage', 'get_network_projects')
def edit_network_action(request, tenant_id, network_id):
    """
    :param request:request object, tenant_id, network_id
    :return:view<'virtual_network_manage/networkprojectindex.html'>::edit actin for a network info
    """
    form = UpdateNetwork(request, tenant_id,network_id,request.POST)
    if form.is_valid():
        data = form.cleaned_data
        switch_tenants(request, tenant_id)
        try:
            params = {'name': data['name'],
                      'admin_state_up': data['admin_state'],
                      'shared': data['shared'],
                      'router:external': data['external']}
            api.quantum.network_modify(request, network_id,
                **params)
        except Unauthorized:
            raise
        except Exception , exe:
            msg = 'Failed to Update network'
            LOG.error("Failed to Update network,the error is %s" % exe.message)
            return HttpResponse({"message":msg, "statusCode":UI_RESPONSE_DWZ_ERROR}, status = UI_RESPONSE_ERROR)
        msg = get_text('Update network successfully!')

        return HttpResponse({"message":msg,
                             "statusCode":UI_RESPONSE_DWZ_SUCCESS ,
                             "object_name":data['name']}, status = UI_RESPONSE_DWZ_SUCCESS)
    else:
        return HttpResponse({"form":form, "message":"", "statusCode":UI_RESPONSE_DWZ_ERROR}, status = UI_RESPONSE_ERROR)

@require_GET
def get_subnet_info(request, subnet_id):
    """
    :param request:request object, network_id
    :return:view<'virtual_network_manage/subnetinfo.html'>::get a subnet info
    """
    try:
        subnet = api.quantum.subnet_get(request, subnet_id)
        network = api.quantum.network_get(request, subnet.network_id)

        return shortcuts.render(request, 'virtual_network_manage/subnetinfo.html', {'network': network, 'subnet':subnet})
    except Unauthorized:
        raise
    except Exception , exe:
        msg = 'get subnet info error.'
        LOG.error('get subnet and network info error,the error is %s' % exe.message)
        return HttpResponse(jsonutils.dumps(ui_response(message = msg)))
@require_GET
def create_subnet_index(request, network_id):
    """
    :param request:request object, network_id
    :return:view<'virtual_network_manage/subnet_create.html'>::index for create subnet
    """
    form = CreateSubnet(request, network_id)
    network = None
    try:
        network = api.quantum.network_get(request, network_id)
    except Unauthorized:
        raise
    except Exception , exe:
        LOG.error('get network info error,the error is %s' % exe.message)
    return shortcuts.render(request, 'virtual_network_manage/subnet_create.html', {'form': form, 'network':network})

def setup_subnet_parameters(params, data, is_create = True):
    """Setup subnet parameters

    This methods setups subnet parameters which are available
    in both create and update.
    """
    is_update = not is_create
    params['enable_dhcp'] = data['enable_dhcp']
    if is_create and data['allocation_pools']:
        pools = [dict(zip(['start', 'end'], pool.strip().split(',')))
                 for pool in data['allocation_pools'].split('\n')
                 if pool.strip()]
        params['allocation_pools'] = pools
    if data['host_routes'] or is_update:
        routes = [dict(zip(['destination', 'nexthop'],
            route.strip().split(',')))
                  for route in data['host_routes'].split('\n')
                  if route.strip()]
        params['host_routes'] = routes
    if data['dns_nameservers'] or is_update:
        nameservers = [ns.strip()
                       for ns in data['dns_nameservers'].split('\n')
                       if ns.strip()]
        params['dns_nameservers'] = nameservers

@check_permission('Create Subnet')
@require_POST
@UIResponse('Virtual NetWork Manage', 'get_network_projects')
def create_subnet_action(request, network_id):
    """
    :param request:request object, network_id
    :return:view<'virtual_network_manage/networkprojectindex.html'>::action for create subnet
    """

    form = CreateSubnet(request, network_id,request.POST)
    if form.is_valid():
        data = form.cleaned_data
        network = None
        try:
            network = api.quantum.network_get(request, network_id)
        except Unauthorized:
            raise
        except Exception as exe:
            LOG.error('Failed to get network,the error is %s' % exe.message)
        if network:
            network_id = network.id
        else:
            network_id = network_id
        try:
            params = {'network_id': network_id,
                      'name': data['subnet_name'],
                      'cidr': data['cidr'],
                      'ip_version': int(data['ip_version'])}
            if network.tenant_id:
                params['tenant_id'] = network.tenant_id
            if data['no_gateway']:
                params['gateway_ip'] = None
            elif data['gateway_ip']:
                params['gateway_ip'] = data['gateway_ip']

            setup_subnet_parameters(params, data)

            api.quantum.subnet_create(request, **params)
        except Unauthorized:
            raise
        except LicenseForbidden:
            raise
        except Exception as exe:
            if exe.message.find('overlaps with another subnet') != -1:
                msg = ('Failed! Overlaps with another subnet.')
            else:
                msg = ('Failed to create subnet')
            LOG.error('Failed to create subnet,the error is %s' % exe.message)
            return HttpResponse(jsonutils.dumps(ui_response(message = msg)))

        return HttpResponse({"message" : "Create subnet successfully!",
                             "statusCode" : UI_RESPONSE_DWZ_SUCCESS ,
                             "object_name" : data['subnet_name']}, status = UI_RESPONSE_DWZ_SUCCESS)
    else:
        return HttpResponse({"form" : form, "message" : "", "statusCode" : UI_RESPONSE_DWZ_ERROR }, status = UI_RESPONSE_ERROR)

@require_GET
def edit_subnet_index(request, subnet_id):
    """
    :param request:request object, subnet_id
    :return:view<'virtual_network_manage/subnet_edit.html'>::index for edit subnet
    """

    form = UpdateSubnet(request, subnet_id)
    subnet = None
    routes = []
    network = None
    try:
        subnet = api.quantum.subnet_get(request, subnet_id)
        routes = ['%s,%s' % (r['destination'], r['nexthop'])
                  for r in subnet['host_routes']]
        network = api.quantum.network_get(request, subnet.network_id)
    except Unauthorized:
        raise
    except Exception , exe:
        LOG.error('get subnet and network info error,the error is %s' % exe.message)
    return shortcuts.render(request, 'virtual_network_manage/subnet_edit.html',
        {'form': form,
         'network':network,
         'subnet': subnet,
         "host_routes":'\n'.join(routes),
         "dns_nameservers":'\n'.join(subnet['dns_nameservers'])})

@check_permission('Edit Subnet')
@require_POST
@UIResponse('Virtual NetWork Manage', 'get_network_projects')
def edit_subnet_action(request, subnet_id):
    """
    :param request:request object, subnet_id
    :return:view<'virtual_network_manage/networkprojectindex.html'>::action for edit subnet
    """
    form =  UpdateSubnet(request, subnet_id, request.POST)
    if form.is_valid():
        data = form.cleaned_data
        params = {}
        try:
            params['name'] = data['subnet_name']
            if data['no_gateway']:
                params['gateway_ip'] = None
            elif data['gateway_ip']:
                params['gateway_ip'] = data['gateway_ip']

            setup_subnet_parameters(params, data, is_create = False)

            api.quantum.subnet_modify(request, subnet_id, **params)
        except Unauthorized:
            raise
        except Exception as exe:
            msg = ('Failed to edit subnet: %s' % data['subnet_name'])
            LOG.error('Failed to edit subnet,the error is %s' % exe.message)
            return HttpResponse(jsonutils.dumps(ui_response(message = msg)))

        return HttpResponse({"message":"Edit subnet successfully!", "statusCode":UI_RESPONSE_DWZ_SUCCESS , "object_name":data['subnet_name']}, status = UI_RESPONSE_DWZ_SUCCESS)
    else:
        return HttpResponse({"form":form, "message":"", "statusCode":UI_RESPONSE_DWZ_ERROR}, status = UI_RESPONSE_ERROR)

@check_permission('Delete Subnet')
@require_http_methods(['DELETE'])
@UIResponse('Virtual NetWork Manage', 'get_network_projects')
def delete_subnet_action(request, subnet_id):
    """
    :param request:request object, subnet_id
    :return:view<'virtual_network_manage/networkprojectindex.html'>::action for delete subnet
    """
    try:
        subnet = api.quantum.subnet_get(request, subnet_id)
        api.quantum.subnet_delete(request, subnet_id)
    except Unauthorized:
        raise
    except Exception as exe:
        if exe.message.find('One or more ports have an IP allocation from this subnet.') != -1:
            msg = get_text('Error! One or more ports have an IP allocation from this subnet.')
        else:

            msg = 'Unable to delete subnet.'
        LOG.error('Unable to delete subnet,the error is %s' % exe.message)

        return HttpResponse({ "message":msg, "statusCode":UI_RESPONSE_DWZ_ERROR }, status = UI_RESPONSE_ERROR)
    LOG.info('delete subnet successfully!')
    return HttpResponse({"message":"delete subnet successfully!", "statusCode":UI_RESPONSE_DWZ_SUCCESS , "object_name":getattr(subnet, 'name', 'unknown')}, status = UI_RESPONSE_DWZ_SUCCESS)

@require_GET
def get_port_info(request, port_id):
    """
    :param request:request object, port_id
    :return:view<'virtual_network_manage/portinfo.html'>::get a port info
    """
    tenant_choices = []
    try:
        port = api.quantum.port_get(request, port_id)
        network = api.quantum.network_get(request, port.network_id)
        tenants = api.tenant_list_not_filter(request, admin = True)
        for tenant in tenants:
            tenant_choices.append((tenant.id, tenant.name))

        return shortcuts.render(request, 'virtual_network_manage/portinfo.html', {'network': network,
                                                                                  'port' : port,
                                                                                  'tenants' : tenant_choices})
    except Unauthorized:
        raise
    except Exception, exe:
        msg = 'get port info error.'
        LOG.error('get port info error,the error is %s' % exe.message)
        return HttpResponse(jsonutils.dumps(ui_response(message = msg)))


@require_GET
def create_port_index(request, network_id):
    """
    :param request:request object, network_id
    :return:view<'virtual_network_manage/port_create.html'>::index for create a port
    """
    form = CreatePort()
    network = None
    try:
        network = api.quantum.network_get(request, network_id)
    except Unauthorized:
        raise
    except Exception, exe:
        LOG.error('get network info error,the error is %s' % exe.message)
    return shortcuts.render(request, 'virtual_network_manage/port_create.html', {'form': form, 'network':network})


@require_POST
@UIResponse('Virtual NetWork Manage', 'get_network_projects')
def create_port_action(request, network_id):
    """
    :param request:request object, network_id
    :return:view<'virtual_network_manage/networkprojectindex.html'>::action for create a port
    """
    form = CreatePort(request.POST)
    if form.is_valid():
        data = form.cleaned_data
        try:
            network = api.quantum.network_get(request, network_id)
            data['tenant_id'] = network.tenant_id
            data['admin_state_up'] = data['admin_state']
            del data['admin_state']

            api.quantum.port_create(request, **data)
        except Unauthorized:
            raise
        except Exception as exe:
            msg = get_text('Failed to create a port for network %s')\
                  % data['network_name']
            LOG.error('Failed to create port,the error is %s' % exe.message)
            return HttpResponse(jsonutils.dumps(ui_response(message = msg)))

        return HttpResponse({"message" : "Create port successfully!",
                             "statusCode" : UI_RESPONSE_DWZ_SUCCESS ,
                             "object_name" : data['name']}, status = UI_RESPONSE_DWZ_SUCCESS)
    else:
        return HttpResponse({"form":form,
                             "message":"",
                             "statusCode":UI_RESPONSE_DWZ_ERROR }, status = UI_RESPONSE_ERROR)

@require_GET
def edit_port_index(request, port_id):
    """
    :param request:request object, port_id
    :return:view<'virtual_network_manage/port_edit.html'>::index for edit a port
    """
    form = UpdatePort()
    port = None
    try:
        port = api.quantum.port_get(request, port_id)
    except Unauthorized:
        raise
    except Exception, exe:
        LOG.error('get port info error,the error is %s' % exe.message)
    return shortcuts.render(request, 'virtual_network_manage/port_edit.html', {'form': form, 'port':port})

@check_permission('Edit Port')
@require_POST
@UIResponse('Virtual NetWork Manage', 'get_network_projects')
def edit_port_action(request, port_id):
    """
    :param request:request object, port_id
    :return:view<'virtual_network_manage/networkprojectindex.html'>::action for edit a port
    """
    form = UpdatePort(request.POST)
    if form.is_valid():
        data = form.cleaned_data
        try:
            api.quantum.port_modify(request, port_id,
            name = data['name'],
            admin_state_up = data['admin_state'],
            device_id = data['device_id'],
            device_owner = data['device_owner'])
        except Unauthorized:
            raise
        except Exception as exe:
            msg = ('Failed to edit port %s' % data['name'])
            LOG.error('Failed to edit port,the error is %s' % exe.message)
            return HttpResponse(jsonutils.dumps(ui_response(message = msg)))

        return HttpResponse({"message":"Edit port successfully!",
                             "statusCode":UI_RESPONSE_DWZ_SUCCESS ,
                             "object_name":data['name']}, status = UI_RESPONSE_DWZ_SUCCESS)
    else:
        return HttpResponse({"form" : form,
                             "message" : "",
                             "statusCode" : UI_RESPONSE_DWZ_ERROR}, status = UI_RESPONSE_ERROR)

@check_permission('Delete Port')
@require_http_methods(['DELETE'])
@UIResponse('Virtual NetWork Manage', 'get_network_projects')
def delete_port_action(request, port_id):
    """
    :param request:request object, port_id
    :return:view<'virtual_network_manage/networkprojectindex.html'>::action for delete a port
    """
    try:
        port = api.quantum.port_get(request, port_id)
        api.quantum.port_delete(request, port_id)
    except Unauthorized:
        raise
    except Exception as exe:
        msg = 'Unable to delete port.'
        LOG.error('Failed to delete port,the error is %s' % exe.message)
        return HttpResponse({ "message":msg, "statusCode":UI_RESPONSE_DWZ_ERROR }, status = UI_RESPONSE_ERROR)
    return HttpResponse({"message":"delete port successfully!",
                         "statusCode":UI_RESPONSE_DWZ_SUCCESS ,
                         "object_name":getattr(port, 'name', 'unknown')}, status = UI_RESPONSE_DWZ_SUCCESS)



