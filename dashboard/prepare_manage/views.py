# encoding = UTF-8
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

__author__ = 'liuh'

import csv

import logging

LOG = logging.getLogger(__name__)

import time
import md5
import dateutil.parser
import os, zipfile
from datetime import datetime
from django.utils.text import normalize_newlines
from django.utils.translation import ugettext_lazy as _
from novaclient import exceptions
from django import shortcuts
from django.conf import settings
from django.views.decorators.http import require_GET, require_POST
from django.http import HttpResponse
from django.db import connection, transaction, IntegrityError
from django.core.servers.basehttp import FileWrapper

from dashboard import api
from dashboard.utils import Pagenation, jsonutils, ui_response
from dashboard.utils.i18n import get_text
from dashboard.utils.ui import UI_RESPONSE_DWZ_ERROR, UI_RESPONSE_DWZ_SUCCESS, UI_RESPONSE_OK, UI_RESPONSE_NOTFOUND,UI_RESPONSE_ERROR
from dashboard.exceptions import Unauthorized
from dashboard.authorize_manage.utils import get_user_role_name, switch_tenants
from dashboard.authorize_manage import ROLE_PROJECTADMIN, ROLE_ADMIN
from dashboard.prepare_manage.utils import  *
from dashboard.project_manage.views import handle_create, handle_update_quotas
from dashboard.project_manage.forms import CreateTenantForm, UpdateQuotasForm
from dashboard.virtual_network_manage.forms import CreateSubnet, CreateNetwork
from dashboard.virtual_network_manage.views import setup_subnet_parameters
from dashboard.virtual_router_manage.forms import CreateRouterForm, CreateRoutersDetailForm, CreateGateWayForm
from dashboard.log_manage import utils
from dashboard.log_manage.models import LoggingAction
from dashboard.log_manage.views import logs_list_same
from dashboard.image_template_manage.forms import CreateImageForm, LaunchImagePrepareForm
from dashboard.image_template_manage.views import get_images_data
from dashboard.usage import quotas
import dashboard.instance_manage as Instance_Manage
from dashboard.instance_manage.models import Distribution
from dashboard.instance_manage.forms import  LaunchForm, InstanceLiveMigratePrepare, InstanceLiveMigratePrepareForm
import dashboard.hard_template_manage as hard_Manage
from dashboard.node_manage.models import Node
from dashboard.node_manage.forms import NodeForm
from models import NeedToDo


NETWORK_NAME_EMPTY_LENGTH = 0
INSTANCE_LIMIT_PER_USER = 6
A_TITLE = {'project_manage': 'Add Project',
           'project_manage_resource': 'Update Project',
           'volume_manage': 'Update Quotas',
           'virtual_network_manage': 'Create Network',
           'virtual_router_manage': 'Add Router',
           'instance_resource': 'Not enough server resources',
           'log_manage': 'log manage',
           'software_manage': 'ISO file',
           'image_template_manage': 'Launch Instances'}

@require_GET
@Pagenation('prepare_manage/index.html')
def prepare_list(request):
    """
    :param request: request object
    :return view<'prepare_manage/index.html'>: the view of images list
    """
    need_to_do = []
    need_to_dos = []
    args = {}
    tenant_id = request.user.tenant_id
    role = get_user_role_name(request)

    try:
#        if role == ROLE_ADMIN:
#            need_to_do = NeedToDo.objects.filter(role=role)
#        if role == ROLE_PROJECTADMIN:
#            need_to_do = NeedToDo.objects.filter(role=role, tenant_id=tenant_id)
        need_to_do = NeedToDo.objects.all()
        #        need_to_do = [inst for inst in need_to_do if
        #                       inst.status == STATUS_DOING or inst.status == STATUS_NEW]
        for nd in need_to_do:
            if nd.status == STATUS_DOING or nd.status == STATUS_NEW:
                title = tuple(
                    [param for param in nd.parameters[2:-2].split("', '") if
                     param])
                if len(title) > 0:
                    if nd.category == PROJECT_MANAGE_RESOURCE or nd.category==INSTANCE_RESOURCE:
                        title_para = str(title[1]).split(',')
                        title_text = ''
                        for para in title_para:
                            title_text += get_text(para)+' '
                        tenant = str(title[0])
                        title = tuple((tenant, title_text))

                    nd.title = get_text(nd.title) % title
                else:
                    nd.title = get_text(nd.title)
                setattr(nd, 'a_title', A_TITLE[nd.category])
                nd.content = nd.title
                need_to_dos.append(nd)

    except Unauthorized:
        raise
    except Exception, exc:
        LOG.info('No image can be found!%s.' % exc)

    args['list'] = need_to_dos

    return args


def get_prepare_list(request):
    need_to_do = []
    need_to_dos = []
    role = get_user_role_name(request)
    try:
        tenants = api.tenant_list(request, admin=True)

        if role is ROLE_ADMIN:
            need_to_do = NeedToDo.objects.filter(role=role)

        if len(need_to_do) == 1 and role is ROLE_ADMIN:
            need_status = need_to_do[0].status
            need_category = need_to_do[0].category
            if len(tenants) == 1 and (
                need_status == STATUS_CLOSED or need_status == STATUS_DONE) and need_category == PROJECT_MANAGE:
                tenant_id = request.user.tenant_id
                obj_network = CreateVirtualNetworkPrepare(None, role, tenant_id)
                if obj_network.status(request) == STATUS_CLOSED:
                    pass

                obj_router = CreateVirtualRouterPrepare(None, role, tenant_id)
                if obj_router.status(request) == STATUS_CLOSED:
                    pass

                obj_instance = CreateInstancePrepare(None, role, tenant_id)
                if obj_instance.status(request) == STATUS_CLOSED:
                    pass

        if role is ROLE_ADMIN:
            need_to_do = NeedToDo.objects.filter(role=role)
        for nd in need_to_do:
            if nd.status == STATUS_DOING or nd.status == STATUS_NEW:
                title = tuple(
                    [n for n in nd.parameters[2:-2].split("', '") if n])
                if len(title) > 0:
                    if nd.category == PROJECT_MANAGE_RESOURCE or nd.category == INSTANCE_RESOURCE:
                        title_para = str(title[1]).split(',')
                        title_text = ''
                        for para in title_para:
                            title_text += get_text(para) + ' '
                        tenant = str(title[0])
                        title = tuple((tenant, title_text))
                    nd.title = get_text(nd.title) % title
                else:
                    nd.title = get_text(nd.title)
                setattr(nd, 'a_title', A_TITLE[nd.category])
                nd.content = nd.title
                need_to_dos.append(nd)
        return shortcuts.render(request, "prepare_manage/prepare_item.html",
                                {"need_to_do": need_to_dos[:6]})
    except Exception, exc:
        LOG.error('Error is :%s' % exc)

        return shortcuts.render(request, "prepare_manage/prepare_item.html",
                                {"need_to_do": need_to_dos[:6]})

PROJECT_MANAGE = 'project_manage'
PROJECT_MANAGE_RESOURCE = 'project_manage_resource'
VOLUME_MANAGE = 'volume_manage'
VIRTUAL_NETWORK_MANAGE = 'virtual_network_manage'
VIRTUAL_ROUTER_MANAGE = 'virtual_router_manage'
INSTANCE_RESOURCE = 'instance_resource'
LOG_MANAGE = 'log_manage'
SOFTWARE_MANAGE = 'software_manage'
IMAGE_TEMPLATE_MANAGE = 'image_template_manage'
LEN_NUM = 0

def update_prepare_body(request, need_bd):
    icon_update = True
    if need_bd.category == PROJECT_MANAGE:
        obj = CreateTenantPrepare(uuid=need_bd.need_uuid)
        if obj.status(request) == STATUS_CLOSED:
            icon_update = False

    elif need_bd.category == PROJECT_MANAGE_RESOURCE:
        obj = CreateTenantResourcesShortagePrepare(uuid=need_bd.need_uuid)
        if obj.status(request) == STATUS_CLOSED:
            icon_update = False

    elif need_bd.category == VOLUME_MANAGE:
        obj = CreateVolumePrepare(uuid=need_bd.need_uuid)
        if obj.status(request) == STATUS_CLOSED:
            icon_update = False

    elif need_bd.category == VIRTUAL_NETWORK_MANAGE:
        obj = CreateVirtualNetworkPrepare(uuid=need_bd.need_uuid)
        if obj.status(request) == STATUS_CLOSED:
            icon_update = False

    elif need_bd.category == VIRTUAL_ROUTER_MANAGE:
        obj = CreateVirtualRouterPrepare(uuid=need_bd.need_uuid)
        if obj.status(request) == STATUS_CLOSED:
            icon_update = False

    elif need_bd.category == INSTANCE_RESOURCE:
        obj = CreateServerResourceShortagePrepare(uuid=need_bd.need_uuid)
        if obj.status(request) == STATUS_CLOSED:
            icon_update = False

    elif need_bd.category == LOG_MANAGE:
        obj = CreateLogItemToLargePrepare(uuid=need_bd.need_uuid)
        if obj.status(request) == STATUS_CLOSED:
            icon_update = False

    elif need_bd.category == SOFTWARE_MANAGE:
        obj = CreateFindSystemISOFilePrepare(uuid=need_bd.need_uuid)
        if obj.status(request) == STATUS_CLOSED:
            icon_update = False

    elif need_bd.category == IMAGE_TEMPLATE_MANAGE:
        obj = CreateInstancePrepare(uuid=need_bd.need_uuid)
        if obj.status(request) == STATUS_CLOSED:
            icon_update = False

    return icon_update


@require_GET
def create_project_need_form(request, need_uuid):
    """
    :param request:request object
    :return:view<'prepare_manage/project_create.html'>::the form table for creating a tenant
    """

    obj = CreateTenantPrepare(uuid=need_uuid)
    if obj.status(request) == STATUS_CLOSED:
        return shortcuts.render(request, 'prepare_manage/info.html', {
            'message': get_text('You have to create a project')})

    form = CreateTenantForm()
    if obj.begin():
        pass
    return shortcuts.render(request,
                            'prepare_manage/project_create.html',
                            {'form': form, "need_uuid": need_uuid})


