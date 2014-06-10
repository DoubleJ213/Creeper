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


__author__ = 'liu xu '
__date__ = '2013-02-05'
__version__ = 'v2.0.1'

import logging

from django import shortcuts
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.debug import sensitive_variables
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.utils.translation import ugettext_lazy as _

from dashboard import api
from dashboard.exceptions import Unauthorized, LicenseForbidden
from dashboard.authorize_manage import ROLE_ADMIN
from dashboard.authorize_manage.utils import (switch_tenants,
                                              set_user_admin_token,
                                              get_user_role_name,
                                              creeper_role_from_roles)
from dashboard.instance_manage.models import Distribution
from dashboard.instance_manage.utils import get_authorized_instances
from dashboard.image_template_manage.views import delete_project_images
from dashboard.utils import jsonutils, UIResponse, Pagenation, check_permission
from dashboard.utils.ui import UI_RESPONSE_OK, UI_RESPONSE_ERROR, UI_RESPONSE_DWZ_ERROR

from .forms import CreateTenantForm, UpdateTenantForm, UpdateQuotasForm, AddProjectUserForm, EditProjectUserForm


if settings.DEBUG:
    __log__ = 'v2.0.1 create'

print __name__
LOG = logging.getLogger(__name__)

#    code begin

@check_permission('View Project')
@require_GET
def index_project(request):
    """
    :param request:request object
    :return:view<'project_manage/index.html'>::list of tenants
    """
    return shortcuts.render(request,
                            'project_manage/index.html',
                            {'role': get_user_role_name(request)})


@check_permission('View Project Users')
@require_GET
@Pagenation('project_manage/projects.html')
def get_all_project(request):
    """
    :param request:request object
    :return:view<'project_manage/index.html'>::list of tenants
    """
    args = {}
    projects = []
    try:
        projects = api.tenant_list(request, admin=True)
    except Unauthorized:
        raise
    except Exception, e:
        LOG.error('Unable to retrieve project list. %s' % e)

    args['list'] = projects
    args['projects'] = projects
    return args


@require_GET
def get_project_menu(request):
    project_menus = []
    projects = []
    try:
        projects = api.tenant_list(request, admin=True)
    except Unauthorized:
        raise
    except Exception, e:
        LOG.error('Unable to retrieve project list. %s' % e)

    for project in projects:
        project_user = []
        users = []
        try:
            users = api.keystone.user_list(request, project.id)
        except Unauthorized:
            raise
        except Exception, e:
            LOG.error('Unable to get tenant %s user. %s' % (project.id, e))

        if users:
            for user in users:
                user_obj = {
                    'user_name': user.name,
                    'user_id': user.id
                }
                project_user.append(user_obj)

        project_menu = {
            'project_name': project.name,
            'project_id': project.id,
            'project_enabled': project.enabled,
            'project_user': project_user
        }
        project_menus.append(project_menu)

    return HttpResponse(jsonutils.dumps(project_menus))


def add_admin_tenant(request, tenant_id):
    roles = api.keystone.role_list(request)
    admin_role_id = ''
    for role in roles:
        if role.name == ROLE_ADMIN:
            admin_role_id = role.id
            break

    api.add_tenant_user_role(request,
                            tenant_id,
                            request.user.id,
                            admin_role_id)


@sensitive_variables('data')
def handle_create(request, data):
    """
    :param request: request object
    :param data: the tenant's information bounded in CreateTenantForm
    :return iRet::True (successful); False(Failed)
    """
    try:
        tenant = api.tenant_create(request,
                                data['name'],
                                data['description'],
                                data['enabled'])
    except (Unauthorized, LicenseForbidden):
        raise
    except Exception, e:
        if u'Duplicate entry' in e.message:
            msg = 'project name has exist.'
        else:
            msg = _('Unable to create tenant %(tenant)s.') % {'tenant': data['name']}
        LOG.error('Unable to create tenant %s. %s' % (data['name'], e))
        return False, msg

    # atomic
    try:
        add_admin_tenant(request, tenant.id)
    except Exception, e:
        while True:
            try:
                set_user_admin_token(request)
                api.tenant_delete(request, tenant.id)
                break
            except:
                pass    # use while for large request
        msg = _('Unable to create tenant %(tenant)s.') % {'tenant': data['name']}
        LOG.error('Unable to add admin to project %s. %s' % (data['name'], e))
        return False, msg

    set_user_admin_token(request)
    # return id instead True, for homepage
    return tenant.id, None


