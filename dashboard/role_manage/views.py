"""
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
"""

__author__ = 'sunyu'
__date__ = '2013-10-21'
__version__ = 'v3.1.3'

import logging
import simplejson
from django import shortcuts
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.http import require_GET, require_POST

import MySQLdb
from dashboard import api
from dashboard.exceptions import Unauthorized
from dashboard.utils.i18n import get_text
from dashboard.authorize_manage.utils import get_user_role_name
from .forms import CreateRoleForm, UpdateRoleForm
from .models import *
from dashboard.utils import jsonutils, ui_response, UIResponse, Pagenation, check_permission
from dashboard.utils.ui import UI_RESPONSE_DWZ_ERROR, UI_RESPONSE_OK, UI_RESPONSE_ERROR

if settings.DEBUG:
    __log__ = 'v2.0.1 create'
LOG = logging.getLogger(__name__)

right_menus = {
    'View Global Monitor': 'Global Monitor',
    'View Own Instance': 'Instance Manage',
    'View Image': 'Image Manage',
    'View Flavor': 'HardTemplate Manage',
    'View Node': 'Foundation Manage',
    'View Volume': 'Volume Manage',
    'View Software': 'Software Manage',
    'View Project': 'Authorization Manage',
    'View User': 'User Manage',
    'View Role': 'Role Manage',
    'View Network': 'Virtual NetWork Manage',
    'View Router': 'Virtual Routers Manage',
    'View Address': 'Virtual Address Manage',
    'View SecurityGroup': 'Network Security Manage',
    'View Notice': 'Notice Manage',
    'View Own Logs': 'Log Query',
    'View Task': 'Check Manage',
}

@check_permission('View Role')
@require_GET
@Pagenation('role_manage/index.html')
def get_role_list(request):
    """
        :param request:request object
        :return:view<'role_manage/index.html'>::list of roles
    """
    roles = []
    args = {}
    try:
        roles = api.keystone.role_list(request)
    except Unauthorized:
        raise
    except Exception, e:
        msg = 'Unable to retrieve role list. %s' % e
        LOG.error(msg)

    admin_role = None
    for role in roles:
        try:
            if 'admin' == role.name:
                admin_role = role
                continue
            setattr(role, 'id', role.id)
#            enabled = getattr(role, 'enabled', '')
#            if enabled is not None and enabled != '':
#                setattr(role, 'enabled', role.enabled)
#            else:
#                setattr(role, 'enabled', '')

            if 'Member' == role.name or 'ProjectAdmin' == role.name or 'Auditor' == role.name:
                setattr(role, 'status', '0')
#                setattr(role, 'enabled', '1')
            else:
                setattr(role, 'status', '1')

        except Exception, exc:
            LOG.error("Can't found attribute. %s" % exc)
    if admin_role is not None:
        roles.remove(admin_role)
    args['list'] = roles
    #    args['current_user_role'] = get_user_role_name(request)

    return args


@check_permission('Create Role')
@require_GET
def create_role_form(request):
    """
    :param request:request object
    :return:view<'role_manage/create.html'>::the form table for creating a role
    """
    form = CreateRoleForm(request)
    roles = []
    #    parent_choices = [('', _("Select a project"))]
    #    try:
    #        roles = api.keystone.role_list(request)
    #        roles = [role for role in roles if
    #                 'ProjectAdmin' == role.name or 'Member' == role.name or 'admin' == role.name or 'Auditor' == role.name]
    #        for role in roles:
    #            parent_choices.append((role.id, role.name))
    #    except Exception, exc:
    #        LOG.error("Error is %s" % exc)
    return shortcuts.render(request,
                            'role_manage/create.html',
                            {'form': form})


@require_POST
@UIResponse('Role Manage', 'get_role_list')
def create_role(request):
    form = CreateRoleForm(request, request.POST.copy())
    if form.is_valid():
    #        roles = api.keystone.role_list(request)
        data = form.cleaned_data
        try:
            rights = data['rights'].split(',')
            role = api.keystone.role_create(request, data['name'],
                                            data['description'], enabled=True)
            role_id = role.id
            for right in rights:
                if len(right) > 2 and right != '':
                    role_right = Role_right(role_id=role_id,
                                            right_key=right)
                    role_right.save()
            return HttpResponse({"message": "create role success",
                                 "statusCode": UI_RESPONSE_OK,
                                 "object_name": getattr(role, 'name', '')},
                                status=UI_RESPONSE_OK)
        except Unauthorized:
            raise
        except Exception, exc:
            if u'Duplicate entry' in exc.message:
                msg = 'role name has exist.'
                LOG.error(msg)
            else:
                msg = 'Unable to create role.'
                LOG.error(msg)
            return HttpResponse({"message": msg,
                                 "statusCode": UI_RESPONSE_DWZ_ERROR},
                                status=UI_RESPONSE_ERROR)
    return HttpResponse({'form': form,
                         "statusCode": UI_RESPONSE_DWZ_ERROR},
                        status=UI_RESPONSE_ERROR)


