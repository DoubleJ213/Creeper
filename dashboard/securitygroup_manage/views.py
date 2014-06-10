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


__author__ = 'zhao lei'
__date__ = '2013-03-14'
__version__ = 'v2.0.1'

import logging

LOG = logging.getLogger(__name__)

#    code begin
from django import shortcuts
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
from django.conf import settings

from dashboard import api
from dashboard.authorize_manage.utils import switch_tenants
from dashboard.utils import jsonutils, ui_response, UIResponse, Pagenation
from dashboard.utils.ui import *
from dashboard.exceptions import Unauthorized
from dashboard.utils.ui import check_permission
from .forms import CreateSecurityGroupForm, CreateSecurityGroupRuleForm

NUMBERS_PER_PAGE = 10

if settings.DEBUG:
    __log__ = 'v2.0.1 create'


@require_GET
def get_securitygroup_projects(request):
    """
    :param request:request object
    :return:view<'project_manage/index.html'>::list of tenants
    """
    return shortcuts.render(request, 'securitygroup_manage/projectindex.html')


@require_GET
def get_securitygroup_projects_menu(request):
    """
    :param request:request object
    :return:view<'project_manage/index.html'>::list of tenants
    """
    project_menus = []
    projects = []
    try:
        projects = api.tenant_list(request, admin=True)
    except Unauthorized:
        raise
    except Exception, ex:
        LOG.error('Unable to retrieve project list,%s.' % ex)
    for project in projects:
        securitygroups = []
        if project.enabled and None != switch_tenants(request, project.id):
            securitygrouplist = api.security_group_list(request)
            if securitygrouplist:
                for securitygroup in securitygrouplist:
                    securitygroup_obj = {
                        'securitygroup_name': securitygroup.name,
                        'securitygroup_id': securitygroup.id
                    }
                    securitygroups.append(securitygroup_obj)

        project_menu = {
            'project_name': project.name,
            'project_id': project.id,
            'project_enabled': project.enabled,
            'project_securitygroup': securitygroups
        }
        project_menus.append(project_menu)
    return HttpResponse(jsonutils.dumps(project_menus))


@require_GET
@Pagenation('securitygroup_manage/index.html')
def get_securitygroup_list(request, tenant_id):
    """
    :param request:request object
    :return:view<'user_manage/index.html'>::list of users
    """
    args = {}
    securitygroups = []
    tenant_choices = []
    try:
        if None != switch_tenants(request, tenant_id):
            securitygroups = api.security_group_list(request)

        tenants = api.tenant_list_not_filter(request, admin=True)
        for tenant in tenants:
            tenant_choices.append((tenant.id, tenant.name))
    except Unauthorized:
        raise
    except Exception, ex:
        msg = 'Unable to retrieve security group list.%s' % ex
        LOG.error(msg)

    args['list'] = securitygroups
    args['tenants'] = tenant_choices
    args['tenant_id'] = tenant_id

    return args


@require_GET
def create_securitygroup_index(request, tenant_id):
    form = CreateSecurityGroupForm(request)
    return shortcuts.render(request, 'securitygroup_manage/create.html',
        {'form': form, 'tenant_id': tenant_id})