@check_permission('Create Project')
@require_GET
def create_project_form(request):
    """
    :param request:request object
    :return:view<'project_manage/create.html'>::the form table for creating a tenant
    """
    form = CreateTenantForm()
    return shortcuts.render(request,
                            'project_manage/create.html',
                            {'form': form})


@check_permission('Create Project')
@require_POST
@UIResponse('Authorization Manage', 'get_project_list')
def create_project_action(request):
    """
    :param request: request object
    :return view<'get_project_list'>::create the tenant successfully
            view<'project_manage/create.html'>::failed to create the tenant
    """
    treeFatherId = request.POST.get('tree_father_id', '')
    if not treeFatherId:
        return HttpResponse({"message": 'Unable to create project',
                             "statusCode": UI_RESPONSE_DWZ_ERROR},
                            status=UI_RESPONSE_ERROR)

    form = CreateTenantForm(request.POST)
    if form.is_valid():
        try:
            iRet, msg = handle_create(request, form.cleaned_data)
            if iRet:
                project_id = ""
                project_name = ""
                project_enabled = ""
                try:
                    projects = api.tenant_list(request, admin=True)
                    for project in projects:
                        if project.name == form.cleaned_data['name']:
                            project_id = project.id
                            project_name = project.name
                            project_enabled = project.enabled
                except Exception, e:
                    msg = 'Can not get project list. %s' % e
                    LOG.error(msg)

                return HttpResponse({"message": "Create Project Success",
                                     "statusCode": UI_RESPONSE_OK,
                                     "object_name": form.cleaned_data['name'],
                                     "operType": "add_project",
                                     "treeNodeObj": {"project_id": project_id,
                                                     "project_name": project_name,
                                                     "project_enabled": project_enabled}},
                                    status=UI_RESPONSE_OK)
            else:
                return HttpResponse({"message": msg,
                                     "statusCode": UI_RESPONSE_DWZ_ERROR},
                                    status=UI_RESPONSE_ERROR)
        except Unauthorized:
            raise
        except LicenseForbidden:
            raise
        except Exception, e:
            LOG.error('Can not get project list. %s' % e)
            return HttpResponse({"message": 'Can not get project list.',
                                 "statusCode": UI_RESPONSE_DWZ_ERROR},
                                status=UI_RESPONSE_ERROR)
    else:
        return HttpResponse({"form": form,
                             "message": "",
                             "statusCode": UI_RESPONSE_DWZ_ERROR},
                            status=UI_RESPONSE_ERROR)


@sensitive_variables('data')
def handle_update(request, data):
    """
    :param request: request object
    :param data: the tenant's info
    :return iRet::True (successful); False(Failed)
    """
    try:
        api.tenant_update(request,
                        data['id'],
                        data['name'],
                        data['description'],
                        data['enabled'])
    except Unauthorized:
        raise
    except Exception, e:
        if u'Duplicate entry' in e.message:
            msg = 'project name has exist.'
        else:
            msg = _('Unable to update tenant %(tenant)s.') % {'tenant': data['name']}
        LOG.error('Unable to update tenant %s. %s' % (data['name'], e))
        return False, msg
    return True, None


@check_permission('Update Project')
@require_GET
def update_project_form(request, tenant_id):
    """
    :param request: request object
    :param tenant_id: id of the tenant
    :return view<'project_manage/update_project.html'>::show the form table for updating the tenant
    """
    form = UpdateTenantForm(request, tenant_id)
    return shortcuts.render(request,
                            'project_manage/update_project.html',
                            {'form': form, 'tenant_id': tenant_id})