@check_permission('Update Role')
@require_GET
def edit_role_form(request, role_id):
    """
    :param request:request object
    :return:view<'role_manage/update.html'>::the form table for updating a role
    """
    form = UpdateRoleForm(request, role_id)
    return shortcuts.render(request,
                            'role_manage/update.html',
                            {'form': form, 'role_id': role_id})


@require_POST
@UIResponse('Role Manage', 'get_role_list')
def edit_role(request, role_id):
    form = UpdateRoleForm(request, role_id, request.POST.copy())
    role = api.keystone.role_get(request, role_id)
    if form.is_valid():
        try:
            data = form.cleaned_data
            rights = data['rights'].split(',')
            kwargs = {"name": data['name'], "description": data['description']}
            api.keystone.role_update(request, role_id, **kwargs)

            role_right = Role_right.objects.filter(role_id=role_id)
            for ro in role_right:
                if rights.count(ro.right_key):
                    rights.remove(ro.right_key)
                else:
                    ro.delete()

            for right in rights:
                if len(right) > 2 and right != '':
                    role_right = Role_right(role_id=role_id,
                                            right_key=right)
                    role_right.save()

            return HttpResponse({"message": "update role success",
                                 "statusCode": UI_RESPONSE_OK,
                                 "object_name": getattr(role, 'name', '')},
                                status=UI_RESPONSE_OK)
        except Unauthorized:
            raise
        except Exception, exc:
            LOG.error('Error is %s' % exc)
            return HttpResponse({"message": "update role failed",
                                 "statusCode": UI_RESPONSE_DWZ_ERROR,
                                 "object_name": getattr(role, 'name', '')},
                                status=UI_RESPONSE_ERROR)
    return HttpResponse({"form": form,
                         "statusCode": UI_RESPONSE_DWZ_ERROR,
                         "object_name": getattr(role, 'name', '')},
                        status=UI_RESPONSE_ERROR)


@check_permission('Delete Role')
@require_GET
def delete_role_form(request, role_id):
    """
    :param request:request object
    :return:view<'role_manage/update.html'>::the page for deleting a role
    """
    return shortcuts.render(request,
                            'role_manage/delete.html',
                            {'role_id': role_id})


@require_POST
@UIResponse('Role Manage', 'get_role_list')
def delete_role(request, role_id):
    try:
        role = api.keystone.role_get(request, role_id)
        data = {'enabled': False}
        api.keystone.role_update(request, role_id, **data)
        #        role.delete()
        #        api.keystone.role_delete(request, role_id)
        return HttpResponse({"message": "delete role success",
                             "statusCode": UI_RESPONSE_OK,
                             "object_name": getattr(role, 'name', '')},
                            status=UI_RESPONSE_OK)
    except Unauthorized:
        raise
    except Exception, exc:
        LOG.error('Error is %s' % exc)
        return HttpResponse({"message": 'resume role failed.',
                             "statusCode": UI_RESPONSE_DWZ_ERROR,
                             "object_name": getattr(role, 'name', '')},
                            status=UI_RESPONSE_ERROR)


@check_permission('Resume Role')
@require_GET
def resume_role_form(request, role_id):
    """
    :param request:request object
    :return:view<'role_manage/update.html'>::the page for resume a role
    """
    return shortcuts.render(request,
                            'role_manage/resume.html',
                            {'role_id': role_id})


@require_POST
@UIResponse('Role Manage', 'get_role_list')
def resume_role(request, role_id):
    try:
        data = {'enabled': True}
        role = api.keystone.role_get(request, role_id)
        api.keystone.role_update(request, role_id, **data)
        #        role.delete()
        return HttpResponse({"message": "resume role success",
                             "statusCode": UI_RESPONSE_OK,
                             "object_name": getattr(role, 'name', '')},
                            status=UI_RESPONSE_OK)

    except Unauthorized:
        raise
    except Exception, exc:
        LOG.error('Error is %s' % exc)
        return HttpResponse({"message": 'resume role failed.',
                             "statusCode": UI_RESPONSE_DWZ_ERROR,
                             "object_name": getattr(role, 'name', '')},
                            status=UI_RESPONSE_ERROR)


