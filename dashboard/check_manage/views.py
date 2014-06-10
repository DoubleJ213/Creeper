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
__date__ = '2013-11-08'
__version__ = 'v3.1.3'

import copy
import logging
import json
import datetime

from django import shortcuts
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import utc

from dashboard import api
from dashboard.exceptions import Unauthorized, LicenseForbidden
from dashboard.instance_manage.models import Distribution
from dashboard.utils import UIResponse, Pagenation, check_permission
from dashboard.utils.ui import UI_RESPONSE_DWZ_ERROR, UI_RESPONSE_DWZ_SUCCESS, UI_RESPONSE_ERROR, UI_RESPONSE_OK

#from .forms import CreateRoleForm, UpdateRoleForm
from .models import Task
from .forms import TaskCheckForm
from .models import PENDING, APPROVE, REJECT, EXPIRED

if settings.DEBUG:
    __log__ = 'v2.0.1 create'
LOG = logging.getLogger(__name__)


@check_permission('View Task')
@require_GET
@Pagenation('check_manage/index.html')
def get_task_list(request):
    args = {}
    status = request.GET.get('status', PENDING)
    #refresh tab
    if status == '${param.status}':
        status = PENDING

    tasks = Task.objects.filter(status=status, deleted=False)
    try:
        if status == PENDING:
            now = datetime.datetime.now(tz=utc)

            _tasks = []
            for task in tasks:
                if task.expire_time <= now:
                    task.status = EXPIRED
                    task.save()
                else:
                    _tasks.append(task)
            args['list'] = _tasks
        else:
            args['list'] = tasks
    except Exception, exc:
        LOG.error('Error is %s' % exc)

    return args

@check_permission('Check Task')
@require_GET
def get_task_form(request, task_id):
    form = TaskCheckForm(request, task_id)
    try:
        task = Task.objects.get(uuid=task_id)
        params = {
            'form': form,
            'task': task,
        }
        return shortcuts.render(request, 'check_manage/task_check.html', params)
    except Exception, exc:
        LOG.error('Error is %s' % exc)
        raise


class ProxyRequest(object):
    def __init__(self, username, user_id, project_id, token_id, catalog, meta, old_tenant_id):
        self.user = self.User(username, user_id, project_id, token_id, catalog, old_tenant_id)
        self.META = copy.copy(meta)

    class User(object):
        def __init__(self, username, user_id, project_id, token_id, catalog, old_tenant_id):
            self.username = username
            self.id = user_id
            self.tenant_id = project_id
            self.token = self.Token(token_id)
            self.service_catalog = copy.deepcopy(catalog)
            self._fix_catalog(old_tenant_id)

        def _fix_catalog(self, old_tenant_id):
            for catalog in self.service_catalog:
                for endpoint in catalog['endpoints']:
                    for key, value in endpoint.items():
                        endpoint[key] = value.replace(old_tenant_id, self.tenant_id)

        class Token(object):
            def __init__(self, token_id):
                self.id = token_id


@check_permission('Check Task')
@require_POST
@UIResponse('Check Manage', 'get_task_list')
def check_task(request, task_id):
    status = request.POST.get('check', PENDING)
    check_comment = request.POST.get('check_comment', '')

    if status not in (APPROVE, REJECT,):
        return HttpResponse({"message": 'Check task failed',
                             "statusCode": UI_RESPONSE_DWZ_ERROR},
                            status=UI_RESPONSE_ERROR)

    task = None
    try:
        task = Task.objects.get(uuid=task_id, deleted=False)
        if status == APPROVE:
            if task.status == EXPIRED:
                return HttpResponse({"message": 'The task expired.',
                                     "statusCode": UI_RESPONSE_DWZ_ERROR},
                                    status=UI_RESPONSE_ERROR)

            proxy_req = ProxyRequest(task.user_name, task.user_id,
                                     task.project_id, task.token_id,
                                     request.user.service_catalog,
                                     request.META, request.user.tenant_id)

            args = json.loads(task.args)
            kwargs = json.loads(task.kwargs)

            res = api.functions.get(task.api)(proxy_req, *args, **kwargs)

            post_api(res, task)

        task.status = status
        task.check_comment = check_comment
        task.save()
    except Unauthorized:
        if task:
            task.status = EXPIRED
            task.save()
        return HttpResponse(content=_('The task expired'),
                            status=401)
    except LicenseForbidden:
        raise
    except Exception, e:
        LOG.error(e)
        return HttpResponse({"message": 'Check task failed',
                             "statusCode": UI_RESPONSE_DWZ_ERROR},
                            status=UI_RESPONSE_ERROR)
    return HttpResponse({"message": 'Check task success',
                         "statusCode": UI_RESPONSE_OK},
                        status=UI_RESPONSE_OK)