@require_POST
def create_project_tenant(request, need_uuid):
    form = CreateTenantForm(request.POST)
    if form.is_valid():
        iRet, msg = handle_create(request, form.cleaned_data)
        role = get_user_role_name(request)
        if iRet:
            obj = CreateTenantPrepare(need_uuid)
            if obj.close():
                pass
            try:
                obj_network = CreateVirtualNetworkPrepare(None, role, iRet)
                if obj_network.renew():
                    pass
            except:
                obj_network = CreateVirtualNetworkPrepare(None, role, iRet)
                if obj_network.renew():
                    pass

            try:
                obj_router = CreateVirtualRouterPrepare(None, role, iRet)
                if obj_router.renew():
                    pass
            except:
                obj_router = CreateVirtualRouterPrepare(None, role, iRet)
                if obj_router.renew():
                    pass

            try:
                obj_instance = CreateInstancePrepare(None, role, iRet)
                if obj_instance.renew():
                    pass
            except:
                obj_instance = CreateInstancePrepare(None, role, iRet)
                if obj_instance.renew():
                    pass
            switch_tenants(request, iRet)
            return HttpResponse(
                jsonutils.dumps({"message": get_text("Create Project Success"),
                                 "statusCode": UI_RESPONSE_OK,
                                 "callbackType": 'closeCurrent',
                                 "tenant_id": iRet}))
        else:
            return HttpResponse(jsonutils.dumps({"message": msg,
                                                 "statusCode": UI_RESPONSE_DWZ_ERROR}))

    else:
        return HttpResponse(jsonutils.dumps({"message": form.errors.as_text(),
                                             "statusCode": UI_RESPONSE_DWZ_ERROR}))


@require_GET
def create_network_index_in_prepare(request, network_obj_id):
    """
    :param request:request object, tenant_id
    :return:view<'prepare_manage/network_create.html'>::create index of network
    """
    tenant_id = request.user.tenant_id

    if network_obj_id == 'project' or network_obj_id is None:
        network_obj_id = 'project'
    else:
        obj = CreateVirtualNetworkPrepare(uuid=network_obj_id)
        network = obj.prepare(request)
        tenant_id = obj.tenant_id
        switch_tenants(request, tenant_id)
        if not network and obj.prepare_id != 'base':
            form = CreateSubnet(request, obj.prepare_id)
            network = api.quantum.network_get(request, obj.prepare_id)
            return shortcuts.render(request,
                                    'prepare_manage/sub_net_create.html',
                                    {'form': form, 'network': network,
                                     'network_obj_id': network_obj_id})

        if obj.status(request) == STATUS_CLOSED:
            return shortcuts.render(request, 'prepare_manage/info.html', {
                'message': get_text('You have to create a network')})
        if obj.begin():
            tenant_id = obj.tenant_id
            pass
    switch_tenants(request, tenant_id)
    form = CreateNetwork(request, tenant_id)
    return shortcuts.render(request, 'prepare_manage/network_create.html',
                            {'form': form, 'tenant_id': tenant_id,
                             'network_obj_id': network_obj_id})


@require_POST
def create_network_action_ajax(request, tenant_id, network_obj_id):
    """
    :param request:request object, tenant_id
    :return:view<'prepare_manage/network_project.html'>::create action of network
    """
    form = CreateNetwork(request, tenant_id, request.POST)
    if form.is_valid():
        data = form.cleaned_data
        switch_tenants(request, request.user.tenant_id)
        try:
            params = {'name': data['name'],
                      'tenant_id': data['tenant_id'],
                      'admin_state_up': data['admin_state'],
                      'shared': data['shared'],
                      'router:external': data['external']}
            network = api.quantum.network_create(request, **params)
        except Unauthorized:
            raise
        except Exception, exe:
            msg = get_text('Failed to create network')
            LOG.error("Failed to create network,the error is %s" % exe.message)
            return HttpResponse(jsonutils.dumps(
                {"message": msg, "network_id": None,
                 "statusCode": UI_RESPONSE_DWZ_ERROR}))
        if network_obj_id == 'project' or network_obj_id is None:
            network_obj_id = 'project'
            role = get_user_role_name(request)
            need_to_do = NeedToDo.objects.filter(role=role,
                                                 category=VIRTUAL_NETWORK_MANAGE)
            if len(need_to_do) > 0:
                network_obj_id = need_to_do[0].need_uuid
                obj = CreateVirtualNetworkPrepare(uuid=network_obj_id)
                obj._obj.prepare_id = network.id
                if obj.begin():
                    pass
        else:
            obj = CreateVirtualNetworkPrepare(uuid=network_obj_id)
            obj._obj.prepare_id = network.id
            if obj.begin():
                pass
        return HttpResponse(jsonutils.dumps(
            {"message": get_text("Create network successfully!"),
             'network_obj_id': network_obj_id,
             "statusCode": UI_RESPONSE_OK, "callbackType": 'closeCurrent',
             "network_id": network.id}))

    else:
        return HttpResponse(jsonutils.dumps({"message": form.errors.as_text(),
                                             "statusCode": UI_RESPONSE_DWZ_ERROR}))


@require_GET
def create_sub_net_index(request, network_id, network_obj_id):
    """
    :param request:request object, network_id
    :return:view<'prepare_manage/sub_net_create.html'>::index for create subnet
    """
    form = CreateSubnet(request, network_id)
    try:
        network = api.quantum.network_get(request, network_id)
        if network_obj_id is None or network_obj_id == 'project':
            network_obj_id = 'project'

        return shortcuts.render(request, 'prepare_manage/sub_net_create.html',
                                {'form': form, 'network': network,
                                 'network_obj_id': network_obj_id})
    except Unauthorized:
        raise
    except Exception, exe:
        LOG.error('get network info error,the error is %s' % exe.message)

    return HttpResponse(jsonutils.dumps(
        ui_response(message=get_text("get network info error."))))


@require_POST
def create_sub_net_action(request, network_id, network_obj_id):
    """
    :param request:request object, network_id
    :return:view<'prepare_manage/network_project.html'>::action for create subnet
    """
    form = CreateSubnet(request, network_id, request.POST)
    if form.is_valid():
        data = form.cleaned_data
        network = []
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
        except Exception as exe:
            msg = get_text('Failed to create subnet')
            LOG.error('Failed to create subnet,the error is %s' % exe.message)
            return HttpResponse(jsonutils.dumps(
                {"message": msg, "network_id": '',
                 "statusCode": UI_RESPONSE_DWZ_ERROR}))
        if network_obj_id is None or network_obj_id == 'project':
            network_obj_id = 'project'
        else:
            obj = CreateVirtualNetworkPrepare(uuid=network_obj_id)
            if obj.close():
                pass
        return HttpResponse(jsonutils.dumps(
            {"message": get_text("Create subnet successfully!"),
             "callbackType": 'closeCurrent', "network_id": network_id,
             "statusCode": UI_RESPONSE_DWZ_SUCCESS}))
    else:
        return HttpResponse(jsonutils.dumps(
            {"message": form.errors.as_text(), "network_id": '',
             "statusCode": UI_RESPONSE_DWZ_ERROR}))


@require_GET
def get_network_info_list(request, tenant_id, network_id, network_obj_id):
    """
    :param request:request object, tenant_id, network_id
    :return:view<'prepare_manage/sub_net_list.html'>::get a network info
    """
    try:
        switch_tenants(request, tenant_id)
        network = api.quantum.network_get(request, network_id)
        network.set_id_as_name_if_empty(length=NETWORK_NAME_EMPTY_LENGTH)

        sub_nets = api.quantum.subnet_list(request, network_id=network.id)

        for s in sub_nets:
            s.set_id_as_name_if_empty()

        return shortcuts.render(request, 'prepare_manage/sub_net_list.html',
                                {'tenant_id': tenant_id, 'subnets': sub_nets,
                                 'network_obj_id': network_obj_id})
    except Unauthorized:
        raise
    except Exception, exe:
        msg = get_text('get network info error.')
        LOG.error('get network info error,the error is %s' % exe.message)
        return HttpResponse(jsonutils.dumps(ui_response(message=msg)))


@require_GET
def create_router_detail_index(request, virtual_router_obj_id):
    tenant_id = request.user.tenant_id

    if virtual_router_obj_id is None or virtual_router_obj_id == 'None':
        virtual_router_obj_id = None
    else:
        obj = CreateVirtualRouterPrepare(uuid=virtual_router_obj_id)
        router = obj.prepare(request)
        tenant_id = obj.tenant_id

        if not router and obj.prepare_id != 'base':
            switch_tenants(request, tenant_id)
            try:
                my_router_project = api.quantum.router_get(request,
                                                           obj.prepare_id)

            except Unauthorized:
                raise
            except Exception, exc:
                msg = get_text('Failed to retrieve the router.')
                LOG.error('Failed to retrieve the router:%s' % exc.message)
                return HttpResponse(jsonutils.dumps(ui_response(message=msg)))

            initial = {'router_id': my_router_project.id,
                       'router_name': my_router_project.name, }

            form = CreateRoutersDetailForm(request, initial=initial)
            return shortcuts.render(request,
                                    'prepare_manage/create_interface.html',
                                    {'form': form, 'tenant_id': tenant_id,
                                     'router_id': obj.prepare_id,
                                     'virtual_router_obj_id': virtual_router_obj_id})

        if obj.status(request) == STATUS_CLOSED:
            return shortcuts.render(request, 'prepare_manage/info.html', {
                'message': get_text('You have to create a network')})
        if obj.begin():
            tenant_id = obj.tenant_id
            pass
    switch_tenants(request, tenant_id)
    form = CreateRouterForm(request)
    return shortcuts.render(request, 'prepare_manage/create_router.html',
                            {'form': form, 'tenant_id': tenant_id,
                             'virtual_router_obj_id': virtual_router_obj_id})


@require_POST
def create_router_action_ajax(request, tenant_id, virtual_router_obj_id):
    form = CreateRouterForm(request, request.POST)
    if form.is_valid():
        data = form.cleaned_data
        try:
            router = api.quantum.router_create(request, name=data['name'])
        except Unauthorized:
            raise
        except Exception, exc:
            msg = get_text('Failed to create router :%s.') % data['name']
            LOG.error('Failed to create router :(%s,%s).' % (
                data['name'], exc.message))
            return HttpResponse(jsonutils.dumps(
                {"message": msg, "router_id": '',
                 "statusCode": UI_RESPONSE_DWZ_ERROR}))
        msg = get_text('add router successfully!')
        if virtual_router_obj_id is None or virtual_router_obj_id == 'None':
            virtual_router_obj_id = None
            role = get_user_role_name(request)
            need_to_do = NeedToDo.objects.filter(role=role,
                                                 category=VIRTUAL_ROUTER_MANAGE)
            if len(need_to_do) > 0:
                virtual_router_obj_id = need_to_do[0].need_uuid
                obj = CreateVirtualRouterPrepare(uuid=virtual_router_obj_id)
                obj._obj.prepare_id = router.id

                if obj.begin():
                    tenant_id = obj.tenant_id
                    pass
        else:
            obj = CreateVirtualRouterPrepare(uuid=virtual_router_obj_id)
            obj._obj.prepare_id = router.id
            if obj.begin():
                tenant_id = obj.tenant_id
                pass
        switch_tenants(request, tenant_id)
        return HttpResponse(jsonutils.dumps(
            {"message": msg, "router_id": router.id,
             'virtual_router_obj_id': virtual_router_obj_id,
             "statusCode": UI_RESPONSE_DWZ_SUCCESS,
             "callbackType": 'closeCurrent'}))
    else:
        return HttpResponse(jsonutils.dumps(
            {"message": form.errors.as_text(), "router_id": '',
             "statusCode": UI_RESPONSE_DWZ_ERROR}))