@require_GET
def index_right(request, role_id):
    """
    :param request:
    :param type:
    :return: The menu list
    """
    role = get_user_role_name(request)
    if not role:
        return HttpResponse('Not Found')
    try:
        right_list = {}
        rights = Right.objects.all().order_by('key')
        list_key = []
        b_parent = {}
        if role_id is not None and role_id != '' and 'None' != role_id:
            role_right = Role_right.objects.filter(role_id=role_id)

            for ro in role_right:
                right_list[ro.right_key] = ro.role_id
            for right in rights:
                if not right_list.has_key(right.key):
                    if list_key.count(right.parent_id) == 0:
                        list_key.append(right.parent_id)

            b_parent['parent'] = list_key
        right_str = ''
        a_parent = {}
        b_body = {}
        back_color = '#F0F3F5'
        num = 0

        for right in rights:
            if right_list.has_key(right.key):
                check_str = "checked='checked'"
            else:
                check_str = ""

            check_box_all = ""
            if right.parent_id == -1:
                num += 1
                if num % 2 == 0:
                    back_color = '#e5eaee'
                else:
                    back_color = '#FFFFFF'
                if b_parent.has_key('parent'):
                    if b_parent['parent'].count(right.id) == 0:
                        check_box_all = "checked='checked'"
                    else:
                        check_box_all = ""

                name = right.name
                if right_menus.has_key(name):
                    name = get_text(right_menus[name])
                else:
                    name = get_text(name)

                a_parent[
                right.id] = "<div><div id='" + right.key + "_div2' class='list_right_div_2'  style='background-color:" + back_color + "'><div id='" + right.key + "_div1' class='list_right_div_1' ><div class='all_div_title' title='" + name + "'>" + name + "</div>"
                a_parent[
                right.id] += "<input type='checkbox' style='float:left;' id='" + right.key + "_title' " + check_box_all + " value='" + right.key + "' /></div><ul id='"\
                             + right.key + "_ul'><li title='" + get_text(
                    right.name) + "'><input type='checkbox' name='rights_list' id='" + right.key + "_input' value='" + right.key + "' " + check_str + " />" + get_text(
                    right.name) + "</li>"

            else:
                if right.key in ['2002','2006']:
                    continue
                name = get_text(right.name)
                if b_body.has_key(right.parent_id):
                    b_body[
                    right.parent_id] += "<li title='" + name + "'><input type='checkbox' name='rights_list' id='" + right.key + "_input' value='" + right.key + "' " + check_str + " />" + name + "</li>"
                else:
                    b_body[
                    right.parent_id] = "<li title='" + name + "'><input type='checkbox' name='rights_list' id='" + right.key + "_input' value='" + right.key + "' " + check_str + " />" + name + "</li>"

        keys_list = a_parent.keys()
        keys_list.sort()

        for c in keys_list:
            right_str += a_parent[c]
            if b_body.has_key(c):
                right_str += b_body[c]
            right_str += "</ul></div></div>"

        if request.is_ajax():
            return HttpResponse(jsonutils.dumps(right_str))
    except Exception, e:
        LOG.error('Can not get list of right,error is %s' % e)
    return shortcuts.render(request, 'control_manage/index.html',
                            {'controllers': rights})


@require_GET
def ajax_checkbox_right(request):
    """
    :param request:
    :param type:
    :return: The menu list
    """
    role = get_user_role_name(request)
    right_id = None
    if "right_id" in request.GET:
        right_id = request.GET['right_id']
    if not role:
        return HttpResponse('Not Found')
    try:
        parent_depends = Right.objects.all()

        rights = parent_depends.filter(key=right_id)
        right = rights[0]
        depend = simplejson.loads(right.depends)
        dict_depend = []
        if '' != depend:
            for dep in depend['depend_keys']:
                if dep in ['2002','2006']:
                    continue
                dict_depend.append(dep)
        for pd in parent_depends:
            if dict_depend.count(pd.key) > 0:
                depend = simplejson.loads(pd.depends)
                if "" != depend:
                    for dep in depend['depend_keys']:
                        if dep in ['2002','2006']:
                            continue
                        if dict_depend.count(dep) == 0:
                            dict_depend.append(dep)

        if request.is_ajax() and len(rights) > 0:
            return HttpResponse(jsonutils.dumps(dict_depend))
    except Exception, e:
        LOG.error('Can not get list of right,error is %s' % e)
    return HttpResponse('Not Found')


