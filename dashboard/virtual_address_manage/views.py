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


__author__ = 'lishiquan'
__date__ = '2013-06-08'
__version__ = 'v2.0.9'

from django.conf import settings

if settings.DEBUG:
    __log__ = 'v2.0.9 create'

import logging
LOG = logging.getLogger(__name__)

#    code begin
from netaddr import *

from django import shortcuts
from django.views.decorators.http import require_GET , require_POST, require_http_methods
from django.http import HttpResponse
from django.utils.datastructures import SortedDict
from .forms import AllocateIPForm , AssociateIPForm

from dashboard import api
from dashboard.authorize_manage.utils import switch_tenants
from dashboard.exceptions import Unauthorized
from dashboard.exceptions import LicenseForbidden
from dashboard.utils import jsonutils , UIResponse , Pagenation
from dashboard.utils.i18n import get_text
from dashboard.utils.ui import *


def get_source(rule):
    """
    :param rule:rule object
    :return:cidr of rule
    """
    if 'cidr' in rule.ip_range:
        return rule.ip_range['cidr'] + ' (CIDR)'
    elif 'name' in rule.group:
        return rule.group['name']
    else:
        return None

def getQuotasItem(obj, item_name, default):
    return_val = default
    if obj and obj != {}:
        try:
            item_value = obj[item_name]
            if item_value:
                return_val = item_value
        except Exception, exe:
            LOG.exception("getQuotasItem,the error is %s "
                          % exe.message)
    return return_val

@require_GET
@Pagenation('virtual_address_manage/floatingIpsIndex.html')
def get_floating_ips_list(request , tenant_id):
    """
    :param request:request object,tenant_id
    :return:view<'virtual_address_manage/floatingIpsIndex.html'>::list of floatingIp
    """
    args = {}
    floating_ips = []
    floating_pool = {}
    floatingips = []
    try:
        if None != switch_tenants(request , tenant_id):
            floating_ips = api.network.tenant_floating_ip_list(request)
            floating_pools = api.network.floating_ip_pools_list(request)
            floating_pool = SortedDict([(pool.id , pool.name) for pool in
                                      floating_pools])


        for floating_ip in floating_ips:
            if tenant_id == floating_ip.tenant_id :
                floating_ip._apidict['pool'] = floating_pool.get(floating_ip.pool,
                                                                get_text("invalid ip pool"))
                floatingips.append(floating_ip)

        instances = []
        tenant_quota = api.nova.nova_tenant_quota_get(request , tenant_id)
        for item in tenant_quota:
            if item.name == "floating_ips":
                ip_num = item.limit
        servers = api.server_list(request)
        for server in servers:
        # to be removed when nova can support unique names
            server_name = server.name
            if any(s.id != server.id and
                   s.name == server.name for s in servers):
                # duplicate instance name
                server_name = "%s [%s]" % (server.name, server.id)
            instances.append((server.id , server_name))
    except Unauthorized:
        raise
    except Exception , exe:
        LOG.exception("ClientException in floating ip index,the error is %s "
                      % exe.message)

    args['list'] = floatingips
    args['floatingiplist'] = floatingips
    args['exceed'] = len(floatingips) >= ip_num     # If the num of floating ips that    allocated is exceeded.
    args['tenant_id'] = tenant_id
    args['ip_num'] = ip_num
    args['instances'] = instances

    return args

@require_GET
def get_floatingip_count_info(request):
    """
    get the total count of floating ip and the count of used ips
    :param request:
    :return:
    """

    try:
        vip_per = 0
        total = 0
        subnet_ids = []
        used = 0

        floating_pools = api.network.floating_ip_pools_list(request)

        for pool in floating_pools:
            for subnet_id in pool.subnets:
                subnet_ids.append(subnet_id)    # all subnet ids in floating_pools
                subnet = api.quantum.subnet_get(request,subnet_id)
                for allocation_pool in subnet.allocation_pools:
                    start = IPAddress(allocation_pool.get("start")).value
                    end = IPAddress(allocation_pool.get("end")).value
                    total += end - start

        ports = api.quantum.port_list(request)
        for port in ports:
            for ip in port.fixed_ips:
                if ip["subnet_id"] in subnet_ids:
                    used += 1

        if total != 0 :
            vip_per = (used * 100) / total

        json_obj = {"vip_per": vip_per}
        return HttpResponse(jsonutils.dumps(json_obj))
    except Unauthorized:
        raise
    except Exception , exe:
        LOG.exception("Cann't get the percent of used floating ip for home page,the error is %s "
                      % exe.message)
        return HttpResponse('Not Found')