@require_GET
def routers_projects_list(request, tenant_id, router_id, virtual_router_obj_id):
    """
    :param request:request object, tenant_id
    :return:view<'prepare_manage/create_router_suc.html'>::create index of network
    """
    router_list = []
    try:
        switch_tenants(request, tenant_id)
        project_list = api.quantum.router_list(request)

        for routerProject in project_list:
            if  routerProject.tenant_id == tenant_id:
                router_list.append(routerProject)

                if routerProject.external_gateway_info:
                    ext_net_id = routerProject.\
                                 external_gateway_info['network_id']
                    try:
                        ext_net = api.quantum.network_get(request,
                                                          ext_net_id,
                                                          expand_subnet=False)
                        ext_net.set_id_as_name_if_empty(length=0)
                        routerProject.external_gateway_info[
                        'network'] = ext_net.name

                    except Unauthorized:
                        raise
                    except Exception, exc:
                        msg = 'Unable to retrieve an external network %s.%s'\
                              % (ext_net_id, exc)
                        LOG.error(msg)
                        routerProject.external_gateway_info[
                        'network'] = ext_net_id

        tenant_name = api.tenant_get(request, tenant_id, admin=True)
        if virtual_router_obj_id is None or virtual_router_obj_id == 'None':
            virtual_router_obj_id = None
        else:
            obj = CreateVirtualRouterPrepare(uuid=virtual_router_obj_id)
            if obj.begin():
                pass
    except Unauthorized:
        raise
    except Exception, exc:
        msg = get_text('Unable to retrieve router list')
        LOG.error('Unable to retrieve router list. %s' % exc.message)
        return HttpResponse(jsonutils.dumps(ui_response(message=msg)))

    return shortcuts.render(request, 'prepare_manage/create_router_suc.html',
                            {'tenant_name': tenant_name.name,
                             'router_id': router_id, 'tenant_id': tenant_id,
                             'router_list': router_list,
                             'virtual_router_obj_id': virtual_router_obj_id})


@require_GET
def create_router_project_index(request, tenant_id, router_project_id,
                                virtual_router_obj_id):
    try:
        switch_tenants(request, tenant_id)
        my_router_project = api.quantum.router_get(request, router_project_id)

    except Unauthorized:
        raise
    except Exception, exc:
        msg = get_text('Failed to retrieve the router.')
        LOG.error('Failed to retrieve the router:%s' % exc.message)
        return HttpResponse(jsonutils.dumps(ui_response(message=msg)))

    initial = {'router_id': my_router_project.id,
               'router_name': my_router_project.name, }

    form = CreateRoutersDetailForm(request, initial=initial)
    if virtual_router_obj_id is None or virtual_router_obj_id == 'None':
        virtual_router_obj_id = None
        ## update router
    else:
        obj = CreateVirtualRouterPrepare(uuid=virtual_router_obj_id)
        if obj.begin():
            pass
    return shortcuts.render(request, 'prepare_manage/create_interface.html',
                            {'form': form, 'tenant_id': tenant_id,
                             'router_id': router_project_id,
                             'virtual_router_obj_id': virtual_router_obj_id})


@require_POST
def create_interface_action_index(request, router_id, virtual_router_obj_id):
    try:
        my_router_project = api.quantum.router_get(request, router_id)

    except Unauthorized:
        raise
    except Exception, exc:
        msg = get_text('Failed to retrieve the router.')
        LOG.error('Failed to retrieve the router:%s' % exc.message)

        return HttpResponse(jsonutils.dumps(ui_response(message=msg)))

    initial = {'router_id': my_router_project.id,
               'router_name': my_router_project.name, }

    form = CreateRoutersDetailForm(request, request.POST, initial=initial)

    if form.is_valid():
        data = form.cleaned_data
        try:
            api.quantum.router_add_interface(request,
                                             data['router_id'],
                                             subnet_id=data['subnet_id'])

        except Exception, exc:
            LOG.error('Failed to add_interface: %s' % exc.message)

            if exc.message.find('in use') != -1:
                msg = get_text('Error! The SubNet is in use.')
            else:
                msg = get_text('Failed to add_interface.')

            return HttpResponse(jsonutils.dumps(ui_response(message=msg)))
        msg = get_text('Create interface successfully!')
        if virtual_router_obj_id is not None or virtual_router_obj_id != 'None':
            obj = CreateVirtualRouterPrepare(uuid=virtual_router_obj_id)
            if obj.end():
                pass
        return HttpResponse(jsonutils.dumps(
            {"message": msg, "router_id": router_id,
             "callbackType": 'closeCurrent',
             "statusCode": UI_RESPONSE_DWZ_SUCCESS}))
    else:
        return HttpResponse(jsonutils.dumps(
            {"message": 'Create router failed', "router_id": '',
             "statusCode": UI_RESPONSE_DWZ_ERROR}))


@require_GET
def get_router_project_info_list(request, tenant_id, router_project_id,
                                 router_topology, virtual_router_obj_id):
    try:
        ports = api.quantum.port_list(request, device_id=router_project_id)

        for port in ports:
            port.set_id_as_name_if_empty()
        if router_topology == '1':
            return shortcuts.render(request,
                                    'prepare_manage/router_project_info.html',
                                    {'interfaces': ports,
                                     "tenant_id": tenant_id,
                                     "router_id": router_project_id,
                                     'virtual_router_obj_id': virtual_router_obj_id})
        else:
            if virtual_router_obj_id is None or virtual_router_obj_id == 'None':
                virtual_router_obj_id = None
            else:
                obj = CreateVirtualRouterPrepare(uuid=virtual_router_obj_id)
                if obj.end():
                    pass
            return shortcuts.render(request, 'prepare_manage/gateway_info.html',
                                    {'interfaces': ports,
                                     "tenant_id": tenant_id,
                                     "router_id": router_project_id})
    except Exception, exc:
        msg = get_text('Port list can not be retrieved.')
        LOG.error('Port list can not be retrieved : %s.' % exc.message)
        return HttpResponse(jsonutils.dumps(ui_response(message=msg)))


@require_GET
def create_gateway_detail_index(request, router_id, virtual_router_obj_id):
    try:
        my_router_project = api.quantum.router_get(request, router_id)

    except Unauthorized:
        raise

    except Exception, exc:
        msg = get_text('Failed to retrieve the router.')
        LOG.error('Failed to retrieve the router. %s' % exc.message)
        return HttpResponse(jsonutils.dumps(ui_response(message=msg)))

    initial = {'router_id': my_router_project.id,
               'router_name': my_router_project.name, }
    try:
        form = CreateGateWayForm(request, initial=initial)
    except Exception, exc:
        msg = 'error is %s' % exc
        LOG.error(msg)

    return shortcuts.render(request, 'prepare_manage/create_gateway.html',
                            {'form': form, 'router_id': router_id,
                             'tenant_id': my_router_project.tenant_id,
                             'virtual_router_obj_id': virtual_router_obj_id})


@require_POST
def create_gateway_action_ajax(request, router_id):
    try:
        my_router_project = api.quantum.router_get(request, router_id)

    except Unauthorized:
        raise
    except Exception, exc:
        msg = get_text('Failed to retrieve the router.')
        LOG.error('Failed to retrieve the router %s' % exc.message)
        return HttpResponse(jsonutils.dumps(ui_response(message=msg)))

    initial = {'router_id': my_router_project.id,
               'router_name': my_router_project.name, }

    form = CreateGateWayForm(request, request.POST, initial=initial)
    msg = get_text('Failed to add gateway.')
    if form.is_valid():
        data = form.cleaned_data
        try:
            api.quantum.router_add_gateway(request,
                                           data['router_id'],
                                           data['extNetwork'])
        except Unauthorized:
            raise
        except Exception, exc:
            LOG.error('Failed to add gateway %s' % exc.message)
            return HttpResponse(jsonutils.dumps(
                {"message": msg, "router_id": '',
                 "statusCode": UI_RESPONSE_DWZ_ERROR}))
        msg = get_text("Create gateway successfully!")
        return HttpResponse(jsonutils.dumps(
            {"message": msg, "router_id": router_id,
             'tenant_id': my_router_project.tenant_id,
             "callbackType": 'closeCurrent',
             "statusCode": UI_RESPONSE_DWZ_SUCCESS}))
    else:
        return HttpResponse(jsonutils.dumps(
            {"message": msg, "router_id": '',
             "statusCode": UI_RESPONSE_DWZ_ERROR}))


def log_large_page(request, log_id):
    log_news = get_text(
        'The number of the logs item is so large, handle please')
    try:
        log_lists = LoggingAction.objects.order_by('-create_at').all()
        log_news = get_text(
            "The number of the logs item is so large(%s),Whether to backup") % len(
            log_lists)
    except Exception, exc:
        LOG.error('Error is :%s' % exc)

    obj = CreateLogItemToLargePrepare(uuid=log_id)
    if obj.status(request) == STATUS_CLOSED:
        return shortcuts.render(request, 'prepare_manage/info.html', {
            'message': get_text('Log has been dealing with')})
    if obj.begin():
        tenant_id = obj.tenant_id
        pass
    switch_tenants(request, tenant_id)
    return shortcuts.render(request, 'prepare_manage/log_init.html',
                            {"log_id": log_id, 'log_news': log_news})


@require_GET
def log_export_form_in_prepare(request, log_id):
    module_choices = []
    event_choices = [('add', get_text('add')), ('edit', get_text('edit')),
                     ('del', get_text('del')), ('login', get_text('login')),
                     ('logout', get_text('logout'))]
    try:
        for log_conf_info in settings.LOG_INFORMATIONS.values():
            module_choice = (log_conf_info[1],
                             get_text(log_conf_info[1]))
            if module_choices.count(module_choice) < 1:
                module_choices.append(module_choice)

    except Unauthorized:
        raise
    except Exception, exc:
        LOG.error("error is %s." % exc)
    obj = CreateLogItemToLargePrepare(uuid=log_id)
    if obj.begin():
        pass
    return shortcuts.render(request, 'prepare_manage/log_export.html',
                            {'log_id': log_id, "module_choices": module_choices,
                             "event_choices": event_choices})


