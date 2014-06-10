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

#    code begin
from django import shortcuts
from django.views.decorators.http import require_GET, require_POST, \
                                            require_http_methods
from django.http import HttpResponse

from dashboard import api
from dashboard.authorize_manage.utils import switch_tenants
from dashboard.utils import jsonutils, ui_response, UIResponse, Pagenation

from dashboard.utils.ui import *

from dashboard.exceptions import Unauthorized
from dashboard.exceptions import LicenseForbidden

from .forms import CreateGateWayForm, CreateRoutersDetailForm, CreateRouterForm

GATEWAYNOEXIST = 0

@require_GET
def get_routers_projects(request):
    """
    :param request:request object
    :return:view<'project_manage/index.html'>::list of tenants
    """
    return shortcuts.render(request, 'virtual_router_manage/routersindex.html')

@require_GET
def get_routers_projects_menu(request):
    """
    :param request:request object
    :return:view<'project_manage/index.html'>::list of tenants
    """
    project_menus = []
    projects = []
    try:
        projects = api.tenant_list(request, admin = True)
    except Unauthorized:
        raise
    except Exception,exc:
        msg = 'Unable to retrieve project list,%s.' % exc
        LOG.error(msg)
    for project in projects:
        routerprojects = []
        if project.enabled and None != switch_tenants(request, project.id):

            routerprojectlist = api.quantum.router_list(request)
            if routerprojectlist:
                for routerProject in routerprojectlist:
                    if project.id == routerProject.tenant_id:
                        routerProject_obj = {
                        'routerProject_name':routerProject.name,
                        'routerProject_id':routerProject.id,
                        'gateway_networkId':get_hasgatewayflag(routerProject)}

                        routerprojects.append(routerProject_obj)

        project_menu = {
            'project_name': project.name,
            'project_id': project.id,
            'project_enabled': project.enabled,
            'project_routerProject': routerprojects
        }
        project_menus.append(project_menu)
    return HttpResponse(jsonutils.dumps(project_menus))

@require_GET
@Pagenation('virtual_router_manage/index.html')
def get_routers_projects_list(request, tenant_id):
    """
    :param request:request object
    :return:view<'user_manage/index.html'>::list of users
    """
    args = {}
    resultrouterlist = []
    try:
        switch_tenants(request, tenant_id)
        routerprojectlist = api.quantum.router_list(request)

        for routerProject in routerprojectlist :
            if  routerProject.tenant_id == tenant_id:

                resultrouterlist.append(routerProject)

                if routerProject.external_gateway_info:
                    ext_net_id = routerProject.external_gateway_info['network_id']
                    try:
                        ext_net = api.quantum.network_get(request,
                                                        ext_net_id,
                                                        expand_subnet = False)
                        ext_net.set_id_as_name_if_empty(length = 0)
                        routerProject.external_gateway_info['network'] = ext_net.name

                    except Unauthorized:
                        raise
                    except Exception , exc:
                        msg = 'Unable to retrieve an external network %s.%s'  % (ext_net_id, exc)
                        LOG.error(msg)
                        routerProject.external_gateway_info['network'] = ext_net_id

        tenant_name = api.tenant_get(request, tenant_id, admin = True)
    except Unauthorized:
        raise
    except Exception, exc:
        msg = get_text('Unable to retrieve router list')
        LOG.error('Unable to retrieve router list. %s' % exc.message)
        return HttpResponse({ "message" : msg, "statusCode" : UI_RESPONSE_DWZ_ERROR },
            status = UI_RESPONSE_ERROR)

    args['list'] = resultrouterlist
    args['tenant_name'] = tenant_name.name
    args['tenant_id'] = tenant_id

    return args

def get_hasgatewayflag(router_project):
    if  router_project.external_gateway_info:
        return router_project.external_gateway_info['network_id']
    else:
        return GATEWAYNOEXIST

@check_permission('Delete RouterProject')
@require_http_methods(['DELETE'])
@UIResponse('Virtual Routers Manage', 'get_routers_projects')
def delete_routerproject_action(request, routerproject_id):
    router_old = None
    try:
#        switch_tenants(request, tenant_id)
        router_old = api.quantum.router_get(request, routerproject_id)
        api.quantum.router_delete(request, routerproject_id)
    except Unauthorized:
        raise
    except Exception, exc:
        if exc.message.find('still has active ports') != -1:
            msg = get_text('Error! The router still has active ports.')
        else:
            msg = get_text('Unable to delete router project:%s.' )% (router_old.name)

        LOG.error('Unable to delete router project."%s"' % exc.message)
        return HttpResponse({ "message" : msg, "statusCode":UI_RESPONSE_DWZ_ERROR },
            status = UI_RESPONSE_ERROR)
    msg = get_text('delete router successfully!')
    return HttpResponse({"message":msg, "statusCode" : UI_RESPONSE_DWZ_SUCCESS ,
                         "object_name" : getattr(router_old, 'name', 'unknown')},
                        status = UI_RESPONSE_DWZ_SUCCESS)

@require_GET
def get_routerprojectinfo(request, tenant_id, router_project_id):
    routerproject = None
    try:
        routerproject = api.quantum.router_get(request, router_project_id)

        routerproject.set_id_as_name_if_empty(length = 0)

    except Unauthorized:
        raise
    except Exception, exc:

        msg = get_text('Unable to retrieve the router :%s.') % (routerproject.name)
        LOG.error('Unable to retrieve the router "%s".' % (exc.message))
        return HttpResponse({ "message" : msg, "statusCode" : UI_RESPONSE_DWZ_ERROR },
                            status = UI_RESPONSE_ERROR)
    if routerproject.external_gateway_info:
        ext_net_id = routerproject.external_gateway_info['network_id']
        ext_net = None
        try:
            ext_net = api.quantum.network_get(request, ext_net_id, expand_subnet = False)
            ext_net.set_id_as_name_if_empty(length = 0)
            routerproject.external_gateway_info['network'] = ext_net.name

        except Exception , exc:
            msg = get_text('Unable to retrieve an external network : %s.') % ext_net.name
            LOG.error('Unable to retrieve an external network : %s. %s' % (ext_net_id, exc.message))
            routerproject.external_gateway_info['network'] = ext_net_id
            return HttpResponse({ "message" : msg, "statusCode" : UI_RESPONSE_DWZ_ERROR },
                                status = UI_RESPONSE_ERROR)

     #interface
    try:
        ports = api.quantum.port_list(request, device_id = router_project_id)

        for port in ports:
            port.set_id_as_name_if_empty()

        return shortcuts.render(request, 'virtual_router_manage/routerprojectinfo.html',
                                {'routerproject' : routerproject,
                                 'interfaces' : ports,
                                 "tenant_id" : tenant_id })
    except Exception, exc:

        msg = get_text('Port list can not be retrieved.')
        LOG.error('Port list can not be retrieved : %s.' % exc.message)
        return HttpResponse(jsonutils.dumps(ui_response(message = msg)))

@check_permission('Delete Router Interface')
@require_http_methods(['DELETE'])
@UIResponse('Virtual Routers Manage', 'get_routers_projects')
def delete_routerif_action(request, routerproject_id, interface_id):
    try:
        port = api.quantum.port_get(request, interface_id)
        if port['device_owner'] == 'network:router_gateway':
            api.quantum.router_remove_gateway(request, routerproject_id)
        else:
            api.quantum.router_remove_interface(request,
                                                routerproject_id,
                                                port_id = interface_id)
    except Unauthorized:
        raise
    except Exception, exc:
        msg = get_text('Failed to delete interface')
        LOG.error('Failed to delete interface :%s' % exc.message)
        return HttpResponse(jsonutils.dumps(ui_response(message = msg)))
    msg = get_text('delete interface successfully!')
    oldrouter = api.quantum.router_get(request, routerproject_id)
    return HttpResponse({"message" : msg, "statusCode" : UI_RESPONSE_DWZ_SUCCESS ,
                         "object_name" : "router=" + getattr(oldrouter, 'name','unknown') +
                         ", interface_id=" + interface_id}, status = UI_RESPONSE_DWZ_SUCCESS)