@check_permission('Update Project')
@require_POST
@UIResponse('Authorization Manage', 'get_project_list')
def update_project_action(request, tenant_id):
    """
    :param request: request object
    :param tenant_id: id of the tenant
    :return view<'get_project_list'>::update the tenant successfully
            view<'project_manage/update_project.html'>::failed to update the tenant
    """
    form = UpdateTenantForm(request, tenant_id, request.POST)
    if form.is_valid():
        iRet, msg = handle_update(request, form.cleaned_data)
        if iRet:
            project_id = tenant_id
            project_name = form.cleaned_data['name']
            project_enabled = form.cleaned_data['enabled']
            return HttpResponse({"message": "Update Project Success",
                                 "statusCode": UI_RESPONSE_OK,
                                 "object_name": project_name,
                                 "operType": "update_project",
                                 "treeNodeObj": {"project_id": project_id,
                                                 "project_name": project_name,
                                                 "project_enabled": project_enabled}},
                                status=UI_RESPONSE_OK)
        else:
            return HttpResponse({"message": msg,
                                 "statusCode": UI_RESPONSE_DWZ_ERROR},
                                status=UI_RESPONSE_ERROR)
    else:
        return HttpResponse({"form": form,
                             "statusCode": UI_RESPONSE_DWZ_ERROR},
                            status=UI_RESPONSE_ERROR)


@sensitive_variables('data')
def handle_update_quotas(request, data):
    """
    :param request: request object
    :param data: the information of tenant quotas
    :return iRet::True (successful); False(Failed)
    """
    try:
        floating_cnt = 0
        floating_ips = api.tenant_floating_ip_list(request)
        for ip in floating_ips:
            if data['tenant_id'] == ip.tenant_id:
                floating_cnt += 1
        if data['floating_ips'] < floating_cnt:
            return False, "floating ip number can not less than used"

        api.nova.nova_tenant_quota_update(request,
            data['tenant_id'],
#            metadata_items=data['metadata_items'],
#            injected_file_content_bytes=data['injected_file_content_bytes'],
            #            volumes=data['volumes'],
            #            gigabytes=data['gigabytes'],
            ram=data['ram'],
            floating_ips=data['floating_ips'],
            instances=data['instances'],
#            injected_files=data['injected_files'],
            cores=data['cores'],
#            fixed_ips=data['fixed_ips'],
            security_groups=data['security_groups'],
            security_group_rules=data['security_group_rules'],
        )
        api.cinder.cinder_tenant_quota_update(request,
            data['tenant_id'],
            volumes=data['volumes'],
            gigabytes=data['gigabytes'],
        )
    except Unauthorized:
        raise
    except LicenseForbidden:
        raise
    except Exception, e:
        msg = _("Unable to update tenant %(tenant)s quotas.") % {'tenant': data['tenant_id']}
        LOG.error("Unable to update tenant %s quotas. %s" % (data['tenant_id'], e))
        return False, msg

    return True, None


@check_permission('Update Project Quotas')
@require_GET
def update_project_quotas_form(request, tenant_id):
    """
    :param request: request object
    :param tenant_id: id of the tenant
    :return view<'project_manage/update_project_quotas.html'>::show the form table for updating the tenant quotas
    """
    form = UpdateQuotasForm(request, tenant_id)
    return shortcuts.render(request,
                            'project_manage/update_project_quotas.html',
                            {'form': form, 'tenant_id': tenant_id})


@check_permission('Update Project Quotas')
@require_POST
@UIResponse('Authorization Manage', 'get_project_list')
def update_project_quotas_action(request, tenant_id):
    """
    :param request: request object
    :param tenant_id: id of the tenant
    :return view<'get_project_list'>::update the tenant quotas successfully
            view<'project_manage/update_project_quotas.html'>::failed to update the tenant quotas
    """
    form = UpdateQuotasForm(request, tenant_id, request.POST)
    if form.is_valid():
        iRet, msg = handle_update_quotas(request, form.cleaned_data)
        if iRet:
            return HttpResponse({"message": "Update Project Quotas Success",
                                 "statusCode": UI_RESPONSE_OK,
                                 "object_name": form.cleaned_data['tenant_name']},
                                status=UI_RESPONSE_OK)
        else:
            return HttpResponse({"message": msg,
                                 "statusCode": UI_RESPONSE_DWZ_ERROR},
                                status=UI_RESPONSE_ERROR)
    else:
        return HttpResponse({"form": form,
                             "statusCode": UI_RESPONSE_DWZ_ERROR},
                            status=UI_RESPONSE_ERROR)


