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
import sys

reload(sys)

import csv

from django.conf import settings

if settings.DEBUG:
    __log__ = 'v2.0.1 create'

import logging

LOG = logging.getLogger(__name__)

#    code begin
import dateutil.parser
import os, zipfile
from datetime import datetime

from django import shortcuts
from django.db import connection, transaction
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponse

from dashboard.utils import UIResponse, Pagenation, jsonutils, check_permission
from dashboard.utils.i18n import get_text
from dashboard.utils.ui import UI_RESPONSE_DWZ_ERROR, UI_RESPONSE_DWZ_SUCCESS, UI_RESPONSE_ERROR
from dashboard.log_manage.models import LoggingAction
from dashboard.log_manage import utils
from dashboard.authorize_manage.utils import get_user_role_name, get_user_role_id
from dashboard.exceptions import Unauthorized
from dashboard.authorize_manage import  ROLE_ADMIN
from dashboard.role_manage.api import assert_role_right

#Just as an argument
#begin
LOG_LIST_FILE_LINES = 65535
#end


@check_permission('Delete Log')
@require_http_methods(['DELETE'])
@UIResponse('Log Query', 'log_query_index')
def delete_logs_query(request):
    """
    Clean all logs for system.
    :param request:request object,user_id
    :return:
    """
    try:
        cursor = connection.cursor()
        sql_where_str = utils.log_search_str(request)
        role_id = get_user_role_id(request)
        right_val = assert_role_right(role_id, 'View All Logs')
        sql = "DELETE FROM log_manage_loggingaction WHERE 1=1 "
        tenantid = request.user.tenant_id
        if not right_val:
            sql = sql +"and tenantid = '" + tenantid + "'"
        if sql_where_str == '':
            cursor.execute(sql)
        else:
            cursor.execute(sql + sql_where_str)

        transaction.commit_unless_managed()
    except Exception, exc:
        msg = _('Unable to clean logs.')
        LOG.error('Unable to clean logs, %s.' % exc)
        return HttpResponse(
            {"message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR},
            status=UI_RESPONSE_ERROR)

    return HttpResponse({"message": "delete logs success",
                         "statusCode": UI_RESPONSE_DWZ_SUCCESS},
                        status=UI_RESPONSE_DWZ_SUCCESS)


@check_permission('Delete Log')
@require_GET
def delete_log_form(request, uuid=None):
    return shortcuts.render(request, 'log_manage/delete_log_form.html',
                            {'uuid': uuid})


@check_permission('Delete Log')
@require_http_methods(['DELETE'])
@UIResponse('Log Query', 'log_query_index')
def delete_log(request, uuid):
    """
    Delete one log.
    :param request:request object;create_at:the create_at item for the log
    :return:
    """
    try:
        log = LoggingAction.objects.get(uuid=uuid)
        log.delete()
    except Exception, exc:
        msg = _('Unable to clean log.')
        LOG.error('Unable to clean log, %s.' % exc)
        return HttpResponse(
            {"message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR},
            status=UI_RESPONSE_ERROR)
    return HttpResponse({"message": "delete log success",
                         "statusCode": UI_RESPONSE_DWZ_SUCCESS},
                        status=UI_RESPONSE_DWZ_SUCCESS)


def get_log_detail(request, uuid=None):
    try:
        log = LoggingAction.objects.filter(uuid=uuid)

        if log:
            log = log[0]
        else:
            log = []
    except Exception, exc:
        LOG.error('Unable to retrieve log list,%s.' % exc)
        log = []

    return shortcuts.render(request, 'log_manage/log_detail.html', {'log': log})


def log_query_home_page(request):
    """
    :param request: request object
    :return: view <'log_manage/query_index.html'> of the log list
    """
    tenant_name = request.user.tenant_name
    log_lists = LoggingAction.objects.order_by('-create_at').all()
    if tenant_name is not None and tenant_name != '':
        log_lists = log_lists.filter(tenant=tenant_name).order_by('-create_at')

    return shortcuts.render(request, "log_manage/log_home.html", {"form_list":log_lists[:11]})


LOG_MODULE_LIST = {0:'Common Manage',
                        1:'Instance Manage',
                        2:'Image Manage',
                        3:'HardTemplate Manage',
                        4:'Foundation Manage',
                        5:'Volume Manage',
                        6:'Software Manage',
                        7:'Authorization Manage',
                        8:'User Manage',
                        9:'Virtual NetWork Manage',
                        10:'Virtual Routers Manage',
                        11:'Virtual Address Manage',
                        12:'Network Security Manage',
                        13:'Notice Manage'}
PROJECTADMIN_LOG_MODULE_LIST = {
                        0:'Common Manage',
                        1:'Instance Manage',
                        2:'Image Manage',
                        3:'Volume Manage',
                        4:'Software Manage',
                        5:'Authorization Manage',
                        6:'User Manage',
                        7:'Virtual NetWork Manage',
                        8:'Virtual Routers Manage',
                        9:'Virtual Address Manage',
                        10:'Network Security Manage',
                        11:'Notice Manage'}


@check_permission('View Own Logs')
@require_GET
@Pagenation('log_manage/query_index.html')
def log_query_index(request):
    """
    :param request: request object
    :return: view <'log_manage/query_index.html'> of the log list
    """
    module_choices = []
    role_name = ROLE_ADMIN
    log_lists = None
    event_choices = [('add', get_text('add')), ('edit', get_text('edit')),
                     ('del', get_text('del')), ('login', get_text('login')),
                     ('logout', get_text('logout'))]
    try:
        role_name = get_user_role_name(request)
        log_conf_info = LOG_MODULE_LIST
        for log_index in range(len(log_conf_info)):
            module_choice = (log_conf_info[log_index],
                             get_text(log_conf_info[log_index]))
            if module_choices.count(module_choice) < 1:
                module_choices.append(module_choice)
        log_lists = get_log_list(request)
    except Unauthorized:
        raise
    except Exception, exc:
        LOG.error("error is %s." % exc)
    args = {}
    username = ''
    module = ''
    event = ''
    tenant_name = ''
    begin_time = ''
    end_time = ''

    if request.GET.has_key('username'):
        username = request.GET['username']
        if username != '':
            log_lists = log_lists.filter(username__contains=username)

    if request.GET.has_key('module'):
        module = request.GET['module']
        if module != '':
            log_lists = log_lists.filter(module=module)

    if request.GET.has_key('event'):
        event = request.GET['event']
        if event != '':
            log_lists = log_lists.filter(event=event)

    if request.GET.has_key('tenant'):
        tenant_name = request.GET['tenant']
        if tenant_name != '':
            log_lists = log_lists.filter(tenant__contains=tenant_name)

    if request.GET.has_key('begintime'):
        begin_time = request.GET['begintime']
        if begin_time != '':
            log_lists = log_lists.filter(
                create_at__gte=(dateutil.parser.parse(begin_time) - abs(
                    datetime.now() - datetime.utcnow())))

    if request.GET.has_key('endtime'):
        end_time = request.GET['endtime']
        if end_time != '':
            log_end_time = dateutil.parser.parse(end_time)
            log_end_time = log_end_time.replace(hour=23, minute=59, second=59)
            log_end_time -= abs(datetime.now() - datetime.utcnow())
            log_lists = log_lists.filter(create_at__lte=log_end_time)
    log_lists = log_lists.order_by('-create_at')

    args['list'] = log_lists
    args['username'] = username
    args['module_choices'] = module_choices
    args['event_choices'] = event_choices
    args["tenant"] = tenant_name
    args["module"] = module
    args["event"] = event
    args["begintime"] = begin_time
    args["endtime"] = end_time
    args["role"] = role_name
    return args


def export_logs_count(request):
    log_lists = logs_list_same(request)
    log_list_len = len(log_lists)
    if log_list_len < 1:
        return HttpResponse(jsonutils.dumps(
            {"message": get_text('Can not export logs'), "statusCode": 300}))
    return HttpResponse(jsonutils.dumps({"message": '', "statusCode": 200}))


@check_permission('Export Log List')
@require_GET
def export_logs_list(request):
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

    head_array = [get_text('module'), get_text('event'), get_text('content'), get_text('create_at'), get_text('user_name'),
                  get_text('tenant_name'), get_text('is_primary')]
    #Windows system
    if out_os == 2:
        head_array = [head_w.encode('GBK') + "        " for head_w in head_array]
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
                content_array = [ get_text(log.module),
                                 log.event,
                                 log.content,
                                 str(dateutil.parser.parse(log.create_at) + abs(
                    datetime.now() - datetime.utcnow()))[:16],
                                 log.username,
                                 log.tenant,
                                 log.is_primary]
                #Windows system
                if out_os == 2:
                    content_array = [c_arr.encode('GBK') + "        " for c_arr in content_array]
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

    return resp


def logs_list_same(request):

    log_lists = get_log_list(request)

    if request.GET.has_key('username'):
        username = request.GET['username']
        if username != '':
            log_lists = log_lists.filter(username__contains=username)

    if request.GET.has_key('module'):
        module = request.GET['module']
        if module != '':
            log_lists = log_lists.filter(module=module)

    if request.GET.has_key('event'):
        event = request.GET['event']
        if event != '':
            log_lists = log_lists.filter(event=event)

    if request.GET.has_key('tenant'):
        tenant_name = request.GET['tenant']
        if tenant_name != '':
            log_lists = log_lists.filter(tenant__contains=tenant_name)

    if request.GET.has_key('begintime'):
        begin_time = request.GET['begintime']
        if begin_time != '':
            log_lists = log_lists.filter(
                create_at__gte=(dateutil.parser.parse(begin_time)
                                - abs(datetime.now() - datetime.utcnow())))

    if request.GET.has_key('endtime'):
        end_time = request.GET['endtime']
        if end_time != '':
            log_end_time = dateutil.parser.parse(end_time)
            log_end_time = log_end_time.replace(hour=23, minute=59, second=59)
            log_end_time -= abs(datetime.now() - datetime.utcnow())
            log_lists = log_lists.filter(create_at__lte=log_end_time)

#    log_lists = log_lists.filter(tenant=request.user.tenant_name)
    return log_lists

# add by yangzhi 2013.11.28
def get_log_list(request):
    role_id = get_user_role_id(request)
    right_val = assert_role_right(role_id, 'View All Logs')
    tenant_id = request.user.tenant_id
    if right_val:
        log_lists = LoggingAction.objects.order_by('-create_at').all()
    else:
        log_lists = LoggingAction.objects.filter(tenantid=tenant_id)
    return log_lists