@require_GET
def get_floating_ips_address(request):
    """
    :param request:request object
    :return:view<'virtual_address_manage/index_ip.html'>::list of tenants
    """
    return shortcuts.render(request, 'virtual_address_manage/index_ip.html')

@require_GET
def get_securitygroup_ips_list(request):
    """
    :param request:request object
    :return:json :the tree of floatingip
    """
    project_menus = []
    projects = []
    try:
        projects = api.tenant_list(request, admin=True)
    except Unauthorized:
        raise
    except Exception , exe:
        LOG.error('Unable to retrieve project list,%s.' % exe)
    for project in projects:
        project_floating_ips = []
        if project.enabled and None != switch_tenants(request , project.id):
            floating_ips = api.tenant_floating_ip_list(request)
            if floating_ips:
                for floating in floating_ips:
                    if floating.tenant_id == project.id:
                        floating_obj = {
                            'floating_ip':floating.ip,
                            'floating_id':floating.id
                        }
                        project_floating_ips.append(floating_obj)
        project_menu = {
            'project_name': project.name,
            'project_id': project.id,
            'project_enabled': project.enabled,
            'project_floating': project_floating_ips
        }
        project_menus.append(project_menu)
    try:
        return HttpResponse(jsonutils.dumps(project_menus))
    except  Exception , exe:
        LOG.error('return HttpResponse error,%s.' % exe)
        return HttpResponse('Not Found')

@require_GET
def get_floating_ips_odd(request, tenant_id, floating_ip):
    """
    :param request:request object,tenant_id, floating_ip
    :return:view<'virtual_address_manage/floatingIpsIndex_ip.html'>::list of floatingip
    """
    float_ip = []
    floating_pool = {}
    floating_ips = None
    try:
        if None != switch_tenants(request , tenant_id):
            float_ip = api.tenant_floating_ip_list(request)
            floating_pools = api.network.floating_ip_pools_list(request)
            floating_pool = SortedDict([(pool.id , pool.name) for pool in
                                      floating_pools])

        for floating in float_ip:
            if floating.ip == floating_ip:
                floating_ips = floating
                break

        if floating_pool:
            floating_ips._apidict['pool'] = floating_pool.get(floating_ips.pool,
                                                        get_text("invalid ip pool"))
    except Unauthorized:
        raise
    except Exception , exe:
        LOG.exception("ClientException in floating ip index,the error is %s" % exe.message)

    instances = []
    servers = []
    try:
        servers = api.server_list(request)
    except Unauthorized:
        raise
    except Exception , exe:
        LOG.error('Unable to retrieve instance list.the error is %s ' % exe.message)

    for server in servers:
        # to be removed when nova can support unique names
        server_name = server.name
        if any(s.id != server.id and
               s.name == server.name for s in servers):
            # duplicate instance name
            server_name = "%s [%s]" % (server.name, server.id)
        instances.append((server.id , server_name))
    return shortcuts.render(request, 'virtual_address_manage/floatingIpsIndex_ip.html',
                {"floatingIp":floating_ips, "tenant_id":tenant_id, "instances":instances})


@require_GET
def allocate_ip_index(request , tenant_id):
    """
    :param request:request object,tenant_id
    :return:view<'virtual_address_manage/allocate_ip.html'>
    """
    form = AllocateIPForm(request)
    return shortcuts.render(request , 'virtual_address_manage/allocate_ip.html' ,
                                                {'form': form, 'tenant_id':tenant_id})