@check_permission('Delete Project')
@require_GET
def delete_project_form(request, tenant_id):
    return shortcuts.render(request,
                            'project_manage/delete.html',
                            {'tenant_id': tenant_id})


@check_permission('Delete Project')
@require_http_methods(['DELETE'])
@UIResponse('Authorization Manage', 'get_project_list')
def delete_project_action(request, tenant_id):
    """
    :param request: request object
    :param tenant_id: id of the tenant
    :return view<'get_project_list'>
    """
    try:
        tenant = api.keystone.tenant_get(request, tenant_id, admin=True)
        users = api.keystone.user_list(request, tenant_id)
        instances = get_authorized_instances(request, tenant_id)
        volumes = api.volume_list(request)
        routers = api.quantum.router_list(request)
        securitygroups = api.security_group_list(request)
        networks = api.quantum.network_list_for_tenant(request, tenant_id)
        floating_ips = api.network.tenant_floating_ip_list(request)


        if instances:
            msg = "Unable to delete tenant.please remove it's instance"
            return HttpResponse({"message": msg,
                                 "statusCode": UI_RESPONSE_DWZ_ERROR},
                                status=UI_RESPONSE_ERROR)

        if len(volumes) > 0:
            msg = "Unable to delete tenant.please remove it's volumes"
            return HttpResponse({"message": msg,
                                 "statusCode": UI_RESPONSE_DWZ_ERROR},
                                status=UI_RESPONSE_ERROR)

        if len(routers) > 0:
            for router in routers:
                if router['tenant_id'] == tenant_id:
                    msg = "Unable to delete tenant.please remove its routers"
                    return HttpResponse({"message": msg,
                                         "statusCode": UI_RESPONSE_DWZ_ERROR},
                        status=UI_RESPONSE_ERROR)

        if len(securitygroups) > 1:
            msg = "Unable to delete tenant.please remove its securitygroups"
            return HttpResponse({"message": msg,
                                 "statusCode": UI_RESPONSE_DWZ_ERROR},
                status=UI_RESPONSE_ERROR)

        if len(networks) > 0:
            for network in networks:
                if network['tenant_id'] == tenant_id:
                    msg = "Unable to delete tenant.please remove its networks"
                    return HttpResponse({"message": msg,
                                         "statusCode": UI_RESPONSE_DWZ_ERROR},
                        status=UI_RESPONSE_ERROR)

        if len(floating_ips) > 0:
            for floating_ip in floating_ips:
                if floating_ip['tenant_id'] == tenant_id:
                    msg = "Unable to delete tenant.please remove its floating_ips"
                    return HttpResponse({"message": msg,
                                         "statusCode": UI_RESPONSE_DWZ_ERROR},
                        status=UI_RESPONSE_ERROR)

        if len(users) > 0:
            msg = "Unable to delete tenant.please remove it's users"
            return HttpResponse({"message": msg,
                                 "statusCode": UI_RESPONSE_DWZ_ERROR},
                status=UI_RESPONSE_ERROR)

        delete_project_images(request, tenant_id)
        api.tenant_delete(request, tenant_id)
    except Unauthorized:
        raise
    except Exception, e:
        msg = 'Unable to delete tenant.'
        LOG.error('Unable to delete tenant %s. %s' % (tenant_id, e))
        return HttpResponse({"message": msg,
                             "statusCode": UI_RESPONSE_DWZ_ERROR},
                            status=UI_RESPONSE_ERROR)

    set_user_admin_token(request)

    return HttpResponse({"message": "delete project success",
                         "statusCode": UI_RESPONSE_OK,
                         "object_name": tenant.name,
                         "operType": "delete_project"},
                        status=UI_RESPONSE_OK)


@require_GET
@Pagenation('project_manage/get_user.html')
def get_project_users(request, tenant_id):
    """
    :param request: request object
    :param tenant_id: id of the tenant
    :return view<'project_manage/get_user.html'>::get the user info on the tenant
    """
    user_roles = []
    try:
        users = api.keystone.user_list(request, tenant_id)
        for user in users:
            roles = api.roles_for_user(request, user.id, tenant_id)
            role_name = creeper_role_from_roles(roles)
            user_roles.append((user, role_name))
    except Unauthorized:
        raise
    except Exception, e:
        LOG.error('Unable to get tenant %s users. %s' % (tenant_id, e))
        return shortcuts.redirect('get_project_list')

    args = {}
    args['user_roles'] = user_roles

    return args