@require_GET
@Pagenation('prepare_manage/log_delete.html')
def log_query_prepare_index(request, log_id):
    """
    :param request: request object
    :return: view <'prepare_manage/log_export.html'> of the log list
    """
    module_choices = []
    role_name = ROLE_ADMIN
    search_ins = []
    event_choices = [('add', get_text('add')), ('edit', get_text('edit')),
                     ('del', get_text('del')), ('login', get_text('login')),
                     ('logout', get_text('logout'))]
    try:
        for log_conf_info in settings.LOG_INFORMATIONS.values():
            module_choice = (log_conf_info[1],
                             get_text(log_conf_info[1]))
            if module_choices.count(module_choice) < 1:
                module_choices.append(module_choice)

        role_name = get_user_role_name(request)

        if role_name == ROLE_PROJECTADMIN:
            tenants = api.tenant_list(request, request.user.is_superuser)
            for tenant in tenants:
                search_ins.append(tenant.id)
    except Unauthorized:
        raise
    except Exception, exc:
        LOG.error("error is %s." % exc)
    module = ''
    event = ''
    begin_time = ''
    end_time = ''
    log_lists = LoggingAction.objects.order_by('-create_at').all()
    args = {}

    if request.GET.has_key('module'):
        module = request.GET['module']
        if module != '':
            log_lists = log_lists.filter(module=module)

    if request.GET.has_key('event'):
        event = request.GET['event']
        if event != '':
            log_lists = log_lists.filter(event=event)

    if request.GET.has_key('begintime'):
        begin_time = request.GET['begintime']
        if begin_time != '':
            log_lists = log_lists.filter(
                create_at__gte=(dateutil.parser.parse(begin_time) + abs(
                    datetime.now() - datetime.utcnow())))

    if request.GET.has_key('endtime'):
        end_time = request.GET['endtime']
        if end_time != '':
            log_end_time = dateutil.parser.parse(end_time)
            log_end_time = log_end_time.replace(hour=23, minute=59, second=59)
            log_lists = log_lists.filter(create_at__lte=log_end_time)
    s_list = []
    if role_name == ROLE_PROJECTADMIN:
        if len(search_ins) != 0:
            for sins in search_ins:
                sin_list = log_lists.filter(tenantid=sins)
                s_list.extend(sin_list)
            log_lists = s_list

            obj = CreateLogItemToLargePrepare(uuid=log_id)
            if obj.begin():
                pass

    args['list'] = log_lists
    args['module_choices'] = module_choices
    args['event_choices'] = event_choices
    args["module"] = module
    args["event"] = event
    args["begintime"] = begin_time
    args["endtime"] = end_time
    args["role"] = role_name
    args['log_id'] = log_id
    return args


def logs_count_in_prepare(request):
    log_lists = logs_list_same(request)
    log_list_len = len(log_lists)
    if log_list_len < 1:
        return HttpResponse(jsonutils.dumps(
            {"message": get_text('Can not export logs'),
             "statusCode": UI_RESPONSE_DWZ_ERROR}))
    return HttpResponse(
        jsonutils.dumps({"message": '', "statusCode": UI_RESPONSE_DWZ_SUCCESS}))

#Just as an argument
#begin
LOG_LIST_FILE_LINES = 65535
#end

@require_GET
def prepare_export_logs(request, log_id):
    """
    Export Logs for system.s
    :param request:
    :return:
    """
    resp = HttpResponse()
    resp['Content-Disposition'] = 'attachment; filename=log.zip'
    resp['Content-Type'] = 'application/zip;'

    out_os = 1
    try:
        user_agent = request.META['HTTP_USER_AGENT']
        if user_agent.count("Windows") > 0:
            out_os = 2
        elif user_agent.count("MacOs") > 0:
            out_os = 3
    except:
        pass

    log_lists = logs_list_same(request)

    log_list_len = len(log_lists)
    log_length = divmod(log_list_len, LOG_LIST_FILE_LINES)
    if log_length[1] != 0:
        log_count = log_length[0] + 1
    else:
        log_count = log_length[0]

    head_array = ['module', 'event', 'content', 'create_at', 'user_name',
                  'tenant_name', 'is_primary']
    #Windows system
    if out_os == 2:
        head_array = [head_w.encode('GBK') + ',' for head_w in head_array]
    #MacOs system
    elif out_os == 3:
        head_array = [head_w + ': ' for head_w in head_array]
    a_file = []
    st_path = ""
    try:
        if os.path.exists(settings.EXPORTS_ROOT):
            c_time = datetime.now().utcnow()
            st_path = c_time.strftime('%Y-%m-%d %X')
        for log_wr in range(log_count):
            first_wr = log_wr * LOG_LIST_FILE_LINES
            second_wr = (log_wr + 1) * LOG_LIST_FILE_LINES
            log_resource = log_lists[first_wr:second_wr]
            if log_count == 1:
                log_resource = log_lists[first_wr:log_list_len]
            elif log_wr == log_count - 1:
                log_resource = log_lists[first_wr:]
            created_at = datetime.now().utcnow()
            file_path = os.path.join(settings.EXPORTS_ROOT,
                                     str(created_at) + '.csv')
            a_file.append(str(created_at))
            cfl = open(file_path, 'wb')
            wr = csv.writer(cfl, dialect='excel', quoting=csv.QUOTE_MINIMAL)
            wr.writerow(head_array)
            #by liu h
            for log in log_resource:
                content_array = [get_text(log.module),
                                 log.event.replace(" ", "\t"),
                                 log.content.replace(" ", "\t"),
                                 log.create_at.replace(" ", "\t"),
                                 log.username.replace(" ", "\t"),
                                 log.tenant.replace(" ", "\t"),
                                 log.is_primary.replace(" ", "\t")]
                #Windows system
                if out_os == 2:
                    content_array = [c_arr.encode('GBK') + "," for c_arr in
                                     content_array]
                #MacOs system
                elif out_os == 3:
                    content_array = [c_arr + ": " for c_arr in content_array]
                try:
                    wr.writerow(content_array)
                except Exception, exc:
                    LOG.error('Unable to generate csv file,%s.' % exc)
            cfl.close()
    except Exception, exc:
        LOG.error('Unable to open csv file path,%s.' % exc)

    zip_name = settings.EXPORTS_ROOT + '/' + st_path + '.zip'
    archive = zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED)
    try:
        for index in range(len(a_file)):
            archive.write(settings.EXPORTS_ROOT + '/' + a_file[index] + '.csv',
                          "/log/" + a_file[index] + ".csv")
        archive.close()
        for file_log in a_file:
            os.remove(settings.EXPORTS_ROOT + '/' + file_log + '.csv')

        zr = open(zip_name, 'r+')

        resp.write(zr.read())
        resp.flush()
        resp.close()
    except Exception, exc:
        LOG.error(exc)
    obj = CreateLogItemToLargePrepare(uuid=log_id)
    if obj.end():
        pass
    return resp