@check_permission('Allocate IP To Project')
@require_POST
@UIResponse('Virtual Address Manage', 'get_floating_ips_address')
def allocate_ip_action(request , tenant_id):
    """
    :param request:request object,tenant_id
    :return:view<'virtual_address_manage/index_ip.html'>
    """
    form =  AllocateIPForm(request , request.POST)
    if form.is_valid():
        data = form.cleaned_data
        switch_tenants(request , tenant_id)
        try:
            fip = api.network.tenant_floating_ip_allocate(request ,
                pool = data.get('pool' , None))
        except Unauthorized:
            raise
        except LicenseForbidden:
            raise
        except Exception , exe:
            msg = 'Unable to allocate this ip pool.'
            LOG.error('Unable to allocate this ip pool.the error is %s ' % exe.message)
            return HttpResponse({"message":msg , "statusCode":UI_RESPONSE_DWZ_ERROR} , status = UI_RESPONSE_ERROR)
        try:
            tenant_old = api.keystone.tenant_get(request , tenant_id , admin=True)
        except Unauthorized:
            raise
        except Exception , exe:
            LOG.error('get tenant error.the error is %s ' % exe.message)
        return HttpResponse({"message":"Allocate IP successfully!",
                             "statusCode":UI_RESPONSE_DWZ_SUCCESS , "object_name":'Floating IP %s  project %s'
                                % (fip.ip, getattr(tenant_old,'name','unknown'))} , status=UI_RESPONSE_DWZ_SUCCESS)
    else:
        return HttpResponse({"form":form, "message":"", "statusCode":UI_RESPONSE_DWZ_ERROR} ,
                                status=UI_RESPONSE_ERROR)


@require_GET
def associate_ip_index(request , ip_id):
    """
    :param request:request object,ip_id
    :return:view<'virtual_address_manage/associate_ip.html'>
    """

    form = AssociateIPForm(request , ip_id)

    tenant_id = getattr(request.user ,'tenant_id',None)

    return shortcuts.render(request , 'virtual_address_manage/associate_ip.html' ,
                                {'form': form,'ip_id':ip_id,'tenant_id':tenant_id})

@check_permission('Associate IP')
@require_POST
@UIResponse('Virtual Address Manage', 'get_floating_ips_address')
def associate_ip_action(request , ip_id):
    """
    :param request:request object,ip_id
    :return:view<'virtual_address_manage/index_ip.html'>
    """

    form =  AssociateIPForm(request , ip_id , request.POST)
    if form.is_valid():
        data = form.cleaned_data
        instance_old = api.server_get(request , data['instance_id'])
        try:

            q_instance_id = data['instance_id']
            if q_instance_id:
                target_id = api.network.floating_ip_target_get_by_instance(
                                request, q_instance_id)

            api.network.floating_ip_associate(request , ip_id , target_id)
            msg = get_text('Successfully associated Floating IP %(ip)s with Instance: %(inst)s') \
                            % {"ip": data['floating_ip'], "inst": data['instance_id']}
        except Unauthorized:
            raise
        except Exception , exe:
            if exe.message.find('fixed IP already has a floating IP on external network') != -1:
                msg = get_text('Error associated Floating IP %(ip)s with Instance %(inst)s, as that the instance already has a floating IP.')\
                      % {"ip": data['floating_ip'], "inst": getattr(instance_old , 'name' , 'unknown')}
            else:
                msg = get_text('Error associated Floating IP %(ip)s with Instance %(inst)s, please create a router with external interfaces for the subnet that the instance was in.') \
                    % {"ip": data['floating_ip'], "inst": getattr(instance_old , 'name' , 'unknown')}
            LOG.error('Error associated Floating IP %(ip)s with Instance %(inst)s .The error is %(e)s'
                      % {"ip": data['floating_ip'], "inst": getattr(instance_old , 'name' , 'unknown') , "e":exe.message})
            return HttpResponse({"message":msg , "statusCode":UI_RESPONSE_DWZ_ERROR} , status = UI_RESPONSE_ERROR)
        return HttpResponse({"message":msg , "statusCode":UI_RESPONSE_DWZ_SUCCESS ,
                             "object_name":(' Floating IP %(ip)s Instance %(inst)s')
                                % {"ip": data['floating_ip'], "inst": getattr(instance_old,'name', 'unknown')}} ,
                                status = UI_RESPONSE_DWZ_SUCCESS)
    else:
        return HttpResponse({"form":form , "message":"",
                             "statusCode":UI_RESPONSE_DWZ_ERROR} , status = UI_RESPONSE_ERROR)



@require_GET
def release_ip_index(request , ip_id):
    """
    :param request:request object,ip_id
    :return:view<'virtual_address_manage/release_ip.html'>
    """
    return shortcuts.render(request , 'virtual_address_manage/release_ip.html' , {'ip_id':ip_id})

