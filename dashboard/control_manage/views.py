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


__author__ = 'tangjun'
__date__ = '2012-01-24'
__version__ = 'v2.0.1'

import logging

#    code begin
from django import shortcuts
from django.conf import settings
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _
from dashboard import exceptions
from django.views.decorators.http import require_GET, require_http_methods

from dashboard import api
from dashboard.authorize_manage import ROLE_ADMIN
from dashboard.authorize_manage.utils import get_user_role_name
from dashboard.authorize_manage.utils import switch_tenants
from dashboard.exceptions import NotFound, Unauthorized
from dashboard.utils import jsonutils
from dashboard.utils import UI_RESPONSE_NOTFOUND
from dashboard.utils.decorators import require_auth

from .models import Controller


if settings.DEBUG:
    __log__ = 'v2.0.1 create'

LOG = logging.getLogger(__name__)


@require_GET
@require_auth
def index_controller(request, type='menu'):
    """
    :param request:
    :param type:
    :return: The menu list
    """
    role = get_user_role_name(request)
    if not role:
        return HttpResponse('Not Found')
    try:
        if type == 'menu':
            controllers = Controller.objects.filter(action_type='menu',
                role=role)
        elif type == 'action':
            controllers = Controller.objects.filter(action_type='menu',
                role=role)
        else:
            if role == ROLE_ADMIN:
                controllers = Controller.objects.all()
            else:
                controllers = Controller.objects.filter(role=role)

        if request.is_ajax():
            return HttpResponse(jsonutils.dumps(controllers))
    except Exception, e:
        LOG.error('Can not get list of controllers,error is %s' % e)
    return shortcuts.render(request, 'control_manage/index.html',
        {'controllers': controllers})


@require_http_methods(['DELETE'])
def delete_controller(request, controller_id):
    try:
        controller = Controller.objects.get(id=int(controller_id))
        controller.delete()
    except Exception, e:
        LOG.error('Can not delete controller =%s,error is %s' % (
        controller_id, e.message))
    return shortcuts.redirect('get_controller_index')

@require_GET
def reboot_instance_client(request, project_id ,instance_id):
    if request.is_ajax():
        switch_tenants(request, project_id)
        try:
            instance = api.server_get(request, instance_id)
            instance_status = instance.status
            if instance_status.lower() in ('active', 'suspend', 'shutoff',):
                api.server_reboot(request, instance_id)
                instance_next = api.server_get(request, instance_id)
                return HttpResponse(jsonutils.dumps({instance_id: 'success',
                                                     "status": getattr(instance_next, 'status', 'None')}))
            else:
                LOG.info('Can not reboot instance,the status is wrong!')
                return HttpResponse(jsonutils.dumps({instance_id: 'failed'}))
        except Unauthorized:
            raise
        except exceptions.NotFound, e:
            msg = _('Can not found instance (%s)') % instance_id
            LOG.error(msg)
            return HttpResponse(jsonutils.dumps({instance_id: 'failed'}))

        except Exception, e:
            LOG.error('Can not reboot instance!')
            return HttpResponse(jsonutils.dumps({instance_id: 'failed'}))


@require_GET
def stop_instance_client(request, project_id,instance_id):
    if request.is_ajax():
        switch_tenants(request, project_id)
        try:
            instance = api.server_get(request, instance_id)
            instance_status = instance.status
            if instance_status.lower() in ('active',):
                api.server_suspend(request, instance_id)
                instance_next = api.server_get(request, instance_id)
                return HttpResponse(jsonutils.dumps({instance_id: 'success',
                                                     "status": getattr(instance_next, 'status', 'None')}))
            else:
                LOG.info(_('Can not suspend instance,the status is wrong!'))
                return HttpResponse(jsonutils.dumps({instance_id: 'failed'}))
        except Unauthorized:
            raise
        except exceptions.NotFound, e:
            msg = _('Can not found instance (%s)') % instance_id
            LOG.error(msg)
            return HttpResponse(jsonutils.dumps({instance_id: 'failed'}))

        except Exception, e:
            LOG.error('Can not suspend instance!')
            return HttpResponse(jsonutils.dumps({instance_id: 'failed'}))


@require_GET
def unstop_instance_client(request,project_id, instance_id):
    if request.is_ajax():
        switch_tenants(request, project_id)
        try:
            instance = api.server_get(request, instance_id)
            instance_status = instance.status
            if instance_status.lower() in ('suspended',):
                api.server_resume(request, instance_id)
                instance_next = api.server_get(request, instance_id)
                return HttpResponse(jsonutils.dumps({instance_id: 'success',
                                                     "status": getattr(instance_next, 'status', 'None')}))
            else:
                LOG.info(_('Can not reboot instance,the status is wrong!'))
                return HttpResponse(jsonutils.dumps({instance_id: 'failed'}))
        except Unauthorized:
            raise
        except exceptions.NotFound, e:
            msg = _('Can not found instance (%s)') % instance_id
            LOG.error(msg)
            return HttpResponse(jsonutils.dumps({instance_id: 'failed'}))

        except Exception, e:
            LOG.error('Can not resume instance. %s' % e)
            return HttpResponse(jsonutils.dumps({instance_id: 'failed'}))

@require_GET
def get_client_instance_status(request, project_id, instance_id):
    """
    :param request: request object
    :param instance_id: the instance id
    :return: the instance's status
    """
    if request.is_ajax():
        switch_tenants(request, project_id)
        try:
            instance = api.server_get(request, instance_id)
        except Unauthorized:
            raise
        except exceptions.ClientException:
            return HttpResponse(content=instance_id, status=UI_RESPONSE_NOTFOUND)
        return HttpResponse(
            jsonutils.dumps({instance_id: getattr(instance, 'status',
                'None')}))
    raise NotFound


@require_GET
def get_client_instance_task(request,project_id, instance_id):
    """
    :param request: request object
    :param instance_id: the instance id
    :return: the instance's task
    """
    if request.is_ajax():
        switch_tenants(request, project_id)
        try:
            instance = api.server_get(request, instance_id)
        except Unauthorized:
            raise
        except exceptions.ClientException:
            return HttpResponse(content=instance_id, status=UI_RESPONSE_NOTFOUND)
        return HttpResponse(jsonutils.dumps(
            {instance_id: getattr(instance, 'OS-EXT-STS:task_state', 'None')}))
    raise NotFound


@require_GET
def get_client_instance_power(request, project_id, instance_id):
    """
    :param request: request object
    :param instance_id: the instance id
    :return: the instance's power
    """
    if request.is_ajax():
        switch_tenants(request, project_id)
        try:
            instance = api.server_get(request, instance_id)
        except Unauthorized:
            raise
        except exceptions.ClientException:
            return HttpResponse(content=instance_id, status=UI_RESPONSE_NOTFOUND)
        if 1 == getattr(instance, 'OS-EXT-STS:power_state', 'None'):
            setattr(instance, 'power_state', 'Running')
        elif 3 == getattr(instance, 'OS-EXT-STS:power_state', 'None'):
            setattr(instance, 'power_state', 'Paused')
        elif 5 == getattr(instance, 'OS-EXT-STS:power_state', 'None'):
            setattr(instance, 'power_state', 'Suspended')
        else:
            setattr(instance, 'power_state', 'No state')
        return HttpResponse(jsonutils.dumps(
            {instance_id: getattr(instance, 'power_state', 'None')}))
    raise NotFound


