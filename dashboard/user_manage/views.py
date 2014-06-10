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


__author__ = 'liu xu'
__date__ = '2013-02-05'
__version__ = 'v2.0.1'

import logging

from django import shortcuts
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.views.decorators.debug import sensitive_variables
from django.utils.translation import ugettext_lazy as _

from dashboard import api
from dashboard.exceptions import Unauthorized, LicenseForbidden
from dashboard.authorize_manage.utils import create_token, get_user_role_name,creeper_role_from_roles
from dashboard.instance_manage.models import Distribution
from dashboard.software_manage.models import SoftwareCollect
from dashboard.utils import jsonutils, ui_response, UIResponse, Pagenation, check_permission
from dashboard.utils.ui import UI_RESPONSE_DWZ_ERROR, UI_RESPONSE_OK, UI_RESPONSE_ERROR

from .forms import CreateUserForm, UpdateUserForm, ChangePasswordForm, UpdateUserPasswordForm


if settings.DEBUG:
    __log__ = 'v2.0.1 create'
LOG = logging.getLogger(__name__)

#    code begin


@check_permission('View User')
@require_GET
@Pagenation('user_manage/index.html')
def index_user(request):
    """
    :param request:request object
    :return:view<'user_manage/index.html'>::list of users
    """
    users = []
    args = {}
    try:
        users = api.keystone.user_list(request)
    except Unauthorized:
        raise
    except Exception, e:
        msg = 'Unable to retrieve user list. %s' % e
        LOG.error(msg)

    args['list'] = users
    args['current_user_role'] = get_user_role_name(request)
    args['current_user_name'] = request.user.username

    return args


@require_GET
def user_detail(request, user_id):
    projects = api.keystone.get_projects_for_user(request, user_id)
    if projects:
        project_name = projects[0].name
        tenant_id = projects[0].id
        roles = api.roles_for_user(request, user_id, tenant_id)
        role_name = creeper_role_from_roles(roles)
    else:
        project_name = None
        role_name = None
    user = api.keystone.user_get(request, user_id)

    return shortcuts.render(request, 'user_manage/detail.html',
                     {'user': user, 'project_name': project_name, 'role_name': role_name})


@check_permission('Create User')
@require_GET
def create_user_form(request):
    """
    :param request:request object
    :return:view<'user_manage/create.html'>::the form table for creating a user
    """
    form = CreateUserForm(request)
    return shortcuts.render(request,
                            'user_manage/create.html',
                            {'form': form})


@sensitive_variables('data')
def handle_create(request, data):
    """
    :param request: request object
    :param data: the user's information bounded in CreateUserForm
    :return iRet::True (successful); False(Failed)
    """
    iRet = True
    try:
        new_user = api.user_create(request,
                                   data['name'],
                                   data['email'],
                                   data['password'],
                                   None, True)

        api.add_tenant_user_role(request,
                                 data['tenant_id'],
                                 new_user.id,
                                 data['role_id'])
    except (Unauthorized, LicenseForbidden):
        raise
    except Exception, e:
        if u'Duplicate entry' in e.message:
            msg = 'username has exist.'
            LOG.error(msg)
        else:
            msg = 'Unable to create user.'
            LOG.error(msg)

        iRet = False
        return iRet, msg

    return iRet, None