@check_permission('Release Floating IP')
@require_http_methods(['DELETE'])
@UIResponse('Virtual Address Manage', 'get_floating_ips_address')
def release_ip_action(request , ip_id):
    """
    :param request:request object,ip_id
    :return:view<'virtual_address_manage/index_ip.html'>
    """
    try:
        release_ip = api.tenant_floating_ip_get(request , ip_id)
    except Unauthorized:
        raise
    except Exception , exe:
        LOG.error('get IP info or instance info error.the error is %s' % exe.message)
    try:
        ip_old = api.network.tenant_floating_ip_release(request , ip_id)
    except Unauthorized:
        raise
    except Exception , exe:
        msg = 'release ip error.'
        LOG.error('release ip error. The error is %s' % exe.message)
        return HttpResponse({ "message":msg, "statusCode":UI_RESPONSE_DWZ_ERROR }, status = UI_RESPONSE_ERROR)
    return HttpResponse({"message":"release ip successfully!" ,
                         "statusCode":UI_RESPONSE_DWZ_SUCCESS , "object_name":getattr(release_ip , 'ip' , 'unknown')} ,
                            status = UI_RESPONSE_DWZ_SUCCESS)

def pub_release_fips(request, ip_ids):
    try:
        for ip_id in ip_ids:
            api.network.tenant_floating_ip_release(request , ip_id)
    except Unauthorized:
        raise
    except Exception , exe:
        msg = 'release ip error.'
        LOG.error('release ip error. The error is %s' % exe.message)
        return HttpResponse({ "message":msg, "statusCode":UI_RESPONSE_DWZ_ERROR }, status = UI_RESPONSE_ERROR)
    return HttpResponse({"message":"release ip successfully!" ,
                         "statusCode":UI_RESPONSE_DWZ_SUCCESS } , status = UI_RESPONSE_DWZ_SUCCESS)

@check_permission('Release Floating IP')
@require_http_methods(['DELETE'])
@UIResponse('Virtual Address Manage', 'get_floating_ips_address')
def release_fips(request):
    """
    :param request: request object
    :param instance_id: the instance id
    :return: Confirm whether to delete instance
    """
    if 'release_fip' in request.POST:
        release_fips = request.POST.getlist('release_fip')
        if release_fips:
            return pub_release_fips(request,release_fips)
        else:
            return HttpResponse('No floatip selected')
    else:
        return HttpResponse('Request is wrong!')


@require_GET
def disassociate_ip_index(request , ip_id , instance_id):
    """
    :param request:request object, ip_id ,instance_id
    :return:view<'virtual_address_manage/disassociate_ip.html'>
    """
    return shortcuts.render(request , 'virtual_address_manage/disassociate_ip.html' ,
                                {'ip_id':ip_id, 'instance_id':instance_id})

@check_permission('Disassociate IP')
@require_POST
@UIResponse('Virtual Address Manage', 'get_floating_ips_address')
def disassociate_ip_action(request , ip_id , instance_id):
    """
    :param request:request object, ip_id, instance_id
    :return:view<'virtual_address_manage/index_ip.html'>
    """
    try:
        api.network.floating_ip_disassociate(request , ip_id , instance_id)
    except Unauthorized:
        raise
    except Exception , exe:
        msg = 'disassociate ip error.'
        LOG.error('disassociate ip error.the error is %s' % exe.message)
        return HttpResponse({ "message":msg , "statusCode":UI_RESPONSE_DWZ_ERROR } ,
                                status = UI_RESPONSE_ERROR)
    try:
        ip_old = api.tenant_floating_ip_get(request , ip_id)
        instance_old = api.server_get(request , instance_id)
    except Unauthorized:
        raise
    except Exception , exe:
        LOG.error('get IP info or instance info error.the error is %s' % exe.message)
    return HttpResponse({"message":"disassociate ip successfully!" ,
                         "statusCode":UI_RESPONSE_DWZ_SUCCESS , "object_name":(' Floating IP %(ip)s Instance %(inst)s')
                        % {"ip":  getattr(ip_old,'ip','unknown') , "inst": getattr(instance_old , 'name' , 'unknown')}} ,
                            status = UI_RESPONSE_DWZ_SUCCESS)