@sensitive_variables('data')
def handle_user_add(request, data):
    """
    :param request: request object
    :param data: the info of the tenant and user:tenant_id,user_id,role_id
    :return iRet::True (successful); False(Failed)
    """
    try:
        api.remove_tenant_user(request, data['tenant_id'], data['user_id'])
        api.add_tenant_user_role(request,
                                data['tenant_id'],
                                data['user_id'],
                                data['role_id'])
    except Unauthorized:
        raise
    except Exception, e:
        msg = 'Unable to add user to tenant.'
        LOG.error('Unable to add  user %s to tenant %s. %s'
                  % (data['user_id'], data['tenant_id'], e))
        return False, msg

    return True, None


@check_permission('Create Project User')
@require_GET
def add_project_users_form(request, tenant_id):
    """
    :param request: request object
    :param tenant_id: id of the tenant
    :return view<'project_manage/add_user.html'>::the form table for adding a user to a tenant
    """
    form = AddProjectUserForm(request, tenant_id)
    return shortcuts.render(request,
                            'project_manage/add_user.html',
                            {'form': form, 'tenant_id': tenant_id})


@check_permission('Create Project User')
@require_POST
@UIResponse('Authorization Manage', 'get_project_list')
def add_project_users_action(request, tenant_id):
    """
    :param request: request object
    :param tenant_id: id of the tenant
    :return view<'get_project_users'>::add the user to the tenant successfully
            view<'project_manage/add_user.html'>::failed to add the user to the tenant
    """
    treeFatherId = request.POST.get('tree_father_id', '')
    userId = request.POST.get('user_id', '')
    if not treeFatherId:
        msg = 'Unable to add user to tenant.'
        LOG.error("Unable to add user to tenant. error is the treeFatherId is null")
        return HttpResponse({"message": msg,
                             "statusCode": UI_RESPONSE_DWZ_ERROR},
                            status=UI_RESPONSE_ERROR)

    if not userId:
        msg = 'Available User is required.'
        LOG.error("Unable to add user to tenant because there is no extra user to add to project.")
        return HttpResponse({"message": msg,
                             "statusCode": UI_RESPONSE_DWZ_ERROR},
            status=UI_RESPONSE_ERROR)

    form = AddProjectUserForm(request, tenant_id, request.POST)
    if form.is_valid():
        data = form.cleaned_data
        iRet, msg = handle_user_add(request, data)
        if iRet:
            try:
                tenant = api.keystone.tenant_get(request, tenant_id, admin=True)
                user = api.keystone.user_get(request, data['user_id'], admin=True)
                roles = api.roles_for_user(request, user.id, tenant_id)
                role_name = creeper_role_from_roles(roles)
                return HttpResponse({"message": "Add project User Success",
                                     "statusCode": UI_RESPONSE_OK,
                                     "object_name": "tenant=" + tenant.name
                                                    + " user=" + user.name,
                                     "operType": "add_user",
                                     "treeNodeObj": {"project_id": tenant_id,
                                                     "user_id": user.id,
                                                     "user_name": user.name,
                                                     "role_name": role_name}},
                                    status=UI_RESPONSE_OK)
            except Unauthorized:
                raise
            except Exception, e:
                msg = 'Unable to add user to tenant.'
                LOG.error('Unable to add user to tenant %s. %s' % (tenant_id, e))
                return HttpResponse({"message": msg,
                                     "statusCode": UI_RESPONSE_DWZ_ERROR},
                                    status=UI_RESPONSE_ERROR)
        else:
            return HttpResponse({"message": msg,
                                 "statusCode": UI_RESPONSE_DWZ_ERROR},
                                status=UI_RESPONSE_ERROR)
    else:
        return HttpResponse({"form": form,
                             "message": "",
                             "statusCode": UI_RESPONSE_DWZ_ERROR},
                            status=UI_RESPONSE_ERROR)