@require_POST
def delete_logs_query_in_prepare(request, log_id):
    """
    Clean all logs for system.
    :param request:request object,user_id
    :return:
    """
    try:
        cursor = connection.cursor()
        sql_where_str = utils.log_search_str(request)
        if sql_where_str == '':
            cursor.execute("DELETE FROM log_manage_loggingaction")
        else:
            cursor.execute(
                "DELETE FROM log_manage_loggingaction WHERE 1=1 " + sql_where_str)

        transaction.commit_unless_managed()
    except Exception, exc:
        msg = get_text('Unable to clean logs.')
        LOG.error('Unable to clean logs, %s.' % exc)
        return HttpResponse(
            jsonutils.dumps(
                {"message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR}))

    log_lists = LoggingAction.objects.order_by('-create_at').all()
    logs = len(log_lists)
    if logs < 700:
        obj = CreateLogItemToLargePrepare(uuid=log_id)
        if obj.close():
            pass
    return HttpResponse(jsonutils.dumps(
        {"message": get_text("delete logs success"),
         "statusCode": UI_RESPONSE_DWZ_SUCCESS,
         "callbackType": "closeCurrent"}))


@require_GET
def delete_log_form_in_prepare(request, uuid=None):
    return shortcuts.render(request, 'prepare_manage/delete_log.html',
                            {'uuid': uuid})


@require_GET
def delete_log_in_prepare(request, uuid):
    """
    Delete one log.
    :param request:request object;create_at:the create_at item for the log
    :return:
    """
    try:
        log = LoggingAction.objects.get(uuid=uuid)
        log.delete()
    except Exception, exc:
        msg = get_text('Unable to clean log.')
        LOG.error('Unable to clean log, %s.' % exc)
        return HttpResponse(
            jsonutils.dumps(
                {"message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR}))
    return HttpResponse(jsonutils.dumps(
        {"message": get_text("delete logs success"),
         "statusCode": UI_RESPONSE_DWZ_SUCCESS}))


def get_log_detail_in_prepare(request, uuid=None):
    try:
        log = LoggingAction.objects.filter(uuid=uuid)

        if log:
            log = log[0]
        else:
            log = []
    except Exception, exc:
        LOG.error('Unable to retrieve log list,%s.' % exc)
        log = []

    return shortcuts.render(request, 'prepare_manage/log_detail.html',
                            {'log': log})


@require_GET
def image_init_page(request, img_obj_id):
    tenant_id = request.user.tenant_id

    if img_obj_id is None or img_obj_id == "None":
        img_obj_id = None
    else:
        obj = CreateInstancePrepare(uuid=img_obj_id)
        if obj.status(request) == STATUS_CLOSED:
            return shortcuts.render(request, 'prepare_manage/info.html', {
                'message': get_text('You have to create a instance')})
        if obj.begin():
            tenant_id = obj.tenant_id
            pass
    switch_tenants(request, tenant_id)
    return shortcuts.render(request, 'prepare_manage/image_init.html',
                            {"img_obj_id": img_obj_id})


@require_GET
def create_image_form_page(request, img_obj_id, page_id):
    """
    :param request: request object
    :return view<'prepare_manage/image_create_and_instance.html'>: the view create image form
    """
    old_tenant_id = request.user.tenant_id

    created_at = datetime.now().utcnow()
    uuid = md5.new(str(created_at)).hexdigest()
    if page_id == '1':
        form = CreateImageForm(request)
        return shortcuts.render(request, 'prepare_manage/image_create.html',
                                {'form': form, 'old_tenant_id': old_tenant_id,
                                 'uuid': uuid, 'img_obj_id': img_obj_id})
    else:
        kwargs = {
            'flavor_input_list': Instance_Manage.views.search_flavor_status(
                request),
            'flavor_list': Instance_Manage.views.flavor_list(request),
            'keypair_list': Instance_Manage.views.keypair_list(request),
            'security_group_list': Instance_Manage.views.security_group_list(
                request),
            'networks': Instance_Manage.views.network_list(request),
            'volume_list': Instance_Manage.views.volume_list(request)}
        form = LaunchImagePrepareForm(request, **kwargs)
        return shortcuts.render(request,
                                'prepare_manage/image_create_and_instance.html',
                                {'form': form, 'old_tenant_id': old_tenant_id,
                                 'uuid': uuid, 'img_obj_id': img_obj_id})


#Just as an argument
#begin
PARAMETER_NUMBER_ZERO = 0
PARAMETER_NUMBER_ONE = 1
PARAMETER_NEGATIVE_ONE = -1
PARAMETER_NEGATIVE_TWO = -2
PARAMETER_NEGATIVE_THREE = -3
UI_IMAGE_STATUS_ACTIVE = "active"
UI_INSTANCE_STATUS_ACTIVE = "ACTIVE"
UI_INSTANCE_STATUS_ERROR = "ERROR"
UI_INSTANCE_STATUS_RESOURCE_IS_NOT_ENOUGH = "RESOURCE_IS_NOT_ENOUGH"
TIME_CHECK_PER_IMAGE_STATUS_SECONDS = 5
UI_CYCLE_IMG_IMAGE_TIME = 25
UI_CYCLE_IMG_INSTANCE_TIME = 50
#end
#create instance
@require_POST
def create_image_index(request, img_obj_id):
    """
    :param request: request object
    :return view<'get_image_list OR prepare_manage/image_create.html'>: the corresponding view
    """
    form = CreateImageForm(request, request.POST.copy())
    if form.is_valid():
        data = form.cleaned_data
        if data['disk_format'] in ('ami', 'aki', 'ari',):
            container_format = data['disk_format']
        else:
            container_format = 'bare'
        kwargs = {
            'name': data['name'],
            'container_format': container_format,
            'disk_format': data['disk_format'],
            'min_disk': (data['min_disk'] or 0),
            'min_ram': (data["min_ram"] or 0),
            'is_public': data['is_public']
        }

        try:
            image_file = open(data['image_data'], 'rb')
            kwargs['data'] = image_file
            try:
                image_create = api.image_create(request, **kwargs)

            except Unauthorized:
                raise
            except Exception, exc:
                LOG.error('Image disk is not enough %s' % exc)
                return HttpResponse(jsonutils.dumps(
                    {"message": get_text('Image disk is not enough'),
                     "router_id": '', "statusCode": UI_RESPONSE_DWZ_SUCCESS}))
        except Exception, exc:
            LOG.error(
                'Can not open the software or image_file format wrong,%s !' % exc)

            return HttpResponse(jsonutils.dumps({"message": get_text(
                'Can not open the software or image_file format wrong !'),
                                                 "router_id": '',
                                                 "statusCode": UI_RESPONSE_DWZ_ERROR}))

        img_cre_time = UI_CYCLE_IMG_IMAGE_TIME
        while img_cre_time > PARAMETER_NUMBER_ZERO:
            img_status = api.glance.image_get(request, image_create.id)
            img_cre_time -= PARAMETER_NUMBER_ONE
            if img_status is None:
                LOG.error('Image is None:Failed')
            if img_status.status == UI_IMAGE_STATUS_ACTIVE:
                img_cre_time = PARAMETER_NEGATIVE_ONE
                break

            time.sleep(TIME_CHECK_PER_IMAGE_STATUS_SECONDS)

        if PARAMETER_NEGATIVE_ONE != img_cre_time:
            return HttpResponse(jsonutils.dumps(
                {"message": get_text('Image Created Failed'), "image_id": '',
                 "statusCode": UI_RESPONSE_DWZ_ERROR}))
        if img_obj_id is None or img_obj_id == "None":
            img_obj_id = 'None'
        else:
            obj = CreateInstancePrepare(uuid=img_obj_id)
            if obj.begin():
                pass
        return HttpResponse(
            jsonutils.dumps({"message": get_text('Image Created'),
                             "statusCode": UI_RESPONSE_OK,
                             "callbackType": 'closeCurrent',
                             "image_id": image_create.id,
                             "img_obj_id": img_obj_id}))

    else:
        return HttpResponse(jsonutils.dumps(
            {"message": get_text('Can not create image!'), "image_id": '',
             "statusCode": UI_RESPONSE_DWZ_ERROR}))


@require_GET
def create_image_page_suc(request, image_id, img_obj_id):
    return shortcuts.render(request, 'prepare_manage/image_create_suc.html',
                            {'img_obj_id': img_obj_id,
                             'image_id': image_id})


@require_POST
def create_instance_index(request, img_obj_id):
    """
    :param request: request object
    :return view<'instance_manage/create.html or index.html'>: if form has no
     error then create a new instance;else to the create template.
    """

    kwargs = {'flavor_list': Instance_Manage.views.flavor_list(request),
              'flavor_input_list': None,
              'keypair_list': Instance_Manage.views.keypair_list(request),
              'security_group_list': Instance_Manage.views.security_group_list(
                  request),
              'networks': Instance_Manage.views.network_list(request),
              'volume_list': Instance_Manage.views.volume_list(request)}
    form = LaunchForm(request, request.POST.copy(), **kwargs)
    _msg = ''

    user_id = None
    if 'user' in request.POST:
        user_id = request.POST['user']

    if form.is_valid():
        data = form.cleaned_data
        object_name = data['name']
        nam_len = len(object_name)
        ins_num = int(data['count'])
        if ins_num > 1 and nam_len > 13:
            object_name = object_name[0:13]
        try:
            dev_mapping = None
            networks = data['networks']
            if networks:
                nics = [{"net-id": net_id, "v4-fixed-ip": ""}
                        for net_id in networks]
            else:
                nics = None
            switch_tenants(request, data['tenant_id'])

            new_server = api.server_create(request,
                                           object_name,
                                           data['image_id'],
                                           data['flavor'],
                                           data.get('keypair'),
                                           normalize_newlines(
                                               data.get('user_data')),
                                           data.get('security_groups'),
                                           dev_mapping,
                                           nics=nics,
                                           instance_count=int(data.get('count'))
            )
            instance_id = new_server.id
            if Distribution.objects.filter(
                user_id=user_id).count() >= INSTANCE_LIMIT_PER_USER:
                _msg = _("Current user's instances reach limit %d.") % (
                    INSTANCE_LIMIT_PER_USER)
            else:
                _relationship = Distribution(instance_id=instance_id,
                                             user_id=user_id)
                try:
                    _relationship.save()
                except Exception, e:
                    LOG.error('create instance-user relationship failed.%s' % e)
                    _msg = _('Can not create instance-user relationship.')
            LOG.info('Instance "%s" launched.' % object_name)
            msg = get_text("Launch instance successfully!") + _msg
        except Unauthorized:
            raise
        except exceptions.OverLimit, e:
            msg = "The number of the instances exceed the quotas"
            LOG.error('The number of the instances exceed the quotas. %s' % e)
        except Exception, e:
            LOG.error('Unable to launch instance.%s' % e)
            msg = get_text('Unable to launch instance')
            return HttpResponse(jsonutils.dumps(
                {"message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR,
                 "callbackType": 'closeCurrent'}))
        if img_obj_id is None or img_obj_id == "image":
            LOG.info(msg)
            ## update
        else:
            obj = CreateInstancePrepare(uuid=img_obj_id)
            if obj.close():
                pass
        return HttpResponse(
            jsonutils.dumps({"message": msg, "callbackType": "closeCurrent",
                             "statusCode": UI_RESPONSE_DWZ_SUCCESS}))
    else:
        return HttpResponse(jsonutils.dumps(
            {"message": form.errors.as_text(),
             "statusCode": UI_RESPONSE_DWZ_ERROR}))


@require_GET
def update_project_quotas_form_index(request, tenant_obj_id):
    """
    :param request: request object
    :param tenant_id: id of the tenant
    :return view<'prepare_manage/update_project_quotas.html'>::show the form table for updating the tenant quotas
    """
    tenant_id = request.user.tenant_id
    form = UpdateQuotasForm(request, tenant_id)

    obj = CreateTenantResourcesShortagePrepare(uuid=tenant_obj_id)
    tenant_id = obj.tenant_id
    switch_tenants(request, tenant_id)
    if obj.status(request) == STATUS_CLOSED:
        return shortcuts.render(request, 'prepare_manage/info.html', {
            'message': get_text('The tenant quota has been updated')})
    if obj.begin():
        pass

    try:
        usages = tenant_quota_usages(request)
    except Unauthorized:
        raise
    except Exception, ex:
        LOG.error("usages not found ,the error is %s" % ex)
        usages = None
    return shortcuts.render(request,
                            'prepare_manage/update_project_quotas.html',
                            {'form': form, 'tenant_id': tenant_id,
                             'tenant_obj_id': tenant_obj_id, 'usages': usages})


@require_POST
def update_project_quotas_action_index(request, tenant_id, tenant_obj_id):
    """
    :param request: request object
    :param tenant_id: id of the tenant
    :return view<'get_project_list'>::update the tenant quotas successfully
            view<'prepare/update_project_quotas_suc.html'>::failed to update the tenant quotas
    """
    form = UpdateQuotasForm(request, tenant_id, request.POST)
    if form.is_valid():
        iRet, msg = handle_update_quotas(request, form.cleaned_data)
        if iRet:
            obj = CreateTenantResourcesShortagePrepare(uuid=tenant_obj_id)
            if obj.close():
                pass
            return HttpResponse(
                jsonutils.dumps(
                    {"message": get_text('Update Project Quotas Success'),
                     "callbackType": "closeCurrent",
                     "statusCode": UI_RESPONSE_DWZ_SUCCESS}))
        else:
            return HttpResponse(
                jsonutils.dumps(
                    {"message": get_text('Update Project Quotas Failed'),
                     "statusCode": UI_RESPONSE_DWZ_ERROR}))
    else:
        return HttpResponse(jsonutils.dumps(
            {"message": get_text('Update Project Quotas Failed'),
             "statusCode": UI_RESPONSE_DWZ_ERROR}))


@require_GET
def update_project_quotas_suc(request):
    return shortcuts.render(request,
                            'prepare_manage/update_project_quotas_suc.html')


def soft_wares_upload_success(request, sw_obj_id):
    obj = CreateFindSystemISOFilePrepare(uuid=sw_obj_id)
    if obj.end():
        pass

    return shortcuts.render(request, 'prepare_manage/upload_IOS_file.html',
                            {"sw_obj_id": sw_obj_id})


def volume_quotas_init_page(request, prepare_volume_id, page_id):
    tenant_id = request.user.tenant_id
    obj = CreateVolumePrepare(uuid=prepare_volume_id)
    if obj.begin():
        tenant_id = obj.tenant_id
        pass
    switch_tenants(request, tenant_id)
    try:
        usages = tenant_quota_usages(request)
    except Unauthorized:
        raise
    except Exception, ex:
        LOG.error("usages not found ,the error is %s" % ex)
        usages = None

    if page_id == 'update':
        form = UpdateQuotasForm(request, tenant_id)
        return shortcuts.render(request,
                                'prepare_manage/volume_quotas_update.html',
                                {'form': form, "usages": usages,
                                 'tenant_id': tenant_id,
                                 'prepare_volume_id': prepare_volume_id})
    if page_id == 'success':
        return shortcuts.render(request,
                                'prepare_manage/volume_quotas_update_suc.html',
                                {"tenant_id": tenant_id,
                                 "prepare_volume_id": prepare_volume_id})


def volume_quotas_tab_init(request, prepare_volume_id):
    tenant_id = request.user.tenant_id
    obj = CreateVolumePrepare(uuid=prepare_volume_id)
    tenant_id = obj.tenant_id
    switch_tenants(request, tenant_id)
    if obj.status(request) == STATUS_CLOSED:
        return shortcuts.render(request, 'prepare_manage/info.html', {
            'message': get_text(
                'The volume of the storage disk has been updated')})
    if obj.begin():
        pass
    tenant = api.keystone.tenant_get(request, tenant_id, admin=True)
    tenant_news = get_text(
        "The volume of the storage disk will be shortage(%s)") % tenant.name
    try:
        usages = tenant_quota_usages(request)
    except Unauthorized:
        raise
    except Exception, ex:
        LOG.error("usages not found ,the error is %s" % ex)
        usages = None

    return shortcuts.render(request, 'prepare_manage/volume_init.html',
                            {"usages": usages, "tenant_id": tenant_id,
                             "tenant_news": tenant_news,
                             "prepare_volume_id": prepare_volume_id})


@require_POST
def volume_quotas_update_action(request, tenant_id, prepare_volume_id):
    """
    :param request: request object
    :param tenant_id: id of the tenant
    :return failed to update the tenant quotas
    """
    form = UpdateQuotasForm(request, tenant_id, request.POST)
    if form.is_valid():
        iRet, msg = handle_update_quotas(request, form.cleaned_data)
        if iRet:
            obj = CreateVolumePrepare(uuid=prepare_volume_id)
            if obj.close():
                pass
            return HttpResponse(
                jsonutils.dumps(
                    {"message": get_text('Update Project Quotas Success'),
                     "callbackType": "closeCurrent",
                     "statusCode": UI_RESPONSE_DWZ_SUCCESS}))
        else:
            return HttpResponse(
                jsonutils.dumps({"message": get_text('Update Quotas Failed'),
                                 "statusCode": UI_RESPONSE_DWZ_ERROR}))
    else:
        return HttpResponse(jsonutils.dumps(
            {"message": get_text('Update Quotas Failed'),
             "statusCode": UI_RESPONSE_DWZ_ERROR}))


@require_GET
def create_node_in_volume(request, prepare_volume_id):
    """
    :param request:request Object
    :return:
    """
    form = NodeForm(request, None)
    obj = CreateVolumePrepare(uuid=prepare_volume_id)
    if obj.begin():
        pass
    return shortcuts.render(request, 'prepare_manage/volume_create_node.html',
                            {'form': form,
                             'prepare_volume_id': prepare_volume_id})


@require_POST
def create_node_form_action(request, prepare_volume_id):
    """
    :param request:request Object
    :return:
    """
    node_form = NodeForm(request, None, request.POST)
    if node_form.is_valid():
        data = node_form.cleaned_data
        created_at = datetime.now().utcnow()
        uuid = md5.new(str(created_at)).hexdigest()
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        control_nodes = Node.objects.filter(type='control_node')
        if control_nodes.__len__() > 0 and data['type'] == 'control_node':
            msg = get_text('control node has already exist')
            return HttpResponse(jsonutils.dumps(
                {"message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR}))

        try:
            node = Node(uuid=uuid, name=data['host_name'], ip=data['host_ip'],
                        type=data['type'], created_at=created_at)
            node.save()
        except IntegrityError:
            msg = get_text('IP %s has already exist') % data['ip']
            return HttpResponse(jsonutils.dumps(
                {"message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR}))

        except Exception, exp:
            debug_info = 'Can not create node,error is %s' % exp
            LOG.error(debug_info)
            msg = get_text('Create node failed, please retry later.')
            return HttpResponse(jsonutils.dumps(
                {"message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR}))

        obj = CreateVolumePrepare(uuid=prepare_volume_id)
        if obj.end():
            pass
        return HttpResponse(jsonutils.dumps(
            {"message": get_text("Create node Success"),
             "callbackType": 'closeCurrent',
             "statusCode": UI_RESPONSE_DWZ_SUCCESS}))
    else:
        return HttpResponse(
            jsonutils.dumps({"message": "Create Node Failed",
                             "statusCode": UI_RESPONSE_DWZ_ERROR}))


@require_POST
def launch_instance_index(request):
    """
    :param request: request object
    :return view<'instance_manage/create.html or index.html'>: if form has no
     error then create a new instance;else to the create template.
    """
    return Instance_Manage.views.create_instance(request)


@require_GET
def launch_form_image_index(request, image_id, img_obj_id, page_id):
    """
    :param request: request object
    :param image_id: the image id from which to launch a instance
    :return view<'instance_manage/instance_create.html'>: the from table to create
    instance
    """
    old_tenant_id = request.user.tenant_id
    kwargs = {
        'flavor_input_list': Instance_Manage.views.search_flavor_status(
            request),
        'flavor_list': Instance_Manage.views.flavor_list(request),
        'keypair_list': Instance_Manage.views.keypair_list(request),
        'security_group_list': Instance_Manage.views.security_group_list(
            request),
        'networks': Instance_Manage.views.network_list(request),
        'volume_list': Instance_Manage.views.volume_list(request)}

    switch_tenants(request, old_tenant_id)
    try:
        usages = tenant_quota_usages(request)
    except Exception, e:
        usages = None
        LOG.error('Can not get tenant usages. %s' % e)

    if page_id == 'image':
        form = LaunchForm(request, **kwargs)
        if img_obj_id is None or img_obj_id == 'None':
            img_obj_id = 'image'
        return shortcuts.render(request, 'prepare_manage/instance_create.html',
                                {'form': form,
                                 'oldtenantid': old_tenant_id, 'usages': usages,
                                 'image_id': image_id,
                                 'img_obj_id': img_obj_id})
    else:
        form = LaunchImagePrepareForm(request, **kwargs)

        return shortcuts.render(request,
                                'prepare_manage/image_create_and_instance.html',
                                {'form': form,
                                 'oldtenantid': old_tenant_id, 'usages': usages,
                                 'img_obj_id': img_obj_id})


@require_POST
def create_instance_action(request, img_obj_id):
    """
    :param request: request object
    :return view<'get_image_list OR image_template_manage/create.html'>: the corresponding view
    """
    kwargs = {
        'flavor_input_list': hard_Manage.views.search_flavor_status(request),
        'flavor_list': Instance_Manage.views.flavor_list(request),
        'keypair_list': Instance_Manage.views.keypair_list(request),
        'security_group_list': Instance_Manage.views.security_group_list(
            request),
        'networks': Instance_Manage.views.network_list(request),
        'volume_list': Instance_Manage.views.volume_list(request)}

    form = LaunchImagePrepareForm(request, request.POST.copy(), **kwargs)
    if form.is_valid():
        data = form.cleaned_data
        images, msg = create_image_thread(request, data)

        if not images:
            return  HttpResponse(jsonutils.dumps(
                {"message": get_text(msg),
                 "statusCode": UI_RESPONSE_DWZ_ERROR}))

        instance, msg = create_instance_thread(request, data, images)
        if not instance:
            return  HttpResponse(jsonutils.dumps(
                {"message": get_text(msg),
                 "statusCode": UI_RESPONSE_DWZ_ERROR}))

        if img_obj_id is None or img_obj_id == "None":
            ## update
            LOG.info(msg)
        else:
            obj = CreateInstancePrepare(uuid=img_obj_id)
            if obj.end():
                pass
        return HttpResponse(jsonutils.dumps(
            {"message": get_text(msg), "statusCode": UI_RESPONSE_DWZ_SUCCESS,
             "callbackType": "closeCurrent"}))
    else:
        return  HttpResponse(jsonutils.dumps(
            {"message": form.errors.as_text(),
             "statusCode": UI_RESPONSE_DWZ_ERROR}))


def create_image_thread(request, data):
    if data['disk_format'] in ('ami', 'aki', 'ari',):
        container_format = data['disk_format']
    else:
        container_format = 'bare'
    kwargs = {
        'name': data['name'],
        'container_format': container_format,
        'disk_format': data['disk_format'],
        'min_disk': (data['min_disk'] or 0),
        'min_ram': (data["min_ram"] or 0),
        'is_public': data['is_public']
    }

    try:
        image_file = open(data['image_data'], 'rb')
        kwargs['data'] = image_file
        try:
            image_create = api.image_create(request, **kwargs)

        except Unauthorized:
            raise
        except Exception, exc:
            msg = 'Image disk is not enough'
            LOG.error('Image disk is not enough %s' % exc)
            return None, msg
    except Exception, exc:
        msg = 'Can not open the software or image_file format wrong !'
        LOG.error(
            'Can not open the software or image_file format wrong,%s !' % exc)
        return None, msg

    img_cre_time = UI_CYCLE_IMG_IMAGE_TIME
    while img_cre_time > PARAMETER_NUMBER_ZERO:
        img_status = api.glance.image_get(request, image_create.id)
        img_cre_time -= PARAMETER_NUMBER_ONE
        if img_status is None:
            LOG.error('Image is None:Failed')
        if img_status.status == UI_IMAGE_STATUS_ACTIVE:
            img_cre_time = PARAMETER_NEGATIVE_ONE
            break

        time.sleep(TIME_CHECK_PER_IMAGE_STATUS_SECONDS)

    if PARAMETER_NEGATIVE_ONE != img_cre_time:
        msg = 'Image Create Timeout'
        return None, msg
    msg = 'Image Create Success'
    return image_create, msg


def create_instance_thread(request, data, img_status):
    user_id = None
    if 'user' in request.POST:
        user_id = request.POST['user']
    if data[
       'name_launch'] != '' and img_status.status == UI_IMAGE_STATUS_ACTIVE:
        try:
            if len(data['volume']) > PARAMETER_NUMBER_ZERO:
                if data['delete_on_terminate']:
                    delete_on_terminate = PARAMETER_NUMBER_ONE
                else:
                    delete_on_terminate = PARAMETER_NUMBER_ZERO
                dev_mapping = {data['device_name']: (
                    "%s::%s" % (data['volume'], delete_on_terminate))}
            else:
                dev_mapping = None
            networks = data['networks']
            if networks:
                nic_s = [{"net-id": net_id, "v4-fixed-ip": ""}
                         for net_id in networks]
            else:
                nic_s = None

            switch_tenants(request, data['tenant_id'])
            instance_test = api.server_create(request,
                                              data['name_launch'],
                                              img_status.id,
                                              data['flavor'],
                                              data.get('keypair'),
                                              normalize_newlines(
                                                  data.get('user_data')),
                                              data.get('security_groups'),
                                              dev_mapping, nics=nic_s,
                                              instance_count=data.get(
                                                  'count'))

            if user_id:
                if Distribution.objects.filter(
                    user_id=user_id).count() >= INSTANCE_LIMIT_PER_USER:
                    _msg = _("Current user's instances reach limit %d.") % (
                        INSTANCE_LIMIT_PER_USER)
                else:
                    _relationship = Distribution(instance_id=instance_test.id,
                                                 user_id=user_id)
                    try:
                        _relationship.save()
                    except Exception, e:
                        LOG.error(
                            'create instance-user relationship failed.%s' % e)

            if_con = UI_CYCLE_IMG_INSTANCE_TIME
            while if_con > PARAMETER_NUMBER_ZERO:
                instance = api.server_get(request, instance_test.id)
                if_con -= PARAMETER_NUMBER_ONE
                if instance.status == UI_INSTANCE_STATUS_ACTIVE:
                    if_con = PARAMETER_NEGATIVE_ONE
                    break
                if instance.status == UI_INSTANCE_STATUS_ERROR:
                    if_con = PARAMETER_NEGATIVE_TWO
                    break
                if instance.status == UI_INSTANCE_STATUS_RESOURCE_IS_NOT_ENOUGH:
                    if_con = PARAMETER_NEGATIVE_THREE
                    break
                time.sleep(TIME_CHECK_PER_IMAGE_STATUS_SECONDS)

            if PARAMETER_NEGATIVE_THREE == if_con:
                try:
                    image = api.glance.image_get(request, img_status.id)
                    image.delete()
                except Unauthorized:
                    raise
                except Exception, exc:
                    msg = _('Can not delete image !')
                    LOG.error('%s,%s' % (msg, exc))
                return None, 'Instance resource is not enough'

            if PARAMETER_NEGATIVE_TWO == if_con:
                try:
                    image = api.glance.image_get(request, img_status.id)
                    image.delete()
                except Unauthorized:
                    raise
                except Exception, exc:
                    msg = _('Can not delete image !')
                    LOG.error('%s,%s' % (msg, exc))
                return None, 'Instance Create Failed'

            if PARAMETER_NEGATIVE_ONE != if_con:
                return None, 'Instance Create Timeout'
            LOG.info('Instance "%s" launched.' % data["name"])
            return instance_test, 'Instance Create Success'
        except Unauthorized:
            raise
        except exceptions.OverLimit, exc:
            LOG.error('Over the limit,%s' % exc)
            return None, 'Over the limit'
        except Exception, exc:
            LOG.error('Unable to launch instance: %s' % exc)
            return None, 'Unable to launch instance'


def get_service_resource_info(request, resource_id):
    try:
        facility_list = api.nova.get_hypervisors_list(request)
        kwargs = {'instance_id': None,
                  'compute_list': facility_list
        }
        form = InstanceLiveMigratePrepare(**kwargs)

        obj = CreateServerResourceShortagePrepare(uuid=resource_id)
        if obj.begin():
            pass

        return shortcuts.render(request,
                                'prepare_manage/volume_migration.html',
                                {"form": form, "resource_id": resource_id})


    except Unauthorized:
        raise
    except Exception, e:
        LOG.error('Can not get hypervisors statistics , error is %s' % e)
        return HttpResponse('Not Found')


from netaddr import *

@require_GET
def get_instance_and_host(request):
    host_id = None
    if "host_id" in request.GET:
        host_id = request.GET['host_id']
    hardware = []
    if host_id != '':
        facility_list = api.nova.get_hypervisors_list(request)
        for facility in facility_list:
            if facility.hypervisor_hostname == host_id:
                hardware.append(facility)
                break
    instances = api.nova.server_list(request, all_tenants=True)
    instance_list = []

    for instance in instances:
        if host_id != getattr(instance, 'OS-EXT-SRV-ATTR:host', 'None'):
            instance_list.append(instance)

    total = 0
    sub_net_ids = []
    used = 0
    if host_id != '':
        floating_pools = api.network.floating_ip_pools_list(request)

        for pool in floating_pools:
            for sub_net_id in pool.subnets:
                sub_net_ids.append(
                    sub_net_id)    # all subnet ids in floating_pools
                sub_net = api.quantum.subnet_get(request, sub_net_id)
                for allocation_pool in sub_net.allocation_pools:
                    start = IPAddress(allocation_pool.get("start")).value
                    end = IPAddress(allocation_pool.get("end")).value
                    total += end - start

        ports = api.quantum.port_list(request)
        for port in ports:
            for ip in port.fixed_ips:
                if ip["subnet_id"] in sub_net_ids:
                    used += 1

    return shortcuts.render(request,
                            'prepare_manage/qutoa_pro_bar.html',
                            {"instance_list": instance_list,
                             "hardware": hardware[0], 'ips_used': used,
                             'ips_total': total})


@require_GET
def get_instance_status(request):
    instance_id = None
    if 'instance_id' in request.GET:
        instance_id = request.GET['instance_id']
    try:
        instance = api.server_get(request, instance_id)
    except Unauthorized:
        raise
    except exceptions.ClientException:
        return HttpResponse(content=instance_id,
                            status=UI_RESPONSE_NOTFOUND)
    return HttpResponse(
        jsonutils.dumps({'instance_status': getattr(instance, 'status',
                                                    'None')}))


@require_POST
def handle_instance_migrate(request, resource_id):
    """
    :param request: request object
    :param instance_id: the instance id
    :return view: after live migration return instance list
    """
    form = InstanceLiveMigratePrepareForm(request.POST.copy())
    if form.is_valid():
        data = form.cleaned_data
        host_name = data['host']
        instance = Instance_Manage.views.get_instance_show_data(request, data[
                                                                         'instance_id'])
        task = getattr(instance, 'OS-EXT-STS:task_state', None)
        if instance and instance.status == 'ACTIVE' and task in (
            None, 'No Valid Host'):
            try:
                api.nova.server_live_migrate(request, data['instance_id'],
                                             host_name,
                                             block_migration=True,
                                             disk_over_commit=False)
                msg = get_text('Live migrate instance successfully!')
            except Unauthorized:
                raise
            except Exception, e:
                msg = get_text('Can not live migrate the instance')
                LOG.error('Can not live migrate the instance. %s' % e)
                return HttpResponse(jsonutils.dumps(
                    {"message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR}))

            obj = CreateServerResourceShortagePrepare(uuid=resource_id)
            if obj.end():
                pass
            return HttpResponse(jsonutils.dumps(
                {'message': msg, "statusCode": UI_RESPONSE_DWZ_SUCCESS,
                 "callbackType": "closeCurrent"}))
        else:
            msg = get_text(
                'Can not live migrate the instance,its status is not active'\
                ' or task is not None')
            return HttpResponse(jsonutils.dumps(
                {"message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR}))
    else:
        return HttpResponse(jsonutils.dumps(
            {"message": form.errors.as_text(),
             "statusCode": UI_RESPONSE_DWZ_ERROR}))


def instance_migrate_suc(request):
    return shortcuts.render(request, "prepare_manage/volume_migration_suc.html")


@require_GET
def software_download_in_prepare(request):
    """
    Get binary file of Software with uuid
    :param request:
    :param software_uuid:
    :return:
    """
    filename = settings.DOC_FILE
    download_path = os.path.join(settings.DOC_ROOT, filename)
    if os.path.isfile(download_path):
        wrapper = FileWrapper(file(download_path))
        response = HttpResponse(wrapper)
        response['Content-Length'] = os.path.getsize(download_path)
        response['Content-Type'] = 'application/octet-stream'
        response['Content-Encoding'] = 'utf-8'

        browser = request.META.get('HTTP_USER_AGENT', '')
        if browser.find("MSIE") != -1:
            filename = filename
        else:
            filename = filename
        response['Content-Disposition'] = 'attachment; filename=%s' % filename

        return response
    else:
        return HttpResponse(jsonutils.dumps(
            ui_response(message=get_text('Binary file does not exist!'))))


@require_GET
def start_image_launch_instance(request, img_obj_id):
    """
    :param request: request object
    :param image_id: the image id from which to launch a instance
    :return view<'prepare_manage/image_start_instance.html'>: the from table to create
    instance
    """
    old_tenant_id = request.user.tenant_id
    kwargs = {
        'flavor_input_list': Instance_Manage.views.search_flavor_status(
            request),
        'flavor_list': Instance_Manage.views.flavor_list(request),
        'keypair_list': Instance_Manage.views.keypair_list(request),
        'security_group_list': Instance_Manage.views.security_group_list(
            request),
        'networks': Instance_Manage.views.network_list(request),
        'volume_list': Instance_Manage.views.volume_list(request)}

    try:
        usages = tenant_quota_usages(request)
    except Exception, e:
        usages = None
        LOG.error('Can not get tenant usages. %s' % e)

    image_list = get_images_data(request)
    form = LaunchForm(request, **kwargs)
    if img_obj_id is None or img_obj_id == 'None':
        img_obj_id = 'image'
        role = get_user_role_name(request)
        need_to_do = NeedToDo.objects.filter(role=role,
                                             category=IMAGE_TEMPLATE_MANAGE)
        if len(need_to_do) > 0:
            img_obj_id = need_to_do[0].need_uuid
            obj = CreateVirtualRouterPrepare(uuid=img_obj_id)
            if obj.begin():
                old_tenant_id = obj._obj.tenant_id
                pass
    else:
        obj = CreateInstancePrepare(uuid=img_obj_id)
        if obj.status(request) == STATUS_CLOSED:
            return shortcuts.render(request, 'prepare_manage/info.html', {
                'message': get_text('You have to create a instance')})
        old_tenant_id = obj._obj.tenant_id
        if obj.begin():
            pass
    switch_tenants(request, old_tenant_id)
    return shortcuts.render(request, 'prepare_manage/image_start_instance.html',
                            {'form': form,
                             'oldtenantid': old_tenant_id, 'usages': usages,
                             'img_obj_id': img_obj_id,
                             'image_list': image_list})


def create_image_disk_and_ram(request):
    if 'image_id' in request.GET:
        image_id = request.GET['image_id']
        try:
            image = api.glance.image_get(request, image_id)
            return HttpResponse(jsonutils.dumps(
                {"message": get_text('Can not export logs'),
                 "statusCode": UI_RESPONSE_DWZ_SUCCESS,
                 'img_disk': image.min_disk, 'img_ram': image.min_ram}))
        except Unauthorized:
            raise
        except Exception, exc:
            LOG.error('error is %s.' % exc)

    return HttpResponse(
        jsonutils.dumps({"message": '', "statusCode": UI_RESPONSE_DWZ_ERROR,
                         'img_disk': '', 'img_ram': ''}))


def list_log(request):
    role = get_user_role_name(request)
    log_lists = LoggingAction.objects.order_by('-create_at').all()
    logs = len(log_lists)
    tenant_id = request.user.tenant_id
    if logs >= 500:
        need_to_do = NeedToDo.objects.filter(role=role, category=LOG_MANAGE)
        need1 = need_to_do.filter(status=STATUS_NEW)
        need2 = need_to_do.filter(status=STATUS_DOING)
        if len(need1) == 0 and len(need2) == 0:
            obj = CreateLogItemToLargePrepare(None, role, tenant_id, None,
                                              str(logs), '')
            if obj.renew():
                pass


def tenant_list(request):
    projects = api.tenant_list(request, admin=True)
    role = get_user_role_name(request)
    try:
        for project in projects:
            para = ''
            tenant = None
            tenant_id = None
            usages = None
            tenant_id = project.tenant_id
            tenant_name = project.name
            switch_tenants(request, tenant_id)
            usages = quotas.tenant_quota_usages(request)

            if usages is not None:
                if get_usages_attribute(usages['cores']):
                    para += 'VCPUs' + ','
                if get_usages_attribute(usages['instances']):
                    para += 'Instances' + ','
                if get_usages_attribute(usages['volumes']):
                    para += 'Volumes' + ','
                if get_usages_attribute(usages['gigabytes']):
                    para += 'Disk Volume' + ','
                    need_to_do = NeedToDo.objects.filter(role=role,
                                                         tenant_id=tenant_id,
                                                         category=VOLUME_MANAGE)
                    need1 = need_to_do.filter(status=STATUS_NEW)
                    need2 = need_to_do.filter(status=STATUS_DOING)
                    if len(need1) == 0 and len(need2) == 0:
                        obj_volume = CreateVolumePrepare(None, role, tenant_id,
                                                         None, str(tenant_name),
                                                         str(
                                                             usages[
                                                             'gigabytes'][
                                                             'used']) + '/' + str(
                                                             usages[
                                                             'gigabytes'][
                                                             'quota']))
                        if obj_volume.renew():
                            pass

                if get_usages_attribute(usages['ram']):
                    para += 'RAM' + ','
                if get_usages_attribute(usages['floating_ips']):
                    para += 'Floating IPs'

            if len(para) > 0:
                need_to_do = NeedToDo.objects.filter(role=role,
                                                     tenant_id=tenant_id,
                                                     category=PROJECT_MANAGE_RESOURCE)
                need1 = need_to_do.filter(status=STATUS_NEW)
                need2 = need_to_do.filter(status=STATUS_DOING)
                if len(need1) == 0 and len(need2) == 0:
                    obj_resource = CreateTenantResourcesShortagePrepare(None,
                                                                        role,
                                                                        tenant_id,
                                                                        None,
                                                                        str(
                                                                            tenant_name),
                                                                        para)
                    if obj_resource.renew():
                        pass
    except Exception, exc:
        LOG.info('Error is :%s' % exc)
        pass


def get_usages_attribute(usages_attr):
    used = usages_attr['used']
    quota = usages_attr['quota']
    if used != 0 and used / (quota * 1.0) > 0.5:
        return True
    return False


def rate_server_resource(facility):
#    instance_name = facility.hypervisor_hostname
    server_str = ''
    memory_mb = facility.memory_mb * 1.5
    memory_mb_used = facility.memory_mb_used
    local_gb_used = facility.local_gb_used
    local_gb = facility.local_gb
    memory_mb_per = int((memory_mb_used * 100) / memory_mb)
    local_gb_per = int((local_gb_used * 100) / local_gb)
    instance_online = getattr(facility, 'num_vm_active', 0)
    num_instances = getattr(facility, 'num_instances', 0)
    cpu_use = facility.cpu_usage
    if cpu_use > 10:
        server_str += 'CPU'

    if memory_mb_per > 10:
        if len(server_str) > 0:
            server_str += ',Memory'
        else:
            server_str += 'Memory'
    if local_gb_per > 10:
        if len(server_str) > 0:
            server_str += ',Disk'
        else:
            server_str += 'Disk'

    return server_str


def get_server_resource(request):
    try:
        role = get_user_role_name(request)
        facility_list = api.nova.get_hypervisors_list(request)
        switch_tenants(request, request.user.tenant_id)
        for facility in facility_list:
            instance_name = facility.hypervisor_hostname

            resource_para = rate_server_resource(facility)
            if len(resource_para) > 0:
                need_to_do = NeedToDo.objects.filter(role=role,
                                                     parameters__contains=instance_name,
                                                     category=INSTANCE_RESOURCE)

                if len(need_to_do) == 0:
                    obj = CreateServerResourceShortagePrepare(None,
                                                              role,
                                                              request.user.tenant_id,
                                                              None,
                                                              str(
                                                                  instance_name),
                                                              str(
                                                                  resource_para))
                    if obj.renew():
                        pass

    except Unauthorized:
        raise
    except Exception, e:
        LOG.error('Can not get hypervisors list , error is %s' % e)


@require_GET
def prepare_list_info(request):
    try:
    #        get_server_resource(request)
    #        tenant_list(request)
    #        list_log(request)
    #        prepare_software_list(request)
        prepare = PrepareListThread(request)
        prepare.start()

        json_obj = {"status": '200'}
        return HttpResponse(jsonutils.dumps(json_obj))
    except Unauthorized:
        raise
    except Exception, exc:
        LOG.error('Can not get hypervisors statistics , error is %s' % exc)
        return HttpResponse('Not Found')

import threading

class PrepareListThread(threading.Thread):
    objs = {}
    objs_locker = threading.Lock()

    def __init__(self, request):
        threading.Thread.__init__(self)
        self.request = request

    def __new__(cls, *args, **kwargs):
        if cls in cls.objs:
            return cls.objs[cls]['obj']

        cls.objs_locker.acquire()
        try:
            if cls in cls.objs:
                return cls.objs[cls]['obj']
            obj = object.__new__(cls)
            cls.objs[cls] = {'obj': obj}

            return cls.objs[cls]['obj']
        finally:
            cls.objs_locker.release()

    @classmethod
    def decorate_init(cls, fns):
        def init_wrap(*args):
            if not cls.objs[cls]['init']:
                fns(*args)
                cls.objs[cls]['init'] = True
            return

        return init_wrap

    def run(self):
        try:
            get_server_resource(self.request)
            tenant_list(self.request)
            list_log(self.request)
            prepare_software_list(self.request)
        except Exception, exc:
            LOG.info(exc)

        return

from dashboard.software_manage.models import Software

def prepare_software_list(request):
    soft_wares = []
    need_to_do = []
    try:
        soft_wares = Software.objects.filter(file_name__contains='.iso',
                                             classify='SystemSoftware',
                                             status='Active').order_by(
            'created_at')
        role = get_user_role_name(request)
        need_to_do = NeedToDo.objects.filter(role=role,
                                             category=SOFTWARE_MANAGE)
        need_list = []
        for nd in need_to_do:
            para = nd.parameters[2:-2].split("', '")[0]
            need_list.append(para)

        for sw in soft_wares:
            created_at = sw.created_at + abs(datetime.now() - datetime.utcnow())
            sw_name = sw.name
            sw_date = datetime.date(created_at)
            date_now = datetime.date(datetime.now())
            if sw_date == date_now:
                if sw_name not in need_list:
                    obj = CreateFindSystemISOFilePrepare(None, role,
                                                         request.user.tenant_id,
                                                         None, str(sw_name), '')

    except Exception, e:
        LOG.error('Can not get list of softwares. %s' % e)

#==========================================================================================================
###check manage####

from dashboard.check_manage.models import Task
from dashboard.check_manage.forms import *


@require_GET
def get_check_list(request):
    task_list = []
    try:
        tasks = Task.objects.filter(user_id=request.user.id).order_by('submit_time')
#        task = Task.objects.all().order_by('level')
        for task in tasks:
            if task.status == 0:
                setattr(task, 'status', 'Pending')
            elif task.status == 1:
                setattr(task, 'status', 'Approve')
            elif task.status == 2:
                setattr(task, 'status', 'Expired')
            task_list.append(task)
        return shortcuts.render(request, "prepare_manage/task_item.html",
                                {"task_list": task_list[:6]})
    except Exception, exc:
        LOG.error('Error is :%s' % exc)

        return shortcuts.render(request, "prepare_manage/task_item.html",
                                {"task_list": task_list[:6]})


@require_GET
def task_action(request, task_id, type='reject'):
    if type == 'reject':
        return reject_task(request, task_id)
    elif type == 'edit':
        return update_task(request, task_id)
    elif type == 'delete':
        return shortcuts.render(request,
                                'prepare_manage/task_delete.html',
                                {'task_id': task_id})
    elif type == 'resume':
        return shortcuts.render(request,
                                'prepare_manage/task_resubmit.html',
                                {'task_id': task_id})


@require_GET
def reject_task(request, task_id):
    try:
        task = Task.objects.filter(id=task_id)
        if len(task) > 0:
            task = task[0]
        else:
            task = None
        return shortcuts.render(request, "prepare_manage/task_edit.html",
                                {"task": task})
    except Exception, exc:
        LOG.error('Error is %s' % exc)

    return shortcuts.render(request, "prepare_manage/task_edit.html",
                            {"task": task})



@require_POST
def delete_task(request, task_id):
    try:
        task = Task.objects.filter(id=task_id)
        task.delete()


        return HttpResponse({"message": "delete role success",
                             "statusCode": UI_RESPONSE_OK,
                             "object_name": getattr(task, 'name', '')},
                            status=UI_RESPONSE_OK)
    except Unauthorized:
        raise
    except Exception, exc:
        LOG.error('Error is %s' % exc)
        return HttpResponse({"message": 'resume role failed.',
                             "statusCode": UI_RESPONSE_DWZ_ERROR,
                             "object_name": getattr(task, 'name', '')},
                            status=UI_RESPONSE_ERROR)


@require_GET
def update_task(request, task_id):
    try:
        task = Task.objects.filter(id=task_id)
        if len(task) > 0:
            task = task[0]
            if task.status == 0:
                setattr(task, 'status', 'Pending')
            elif task.status == 1:
                setattr(task, 'status', 'Approve')
            elif task.status == 2:
                setattr(task, 'status', 'Expired')
        else:
            task = None
        return shortcuts.render(request, "prepare_manage/task_edit.html",
                                {"task": task})
    except Exception, exc:
        LOG.error('Error is %s' % exc)

    return shortcuts.render(request, "prepare_manage/task_edit.html",
                            {"task": task})

def resume_task(request):
    try:
        form = TaskCheckForm(request,request.POST)
        if form.is_valid():
            data = form.clean_data
            task_id = data['task_id']
            task = Task.objects.get(id=task_id)
            task.check_comment = data['check_comment']
            task.save()
            return HttpResponse({"message": "delete role success",
                                 "statusCode": UI_RESPONSE_OK,
                                 "object_name": getattr(task, 'name', '')},
                                status=UI_RESPONSE_OK)

    except Unauthorized:
        raise
    except Exception, exc:
        LOG.error('Error is %s' % exc)

    return HttpResponse({"message": 'resume role failed.',
                             "statusCode": UI_RESPONSE_DWZ_ERROR,
                             "object_name": getattr(task, 'name', '')},
                            status=UI_RESPONSE_ERROR)