@require_POST
@UIResponse('User Manage', 'get_user_list')
def create_user_action(request):
    """
    :param request:request object
    :return:view<'get_user_list'>::Succeed in creating a user
            view<'user_manage/create.html'>::Failed to create a user
    """
    form = CreateUserForm(request, request.POST)
    if form.is_valid():
        iRet, msg = handle_create(request, form.cleaned_data)
        if iRet:
            return HttpResponse({"message": "Create User Success",
                                 "statusCode": UI_RESPONSE_OK,
                                 "object_name": form.cleaned_data['name']},
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


@sensitive_variables('data', 'password')
def handle_update(request, user_id, data):
    """
    :param request: request object
    :param user_id: the user's id
    :param data: the user's info
    :return iRet:: True (successful);False(Failed)
    """
    iRet = True

    try:
        api.keystone.user_update(request, user_id, **data)
    except Unauthorized:
        raise
    except Exception, e:
        iRet = False
        msg = _('Unable to update user %(user)s information.') % {'user': user_id}
        LOG.error('Unable to update user %s information. %s' % (user_id, e))
        return iRet, msg

    return iRet, None


@check_permission('Update User')
@require_GET
def update_user_form(request, user_id):
    """
    :param request: request object
    :param user_id: the user's id
    :return view<'user_manage/update.html'>:: the form table for updating user information
    """
    form = UpdateUserForm(request, user_id)
    return shortcuts.render(request,
                            'user_manage/update.html',
                            {'form': form, 'user_id': user_id})


@require_POST
@UIResponse('User Manage', 'get_user_list')
def update_user_action(request, user_id):
    """
    :param request: request object
    :param user_id: the user's id
    :return view<'get_user_list'>::update successfully
            view<'user_manage/update.html'>::failed
    """
    form = UpdateUserForm(request, user_id, request.POST)
    if form.is_valid():
        iRet, msg = handle_update(request, user_id, form.cleaned_data)
        if iRet:
            return HttpResponse({"message": "Update User Success",
                                 "statusCode": UI_RESPONSE_OK,
                                 "object_name": form.cleaned_data['name']},
                                status=UI_RESPONSE_OK)
        else:
            return HttpResponse({"message": msg,
                                 "statusCode": UI_RESPONSE_DWZ_ERROR},
                                status=UI_RESPONSE_ERROR)
    else:
        return HttpResponse({"form": form,
                             "statusCode": UI_RESPONSE_DWZ_ERROR},
                            status=UI_RESPONSE_ERROR)


@sensitive_variables('data', 'password')
def handle_update_password(request, user_id, data):
    """
    :param request: request object
    :param user_id: the user's id
    :param data: the user's info
    :return iRet:: True (successful);False(Failed)
    """
    iRet = True
    user = user_id
    password = data.pop('password')
    # If present, update password
    # FIXME(gabriel): password change should be its own form and view
    if password:
        try:
            api.user_update_password(request, user, password)
        except Unauthorized:
            raise
        except Exception, e:
            iRet = False
            msg = _('Unable to update password of user %(user)s.') % {'user': user}
            LOG.error('Unable to update password of user %s. %s' % (user, e))
            return iRet, msg

    return iRet, None


@check_permission('Update Password')
@require_GET
def update_user_password_form(request, user_id):
    """
    :param request: request object
    :param user_id: the user's id
    :return view<'user_manage/update.html'>:: the form table for updating user information
    """
    form = UpdateUserPasswordForm(request, user_id)
    return shortcuts.render(request,
                            'user_manage/updatepassword.html',
                            {'form': form, 'user_id': user_id})


@require_POST
def update_user_password_action(request, user_id):
    """
    :param request: request object
    :param user_id: the user's id
    :return view<'get_user_list'>::update successfully
            view<'user_manage/update.html'>::failed
    """
    form = UpdateUserPasswordForm(request, user_id, request.POST)
    if form.is_valid():
        iRet, msg = handle_update_password(request, user_id, form.cleaned_data)
        if iRet:
            return HttpResponse(jsonutils.dumps(
                ui_response(form,
                            message="Update User Password Success",
                            object_name=form.cleaned_data['name'])))
        else:
            return HttpResponse(jsonutils.dumps(ui_response(message=msg)))
    else:
        return HttpResponse(jsonutils.dumps(ui_response(form)))


@check_permission('Delete User')
@require_GET
def delete_user_form(request, user_id):
    return shortcuts.render(request,
                            'user_manage/delete.html',
                            {'user_id': user_id})


@require_http_methods(['DELETE'])
@UIResponse('User Manage', 'get_user_list')
def delete_user_action(request, user_id):
    """
    :param request: request object
    :param user_id: the user's id
    :return view<'get_user_list'>::delete successfully
    """
    if user_id == request.user.id:
        msg = 'Unable to delete your self.'
        return HttpResponse({"message": msg,
                             "statusCode": UI_RESPONSE_DWZ_ERROR},
                            status=UI_RESPONSE_ERROR)

    try:
        user = api.user_get(request, user_id, admin=True)
    except Unauthorized:
        raise
    except Exception, e:
        msg = 'Unable to retrieve user information.'
        LOG.error('Unable to retrieve user information. %s' % e)
        return HttpResponse({"message": msg,
                             "statusCode": UI_RESPONSE_DWZ_ERROR},
                            status=UI_RESPONSE_ERROR)

    try:
        Distribution.objects.filter(user_id=user_id).delete()
        SoftwareCollect.objects.filter(userid=user_id).delete()

        api.user_delete(request, user_id)
    except Unauthorized:
        raise
    except Exception, e:
        msg = 'can not delete user %(user)s.' % {'user': user_id}
        LOG.error('can not delete user %s. %s' % (user_id, e))
        return HttpResponse({"message": msg,
                             "statusCode": UI_RESPONSE_DWZ_ERROR},
                            status=UI_RESPONSE_ERROR)

    return HttpResponse({"message": "delete user success",
                         "statusCode": UI_RESPONSE_OK,
                         "object_name": getattr(user, 'name', '')},
                        status=UI_RESPONSE_OK)


@require_GET
def change_user_password_form(request):
    """
    :param request: request object
    :param user_id: the user's id
    :return view<'user_manage/update.html'>:: the form table for updating user information
    """
    form = ChangePasswordForm(request, request.user.id)
    return shortcuts.render(request,
                            'user_manage/changepassword.html',
                            {'form': form, 'user_id': request.user.id})


@require_POST
def change_user_password_action(request, user_id):
    if request.user.username == "admin":
        return HttpResponse(jsonutils.dumps(
            ui_response(status_code=UI_RESPONSE_DWZ_ERROR,
                        message="admin can't change password")))

    username = request.user.username

    form = ChangePasswordForm(request, user_id, request.POST)
    if form.is_valid():
        old_password = request.POST.get('oldpassword', '')
        password = request.POST.get('password', '')
        try:
            api.user_update_own_password(request, old_password, password)
        except Unauthorized:
            return HttpResponse(jsonutils.dumps(
                ui_response(status_code=UI_RESPONSE_DWZ_ERROR,
                            message="The old password is wrong.")))
        except Exception, e:
            LOG.error('Change password error. %s' % e)
            return HttpResponse(jsonutils.dumps(
                ui_response(status_code=UI_RESPONSE_DWZ_ERROR,
                            message="change password error")))

        try:
            create_token(request, username, password)
        except Exception:
            pass

        return HttpResponse(jsonutils.dumps(
            ui_response(status_code=UI_RESPONSE_OK,
                        message="change password success.",
                        object_name=username)))
    else:
        return HttpResponse(jsonutils.dumps(ui_response(form)))