@sensitive_variables('data')
def handle_user_edit(request, data):
    """
    :param request: request object
    :param data: the info of the tenant and user:tenant_id,user_id,role_id
    :return iRet::True (successful); False(Failed)
    """
    user = data.pop('user_id')
    tenant = data.pop('tenant_id')
    role = data.pop('role_id')
    try:
        api.remove_tenant_user(request, tenant, user)
        api.add_tenant_user_role(request, tenant, user, role)
    except Unauthorized:
        raise
    except Exception, e:
        msg = 'Unable to edit user from tenant.'
        LOG.error('Unable to edit user %s from tenant %s. %s' % (user, tenant, e))
        return False, msg

    return True, None


@check_permission('Update Project User')
@require_GET
def edit_project_users_form(request, tenant_id, user_id):
    """
    :param request: request object
    :param tenant_id: id of the tenant
    :param user_id: id of the user
    :return view<'project_manage/edit_user_role.html'>::the form table for editing the role of a user on the tenant
    """
    form = EditProjectUserForm(request, tenant_id, user_id)
    try:
        user = api.user_get(request, user_id, admin=True)
        roles = api.roles_for_user(request, user_id, tenant_id)
        role = creeper_role_from_roles(roles)
    except Unauthorized:
        raise
    except Exception, e:
        LOG.error('Unable get user %s. %s' % (user_id, e))
        raise

    return shortcuts.render(request,
                            'project_manage/edit_user_role.html',
                            {'form': form, 'user': user, 'role': role,
                             'tenant_id': tenant_id, 'user_id': user_id})


@check_permission('Update Project User')
@require_POST
@UIResponse('Authorization Manage', 'get_project_list')
def edit_project_users_action(request, tenant_id, user_id):
    """
    :param request: request object
    :param tenant_id: id of the tenant
    :param user_id: id of the user
    :return view<'get_project_users'>::add the user to the tenant successfully
            view<'edit_project_users'>::failed to add the user to the tenant
    """
    form = EditProjectUserForm(request, tenant_id, user_id, request.POST)
    if form.is_valid():
        iRet, msg = handle_user_edit(request, form.cleaned_data)
        if iRet:
            tenant = api.keystone.tenant_get(request, tenant_id, admin=True)
            user = api.keystone.user_get(request, user_id, admin=True)
            roles = api.roles_for_user(request, user_id, tenant_id)
            role_name = creeper_role_from_roles(roles)
            return HttpResponse({"message": "Edit project User Success",
                                 "statusCode": UI_RESPONSE_OK,
                                 "object_name": "tenant=" + tenant.name
                                                + " user=" + user.name,
                                 "operType": "edit_user",
                                 "treeNodeObj": {"project_id": tenant_id,
                                                 "user_id": user.id,
                                                 "user_name": user.name,
                                                 "role_name": role_name}},
                                status=UI_RESPONSE_OK)
        else:
            return HttpResponse({"message": msg,
                                 "statusCode": UI_RESPONSE_DWZ_ERROR},
                                status=UI_RESPONSE_ERROR)

    else:
        return HttpResponse({"form": form,
                             "message": "",
                             "statusCode": UI_RESPONSE_DWZ_ERROR},
                            status=UI_RESPONSE_ERROR)


@check_permission('Delete Project User')
@require_GET
def delete_project_users_form(request, tenant_id, user_id):
    return shortcuts.render(request,
                            'project_manage/delete_user.html',
                            {'user_id': user_id, 'tenant_id': tenant_id})