@check_permission('View Role')
@require_GET
def get_role_detail(request, role_id):
    host = settings.DATABASES['default']['HOST']
    db = settings.DATABASES['default']['NAME']
    user = settings.DATABASES['default']['USER']
    passwd = settings.DATABASES['default']['PASSWORD']
    conn = MySQLdb.connect(host=host, db=db, user=user, passwd=passwd)
    cur = conn.cursor()
    try:
        # role_rights = Role_right.objects.filter(role_id=role_id)
        sql = "select r.id, r.name, r.parent_id from rights as r where r.key in"\
              "(select rr.right_key from role_right as rr where rr.role_id='%s')" % role_id
        cur.execute(sql)
        rights = cur.fetchall()
        parent_index = {}
        right_list = []
        index = 0
        for right in rights:
            #right[0]:id, right[1]:name, right[2]:parent_id
            if right[2] == -1:
                menu = right_menus[right[1]]
                right_list.append([menu, right[1]])
                parent_index[right[0]] = index
                index += 1
        for right in rights:
            if right[2] != -1:
                p_index = parent_index[right[2]]
                right_list[p_index].append(right[1])

    except Exception, e:
        LOG.error('Can not get right list of role, error is %s' % e)
    cur.close()
    conn.close()
    role = api.keystone.role_get(request, role_id)
    params = {
        'right_list': right_list,
        'role': role,
    }
    return shortcuts.render(request, 'role_manage/detail.html', params)


def get_rights_relation(request):
    role = get_user_role_name(request)
    role_id = None
    if "role_id" in request.GET:
        role_id = request.GET['role_id']
    if not role:
        return HttpResponse('Not Found')
    try:
        role_right_list = Role_right.objects.filter(role_id=role_id)
        d = []
        for rrl in role_right_list:
            d.append(rrl.right_key)
        if request.is_ajax() and len(d) > 0:
            return HttpResponse(jsonutils.dumps(d))
    except Exception, e:
        LOG.error('Can not get list of right,error is %s' % e)
    return HttpResponse('Not Found')


@require_GET
def all_checkbox_right(request):
    """
    :param request:
    :param type:
    :return: The menu list
    """
    role = get_user_role_name(request)
    right_id = None
    if "right_id" in request.GET:
        right_id = request.GET['right_id']
    if not role:
        return HttpResponse('Not Found')
    try:
        rights = Right.objects.filter(key=right_id)
        right = rights[0]
        dict_depend = []
        depend = simplejson.loads(right.depends)
        if '' != depend:
            for dep in depend['depend_keys']:
                if dep in ['2002','2006']:
                    continue
                if dict_depend.count(dep) == 0:
                    dict_depend.append(dep)
        parent_id = right.id
        rights = Right.objects.filter(parent_id=parent_id)
        for rr in rights:
            depend = simplejson.loads(rr.depends)
            if '' != depend:
                for dep in depend['depend_keys']:
                    if dep in ['2002','2006']:
                        continue
                    if dict_depend.count(dep) == 0:
                        dict_depend.append(dep)

        if request.is_ajax() and len(rights) > 0:
            return HttpResponse(jsonutils.dumps(dict_depend))
    except Exception, e:
        LOG.error('Can not get list of right,error is %s' % e)
    return HttpResponse('Not Found')


def checkbox_right_cancel(request):
    """
    :param request:
    :param type:
    :return: The menu list
    """
    role = get_user_role_name(request)
    right_id = None
    if "right_id" in request.GET:
        right_id = request.GET['right_id']
    if not role:
        return HttpResponse('Not Found')
    try:
        rights = Right.objects.all()
        ch_depend = {}
        dict_depend = []
        for rr in rights:
            depend = simplejson.loads(rr.depends)
            if '' != depend:
                for dep in depend['depend_keys']:
                    if dep in ['2002','2006']:
                        continue
                    if dep == right_id:
                        if rr.parent_id == -1:
                            ch_depend[rr.id] = rr.key
                        dict_depend.append(rr.key)

        for rr in rights:
            if dict_depend.count(rr.key) == 0:
                if rr.key in ['2002','2006']:
                    continue
                if ch_depend.has_key(rr.parent_id):
                    dict_depend.append(rr.key)

        if request.is_ajax() and len(rights) > 0:
            return HttpResponse(jsonutils.dumps(dict_depend))
    except Exception, e:
        LOG.error('Can not get list of right,error is %s' % e)
    return HttpResponse('Not Found')