@require_GET
def create_routerprojectdetail(request, tenant_id, routerproject_id):

    try:
        switch_tenants(request, tenant_id)
        myrouterproject = api.quantum.router_get(request, routerproject_id)

    except Unauthorized:
        raise
    except Exception , exc:
        msg = get_text('Failed to retrieve the router.')
        LOG.error('Failed to retrieve the router:%s' % exc.message)
        return HttpResponse(jsonutils.dumps(ui_response(message = msg)))

    initial = {'router_id' : myrouterproject.id,
               'router_name' : myrouterproject.name,}

    form = CreateRoutersDetailForm(request, initial = initial)
    return shortcuts.render(request, 'virtual_router_manage/createinterface.html',
                            {'form' : form,'tenant_id':tenant_id,'router_id' : routerproject_id})

@check_permission('Add Router Interface')
@require_POST
@UIResponse('Virtual Routers Manage', 'get_routers_projects')
def create_interface_action(request, router_id):
    try:
        myrouterproject = api.quantum.router_get(request, router_id)

    except Unauthorized:
        raise
    except Exception , exc:
        msg = get_text('Failed to retrieve the router.')
        LOG.error('Failed to retrieve the router:%s' % exc.message)

        return HttpResponse(jsonutils.dumps(ui_response(message = msg)))

    initial = {'router_id':myrouterproject.id,
               'router_name': myrouterproject.name,}

    form = CreateRoutersDetailForm(request, request.POST, initial = initial)

    if form.is_valid():
        data = form.cleaned_data
        try:
            api.quantum.router_add_interface(request,
                                            data['router_id'],
                                            subnet_id = data['subnet_id'])

        except LicenseForbidden:
            raise
        except Exception , exc:
            if exc.message.find('in use') != -1:
                msg = get_text('Error! The SubNet is in use.')
            elif exc.message.find('Router already has a port on subnet') != -1:
                msg = get_text('Router already has a port on subnet.')
            else:
                msg = get_text('Failed to add_interface.')
            LOG.error('Failed to add_interface: %s' % exc.message)

            return HttpResponse(jsonutils.dumps(ui_response(message = msg)))

        msg = get_text('Create interface successfully!')
        return HttpResponse({"message":msg, "statusCode" : UI_RESPONSE_DWZ_SUCCESS ,
                            "object_name" : data['router_name']},
                            status = UI_RESPONSE_DWZ_SUCCESS)
    else:
        return HttpResponse({"form":form, "message" : "",
                            "statusCode" : UI_RESPONSE_DWZ_ERROR},
                            status = UI_RESPONSE_ERROR)

@require_GET
def create_gateway_detail(request, router_id):

    try:
        myrouterproject = api.quantum.router_get(request, router_id)

    except Unauthorized:
        raise

    except Exception , exc:
        msg = get_text('Failed to retrieve the router.')
        LOG.error('Failed to retrieve the router. %s' % exc.message)
        return HttpResponse(jsonutils.dumps(ui_response(message = msg)))

    initial = {'router_id' : myrouterproject.id,
               'router_name' : myrouterproject.name,}
    try:
        form = CreateGateWayForm(request, initial = initial)
    except Exception, exc:
        msg = 'Create gate way form error. %s' % exc
        LOG.error(msg)

    return shortcuts.render(request, 'virtual_router_manage/creategateway.html',
                            {'form' : form,'router_id' : router_id})

@check_permission('Set Gateway')
@require_POST
@UIResponse('Virtual Routers Manage', 'get_routers_projects')
def create_gateway_action(request, router_id):

    try:
        myrouterproject = api.quantum.router_get(request, router_id)

    except Unauthorized:
       raise
    except Exception , exc:
        msg = get_text('Failed to retrieve the router.')
        LOG.error('Failed to retrieve the router %s' % exc.message)
        return HttpResponse(jsonutils.dumps(ui_response(message = msg)))

    initial = {'router_id' : myrouterproject.id,
               'router_name' : myrouterproject.name,}

    form = CreateGateWayForm(request, request.POST, initial = initial)

    if form.is_valid():
        data = form.cleaned_data
        try:

            api.quantum.router_add_gateway(request,
                                            data['router_id'],
                                            data['extNetwork'])

        except Exception , exc:
            msg = get_text('Failed to add gateway.')
            LOG.error('Failed to add gateway %s' % exc.message)
            return HttpResponse(jsonutils.dumps(ui_response(message = msg)))
        msg = get_text("Create gateway successfully!")

        return HttpResponse({"message" : msg, "statusCode" : UI_RESPONSE_DWZ_SUCCESS ,
                            "object_name" : data['router_name']},
                            status = UI_RESPONSE_DWZ_SUCCESS)
    else:
        return HttpResponse({"form" : form,"message" : "",
                            "statusCode" : UI_RESPONSE_DWZ_ERROR},
                            status = UI_RESPONSE_ERROR)