def post_api(res, task):
    if task.api == 'server_create':
        instance_id = res.id
        user_id = json.loads(task.creeper_args)
        if user_id:
            _relationship = Distribution(instance_id=instance_id,
                                         user_id=user_id)
            _relationship.save()



@require_GET
def get_user_task_list(request):
    tasks = None
    try:
        tasks = Task.objects.filter(user_id=request.user.id, deleted=False).order_by('-submit_time')
        return shortcuts.render(request, "check_manage/task_item.html",
            {"task_list": tasks[:6]})
    except Exception, exc:
        LOG.error('Error is :%s' % exc)

        return shortcuts.render(request, "check_manage/task_item.html",
            {"task_list": tasks[:6]})


@require_GET
@Pagenation('check_manage/task_index.html')
def get_user_task_list_all(request):
    args = {}
    tasks = None
    try:
        tasks = Task.objects.filter(user_id=request.user.id, deleted=False).order_by('-submit_time')
    except Exception, exc:
        LOG.error('Error is :%s' % exc)
    args['list'] = tasks
    return args



@require_GET
def task_detail(request, task_id):
    task = None
    try:
        task = Task.objects.filter(id=task_id)[0]
    except Exception, exc:
        LOG.error('Error is %s' % exc)
    return shortcuts.render(request, "check_manage/task_detail.html",
        {"task": task})

@require_GET
def resubmit_task_form(request, task_id):
    form = TaskCheckForm(request, task_id)
    return shortcuts.render(request,'check_manage/task_resubmit.html',
        {'form':form, 'task_id': task_id})

@require_POST
@UIResponse('Check Manage', 'get_user_task_list_all')
def resubmit_task_action(request, task_id):
    task = None
    submit_time = datetime.datetime.now(tz=utc)
    try:
        task = Task.objects.get(id=task_id)
        resume_num = task.resume_num
        if resume_num > 2:
            msg = "Resume number has touch the max number."
            return HttpResponse({"message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR},
                status=UI_RESPONSE_ERROR)
        check_comment = request.POST.get('check_comment', '')
        task.check_comment = check_comment
        task.token_id = request.user.token.id
        task.resume_num = resume_num + 1
        task.status = PENDING
        task.submit_time = submit_time
        task.expire_time = submit_time+datetime.timedelta(hours=24)
        task.save()
        return HttpResponse({"message": "Resubmit task successfully.",
                             "statusCode": UI_RESPONSE_OK,
                             "object_name": getattr(task, 'name', '')},
            status=UI_RESPONSE_OK)

    except Unauthorized:
        raise
    except Exception, exc:
        LOG.error('Error is %s' % exc)

    return HttpResponse({"message": 'Failed to resubmit task.',
                         "statusCode": UI_RESPONSE_DWZ_ERROR,
                         "object_name": getattr(task, 'name', '')},
        status=UI_RESPONSE_ERROR)


@require_GET
def delete_task_form(request, task_id):
    return shortcuts.render(request,
        'check_manage/task_delete.html',
        {'task_id': task_id})

@require_http_methods(['DELETE'])
@UIResponse('Check Manage', 'get_user_task_list_all')
def delete_task_action(request, task_id):
#    task = None
#    try:
#        task = Task.objects.get(id=task_id)
    try:
        task = Task.objects.get(id=task_id)
        task.deleted = True
        task.save()
    except Exception, exc:
        msg = _('Unable to delete the task.')
        LOG.error('Unable to delete the task, %s.' % exc)
        return HttpResponse(
            {"message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR},
            status=UI_RESPONSE_ERROR)
    return HttpResponse({"message": "Delete success",
                         "statusCode": UI_RESPONSE_DWZ_SUCCESS}, status=UI_RESPONSE_DWZ_SUCCESS)