@check_permission('Delete Project User')
@require_http_methods(['DELETE'])
@UIResponse('Authorization Manage', 'get_project_list')
def delete_project_users_action(request, tenant_id, user_id):
    """
    :param request: request object
    :param tenant_id: id of the tenant
    :param user_id: id of the user
    :return view<'get_project_list'>
    """
    try:
        vms = Distribution.objects.filter(user_id=user_id)
        for vm in vms:
            instance = api.server_get(request, vm.instance_id)
            if instance.tenant_id == tenant_id:
                vm.delete()

        api.remove_tenant_user(request, tenant_id, user_id)
    except Unauthorized:
        raise
    except Exception, e:
        msg = 'Unable to delete user from tenant.'
        LOG.error('Unable to delete user %s from tenant %s. %s'
                  % (user_id, tenant_id, e))
        return HttpResponse({"message": msg,
                             "statusCode": UI_RESPONSE_DWZ_ERROR},
                            status=UI_RESPONSE_ERROR)

    tenant = api.keystone.tenant_get(request, tenant_id, admin=True)
    user = api.keystone.user_get(request, user_id, admin=True)
    return HttpResponse({"message": "delete project user success",
                         "statusCode": UI_RESPONSE_OK,
                         "object_name": "tenant=" + tenant.name
                                        + " user=" + user.name,
                         "operType": "delete_user"},
                        status=UI_RESPONSE_OK)


@require_GET
def get_project_user(request, tenant_id, user_id):
    try:
        user = api.user_get(request, user_id)
        roles = api.roles_for_user(request, user_id, tenant_id)
        role_name = creeper_role_from_roles(roles)
    except Unauthorized:
        raise
    except Exception, e:
        LOG.error("Unable to retrieve user %s. %s" % (user_id, e))
        raise

    return shortcuts.render(request,
                            'project_manage/user_info.html',
                            {'user': user, 'role_name': role_name})


@require_GET
def enable_project_form(request, tenant_id):
    """
    :param request: request object
    :param tenant_id: id of the tenant
    """
    return shortcuts.render(request,
                            'project_manage/enable_project.html',
                            {'tenant_id': tenant_id})


@require_POST
@UIResponse('Authorization Manage', 'get_project_list')
def enable_project_action(request, tenant_id):
    """
    :param request: request object
    :param tenant_id: id of the tenant
    :return view<'get_project_list'>::enable the tenant successfully
            view<'project_manage/enable_project.html'>::failed to enable the tenant
    """
    try:
        tenant = api.keystone.tenant_get(request, tenant_id, admin=True)
    except Unauthorized:
        raise
    except Exception, e:
        LOG.error('Unable get project %s. %s', (tenant_id, e))
        return HttpResponse({"message": "Unable get project",
                             "statusCode": UI_RESPONSE_DWZ_ERROR},
                            status=UI_RESPONSE_ERROR)

    data = {}
    data['id'] = tenant.id
    data['name'] = tenant.name
    data['description'] = tenant.description
    data['enabled'] = True
    iRet, msg = handle_update(request, data)
    if iRet:
        return HttpResponse({"message": "Enable Project Success",
                             "statusCode": UI_RESPONSE_OK,
                             "operType": "enable_project",
                             "treeNodeObj": {"project_id": tenant_id}},
                            status=UI_RESPONSE_OK)
    else:
        return HttpResponse({"message": msg,
                             "statusCode": UI_RESPONSE_DWZ_ERROR},
                            status=UI_RESPONSE_ERROR)


@require_GET
def get_project_summary(request):
    project_summary = {}
    INSTANCE_ON_STATUS = ('active',)
    try:
        projects = api.tenant_list(request, admin=True)
        for project in projects:
            if not project.enabled:
                continue

            users = api.user_list(request, project.id)
            networks = api.network_list_for_tenant(request, project.id)

            instance_on_cnt = 0
            instance_off_cnt = 0
            instances = []
            if switch_tenants(request, project.id):
                instances = api.server_list(request)

            for instance in instances:
                if instance.status.lower() in INSTANCE_ON_STATUS:
                    instance_on_cnt += 1
                else:
                    instance_off_cnt += 1

            summary = {'project_name': project.name,
                       'user_cnt': len(users),
                       'network_cnt': len(networks),
                       'instance_on_cnt': instance_on_cnt,
                       'instance_off_cnt': instance_off_cnt}

            project_summary[project.id] = summary
    except Unauthorized:
        raise
    except Exception, e:
        LOG.error(e)

    sorted_list = sorted(project_summary.iteritems(), key=lambda d: d[1]['instance_on_cnt'], reverse=True)

    sorted_list = [ data[1] for data in sorted_list  ]
    sorted_list = sorted_list[0:5]

    return HttpResponse(jsonutils.dumps(sorted_list))