@check_permission('Delete Gateway')
@require_http_methods(['DELETE'])
@UIResponse('Virtual Routers Manage', 'get_routers_projects')
def delete_gateway_action(request, router_id):
    try:
        api.quantum.router_remove_gateway(request, router_id)

    except Unauthorized:
        raise
    except Exception , exc:
        msg = get_text('Unable to clear gateway for router.')
        LOG.error('Unable to clear gateway for router :%s' % exc.message)
        return HttpResponse({ "message" : msg, "statusCode" : UI_RESPONSE_DWZ_ERROR },
                            status = UI_RESPONSE_ERROR)

    msg = get_text('delete gateway successfully!')
    return HttpResponse({"message" : msg, "statusCode" : UI_RESPONSE_DWZ_SUCCESS ,
                         "object_name" : router_id}, status = UI_RESPONSE_DWZ_SUCCESS)

@require_GET
def create_router_detail(request, tenant_id, routerortopology):
    form = CreateRouterForm(request)
    return shortcuts.render(request, 'virtual_router_manage/createrouter.html',
                            {'form': form, 'tenant_id' : tenant_id, 'gotoflag' : routerortopology})

@check_permission('Add RouterProject')
@require_POST
@UIResponse('Virtual Routers Manage', 'get_routers_projects')
def create_router_action(request, tenant_id):
    switch_tenants(request, tenant_id)
    form = CreateRouterForm(request, request.POST)
    if form.is_valid():
        data = form.cleaned_data
        try:
            api.quantum.router_create(request,
                                        name = data['name'])

        except Unauthorized:
            raise
        except LicenseForbidden:
            raise
        except Exception , exc:
            msg = get_text('Failed to create router :%s.') % data['name']
            LOG.error('Failed to create router :%s,%s.' % (data['name'], exc.message))
            return HttpResponse({"message" : msg, "statusCode" : UI_RESPONSE_DWZ_ERROR},
                                status = UI_RESPONSE_ERROR)
        msg = get_text('add router successfully!')
        return HttpResponse({"message" : msg, "statusCode" : UI_RESPONSE_DWZ_SUCCESS ,
                             "object_name" : data['name']}, status = UI_RESPONSE_DWZ_SUCCESS)
    else:
        return HttpResponse({"form" : form, "message" : "",
                            "statusCode" : UI_RESPONSE_DWZ_ERROR},
                            status = UI_RESPONSE_ERROR)


@require_POST
@UIResponse('Virtual NetWork Topology', 'get_network_topology')
def create_router_action_topology(request, tenant_id):
    switch_tenants(request, tenant_id)
    form = CreateRouterForm(request, request.POST)
    if form.is_valid():
        data = form.cleaned_data
        try:
            api.quantum.router_create(request,
                name = data['name'])

        except Unauthorized:
            raise
        except Exception , exc:
            msg = get_text('Failed to create router :%s.') % data['name']
            LOG.error('Failed to create router :%s,%s.' % (data['name'], exc.message))
            return HttpResponse({"message" : msg, "statusCode" : UI_RESPONSE_DWZ_ERROR},
                status = UI_RESPONSE_ERROR)
        msg = get_text('add router successfully!')

        return HttpResponse({"message" : msg, "statusCode" : UI_RESPONSE_DWZ_SUCCESS ,
                             "object_name" : data['name']}, status = UI_RESPONSE_DWZ_SUCCESS)
    else:
        return HttpResponse({"form" : form, "message" : "",
                             "statusCode" : UI_RESPONSE_DWZ_ERROR},
            status = UI_RESPONSE_ERROR)