@check_permission('Add SecurityGroup')
@require_POST
@UIResponse('Network Security Manage', 'get_securitygroup_projects')
def create_securitygroup_action(request, tenant_id):
    form = CreateSecurityGroupForm(request, request.POST)
    if form.is_valid():
        data = form.cleaned_data
        switch_tenants(request, tenant_id)
        try:
            api.security_group_create(request, data['name'],
                data['description'])
        except Unauthorized:
            raise
        except Exception, ex:
            msg = ' Unable to create security group.'
            LOG.error("the error is %s" % ex.message)
            if ex.message.count(
                u'Quota exceeded, too many security groups.') > 0:
                msg = 'Quota exceeded, too many security groups.'
            return HttpResponse(
                {"message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR},
                status=UI_RESPONSE_ERROR)
        return HttpResponse({"message": "Create security group successfully!",
                             "statusCode": UI_RESPONSE_DWZ_SUCCESS,
                             "object_name": data['name']},
            status=UI_RESPONSE_DWZ_SUCCESS)
    else:
        return HttpResponse(
            {"form": form, "message": "", "statusCode": UI_RESPONSE_DWZ_ERROR},
            status=UI_RESPONSE_ERROR)


@require_GET
def delete_securitygroup_index(request, security_group_id):
    return shortcuts.render(request, 'securitygroup_manage/delete.html',
        {'security_group_id': security_group_id})


@check_permission('Delete SecurityGroup')
@require_http_methods(['DELETE'])
@UIResponse('Network Security Manage', 'get_securitygroup_projects')
def delete_securitygroup_action(request, security_group_id):
    try:
        group_old = api.security_group_get(request, security_group_id)
        api.security_group_delete(request, security_group_id)
    except Unauthorized:
        raise
    except Exception, ex:
        msg = 'Unable to delete security group.'
        LOG.error("the error is %s" % ex.message)
        return HttpResponse(
            {"message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR},
            status=UI_RESPONSE_ERROR)
    return HttpResponse({"message": "delete security group successfully!",
                         "statusCode": UI_RESPONSE_DWZ_SUCCESS,
                         "object_name": getattr(group_old, 'name', 'unknown')},
        status=UI_RESPONSE_DWZ_SUCCESS)


def get_source(rule):
    if 'cidr' in rule.ip_range:
        return rule.ip_range['cidr'] + ' (CIDR)'
    elif 'name' in rule.group:
        return rule.group['name']
    else:
        return None


@require_GET
def get_securitygroup_info(request, tenant_id, security_group_id):
    try:
        securitygroup = api.security_group_get(request, security_group_id)

        rules = [api.nova.SecurityGroupRule(frule) for
                 frule in securitygroup.rules]

        for rule in rules:
            setattr(rule, "ip_range", get_source(rule))

        return shortcuts.render(request,
            'securitygroup_manage/securitygroupinfo.html',
            {'securitygroup': securitygroup, 'rules': rules,
             "tenant_id": tenant_id})
    except Unauthorized:
        raise
    except Exception, ex:
        msg = 'get security group info error'
        LOG.error("the error is %s" % ex.message)
        return HttpResponse(jsonutils.dumps(ui_response(message=msg)))


@require_GET
def edit_securitygrouprules(request, security_group_id):
    try:
        securitygroup = api.security_group_get(request, security_group_id)

        number_per_page = NUMBERS_PER_PAGE
        if request.GET.has_key("numPerPage"):
            number_per_page = request.GET['numPerPage']
        paginator = Paginator(securitygroup.rules, number_per_page)
        page = request.GET.get('pageNum', 1)
        try:
            page_obj = paginator.page(page)  #page obj
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            page_obj = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            page_obj = paginator.page(paginator.num_pages)

        return shortcuts.render(request, 'securitygroup_manage/rules.html',
            {'page_obj': page_obj, 'security_group_id': security_group_id})
    except Unauthorized:
        raise
    except Exception, ex:
        msg = 'get security group rules info error.'
        LOG.error("the error is %s" % ex.message)
        return HttpResponse(jsonutils.dumps(ui_response(message=msg)))


@require_GET
def create_securitygrouprules_index(request, tenant_id, security_group_id):
    try:
        if None != switch_tenants(request, tenant_id):
            groups = api.security_group_list(request)
    except Unauthorized:
        raise
    except Exception, ex:
        groups = []
        LOG.error("Unable to retrieve security groups. The error is %s" % ex.message)

    security_groups = [(group.id, group.name) for group in groups]

    initial = {'security_group_id': security_group_id,
               'security_group_list': security_groups}

    form = CreateSecurityGroupRuleForm(request, initial=initial)
    return shortcuts.render(request, 'securitygroup_manage/createrule.html',
        {'form': form, 'tenant_id':tenant_id, 'security_group_id': security_group_id})


@require_GET
def delete_securitygrouprules_index(request, security_group_id, rule_id):
    return shortcuts.render(request, 'securitygroup_manage/deleterule.html',
        {'security_group_id': security_group_id, 'rule_id': rule_id})

@check_permission('Create Rule')
@require_POST
@UIResponse('Network Security Manage', 'get_securitygroup_projects')
def create_securitygrouprules_action(request, security_group_id):
    try:
        groups = api.security_group_list(request)
    except Unauthorized:
        raise
    except Exception, ex:
        groups = []
        LOG.error("Unable to retrieve security groups. The error is %s" % ex.message)

    security_groups = [(group.id, group.name) for group in groups]

    initial = {'security_group_id': security_group_id,
               'security_group_list': security_groups}
    form = CreateSecurityGroupRuleForm(request, request.POST, initial=initial)
    if form.is_valid():
        data = form.cleaned_data
        try:
            security_group_rule = api.security_group_rule_create(request,
                security_group_id,
                data['ip_protocol'], data['from_port'],
                data['to_port'], data['cidr'], data['source_group'])
        except Unauthorized:
            raise
        except Exception, ex:
            msg = ex.message
            LOG.error("the error is %s" % ex.message)
            if msg.count("This rule already exists") > 0:
                msg = "This rule already exists"
            if msg.count("SecurityGroupLimitExceeded: Quota exceeded, too many security group rules.") > 0:
                msg = "SecurityGroupLimitExceeded: Quota exceeded, too many security group rules."
            if msg.find("Invalid port range") != -1:
                msg = "Please enter the correct values!"
            return HttpResponse(
                {"message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR},
                status=UI_RESPONSE_ERROR)
        group_old = api.security_group_get(request, security_group_id)
        return HttpResponse(
            {"message": "Create security group rule successfully!",
             "statusCode": UI_RESPONSE_DWZ_SUCCESS,
             "object_name": "security_group=" + getattr(group_old, 'name',
                 'unknown') + ",rule_id=" + str(
                 getattr(security_group_rule, 'id',
                     'unknown'))},
            status=UI_RESPONSE_DWZ_SUCCESS)
    else:
        return HttpResponse(
            {"form": form, "message": "", "statusCode": UI_RESPONSE_DWZ_ERROR},
            status=UI_RESPONSE_DWZ_SUCCESS)

@check_permission('Delete Rule')
@require_http_methods(['DELETE'])
@UIResponse('Network Security Manage', 'get_securitygroup_projects')
def delete_securitygrouprules_action(request, security_group_id, rule_id):
    try:
        api.security_group_rule_delete(request, rule_id)
    except Unauthorized:
        raise
    except Exception, ex:
        msg = 'delete security group rule error.%s' % ex
        LOG.error(msg)
    group_old = api.security_group_get(request, security_group_id)
    return HttpResponse({"message": "delete security group rule successfully!",
                         "statusCode": UI_RESPONSE_DWZ_SUCCESS,
                         "object_name": "security_group=" + getattr(group_old,
                             'name',
                             'unknown') + ",rule_id=" + rule_id},
        status=UI_RESPONSE_DWZ_SUCCESS)
