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

__author__ = 'tangjun'
__date__ = '2013-02-18'
__version__ = 'v2.0.2'

import datetime
import logging
import md5

from django import shortcuts
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.http import HttpResponse
from django.utils.timezone import utc
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_GET, require_POST,\
    require_http_methods

from dashboard.api import get_host_monitor
from dashboard.api.monitor import VoyageMonitor, VoyageClientException
from dashboard.node_manage.models import Node
from dashboard.node_manage.forms import NodeForm
from dashboard.utils import jsonutils, time
from dashboard.utils import UIResponse, ui_response, Pagenation,\
    UI_RESPONSE_NOTFOUND, UI_RESPONSE_BADREQUEST,\
    UI_RESPONSE_ERROR, UI_RESPONSE_OK, UI_RESPONSE_DWZ_ERROR,\
    UI_RESPONSE_DWZ_SUCCESS
from dashboard.utils import check_permission


if settings.DEBUG:
    __log__ = """v2.0.1 create [2013-01-14]
    V2.0.2 [add]: Get monitor information of node [2013-02-18]
    """

LOG = logging.getLogger(__name__)

def get_available_nodes(nodes):
    """

    :param nodes:
    :param host_tree:
    :return:
    """
    available_nodes = {}
    host_tree = []
    for node in nodes:
        available_nodes[node.name] = node.uuid
        host_tree.append(node.to_simple_express())
    return available_nodes, host_tree


def get_nodes(request):
    """

    :param request:
    :return:
    """
    try:
        nodes = Node.objects.all()
        for node in nodes:
            setattr(node, 'status_link', reverse('get_node_monitor_info_item',
                                                 args=[node.uuid,
                                                       'check_status']))

    except Exception, exp:
        msg = 'Can not get list of nodes,error is %s' % exp
        LOG.error(msg)
        nodes = None

    return nodes


@require_GET
@check_permission('View Node')
@Pagenation('node_manage/index.html')
def index_node(request):
    """
    :param request: request Object
    :return:
    """
    args = {}
    nodes = get_nodes(request) or []
    args['list'] = nodes
    return args


@require_GET
def create_node(request):
    """
    :param request:request Object
    :return:
    """
    form = NodeForm(request, None)
    return shortcuts.render(request, 'node_manage/create.html', {'form': form})

#: Modify by lingkang 2013-03-14 auto refresh after doing sth
@require_POST
@check_permission('Add Node')
@UIResponse('Foundation Manage', 'get_node_index')
def create_node_action(request):
    """
    :param request:request Object
    :return:
    """
    node_form = NodeForm(request, None, request.POST)
    if node_form.is_valid():
        data = node_form.cleaned_data
        created_at = datetime.datetime.now(tz=utc)
        uuid = md5.new(str(created_at)).hexdigest()
        control_nodes = Node.objects.filter(type='control_node')
        if control_nodes.__len__() > 0 and data['type'] == 'control_node':
            msg = 'control node has already exist'
            return HttpResponse(
                {"message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR},
                status=UI_RESPONSE_ERROR)

        try:
            node = Node(uuid=uuid, name=data['host_name'], ip=data['host_ip'],
                        type=data['type'], created_at=created_at)
            node.save()
        except IntegrityError:
            msg = 'IP %s has already exist' % data['ip']
            return HttpResponse(
                {"message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR},
                status=UI_RESPONSE_ERROR)

        except Exception, exp:
            debug_info = 'Can not create node,error is %s' % exp
            LOG.error(debug_info)
            msg = 'Create node failed, please retry later.'
            return HttpResponse(
                {"message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR},
                status=UI_RESPONSE_ERROR)

        return HttpResponse({"message": "Create node Success",
                             "statusCode": UI_RESPONSE_DWZ_SUCCESS,
                             "object_name": data['host_name']},
                            status=UI_RESPONSE_OK)
    else:
        return HttpResponse({"form": node_form, "message": "",
                             "statusCode": UI_RESPONSE_DWZ_ERROR},
                            status=UI_RESPONSE_ERROR)


@require_GET
def update_node(request, node_uuid):
    """
    :param request: request Object
    :param node_uuid: the uuid of node which will show in table
    :return:
    """
    try:
        node = Node.objects.get(uuid=node_uuid)
    except Node.DoesNotExist:
        return HttpResponse(
            _('Can not get node (uuid=%s) information') % node_uuid)
    node_form = NodeForm(request, node_uuid, node.get_values())
    return shortcuts.render(request, 'node_manage/update.html',
                            {'form': node_form, 'uuid': node_uuid})


@require_POST
def update_node_action(request, node_uuid):
    """
    :param request: request Object
    :param node_uuid: the uuid of node whichj will be updated
    :return:
    """
    node_form = NodeForm(request, node_uuid, request.POST)
    if node_form.is_valid():
        data = node_form.cleaned_data
        control_nodes = Node.objects.filter(type='control_node').exclude(
            uuid=node_uuid)
        if control_nodes.__len__() > 0 and data['type'] == 'control_node':
            msg = 'control node has already exist'
            return HttpResponse(jsonutils.dumps(ui_response(message=msg)))

        try:
            node = Node.objects.get(uuid=node_uuid)
            node.name = data['name']
            node.passwd = data['passwd']
            node.ip = data['ip']
            node.type = data['type']
            node.save()
        except Node.DoesNotExist:
            msg = 'Can not get node (uuid=%s) information' % node_uuid
            return HttpResponse(jsonutils.dumps(ui_response(message=msg)))

        except Exception, exp:
            err_msg = 'Can not update node uuid=%s,error is %s' % (node_uuid,
                                                                   exp)
            LOG.error(err_msg)
            msg = 'update node uuid=%s failed, please retry later.' % node_uuid
            return HttpResponse(jsonutils.dumps(ui_response(message=msg)))

        return HttpResponse(jsonutils.dumps(
            ui_response(node_form, message="Update node Success",
                        object_name=node.name)))
    else:
        return HttpResponse(jsonutils.dumps(ui_response(node_form)))


@require_GET
@check_permission('Delete Node')
def delete_node_form(request, node_uuid):
    """
    :param request:
    :param node_uuid:
    :return:
    """
    return shortcuts.render(request, 'node_manage/delete.html',
                            {'node_uuid': node_uuid})

#: Modify by lingkang 2013-03-14 auto refresh after doing sth
@require_http_methods(['DELETE'])
@check_permission('Delete Node')
@UIResponse('Foundation Manage', 'get_node_index')
def delete_node(request, node_uuid):
    """
    :param request: request Object
    :param node_uuid: the uuid of node which will be deleted
    :return:
    """
    try:
        controller = Node.objects.get(uuid=node_uuid)
        controller.delete()
    except Exception, exp:
        err_msg = 'Can not delete node uuid=%s,error is %s' % (node_uuid, exp)
        LOG.error(err_msg)
        msg = 'Can not delete node uuid=%s' % node_uuid
        return HttpResponse(
            {"message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR},
            status=UI_RESPONSE_ERROR)

    return HttpResponse({"message": "delete node success",
                         "statusCode": UI_RESPONSE_DWZ_SUCCESS,
                         "object_name": controller.name}, status=UI_RESPONSE_OK)


def get_node_monitor_info_item(request, node_uuid, host_id):
    """
    :param request:
    :param node_uuid:
    :param host_id:
    :return:
    """
    try:
        node = Node.objects.get(uuid=node_uuid)
        client = VoyageMonitor()
        try:
            all_services_status = client.check_load(request.user.tenant_id,
                                                    request.user.token.id,
                                                    host_id, node_uuid)
            return HttpResponse(jsonutils.dumps(
                {node_uuid: all_services_status, "name": node.name}))
        except VoyageClientException:
            LOG.error('Voyage service can not connect.')
            return HttpResponse('Not Found')
    except Exception, exp:
        msg = 'Get monitor info error, reason: %s' % (exp)
        LOG.error(msg)
        return HttpResponse('Not Found')


@require_GET
#@check_permission('index_node')
def get_all_hosts_status(request):
    """
    :param request:
    :return:
    """
    client = VoyageMonitor()
    try:
        status = client.get_host_status(tenant_id=request.user.tenant_id,
                                        token=request.user.token.id)
        return HttpResponse(jsonutils.dumps(status))
    except VoyageClientException:
        LOG.error('Voyage service can not connect.')
        return HttpResponse('Not Found')


@require_GET
#@check_permission('index_node')
def get_host_metadata(request):
    """
    :param request:
    :return:
    """
    client = VoyageMonitor()
    try:
        hosts = client.get_host_list(tenant_id=request.user.tenant_id,
                                     token=request.user.token.id)
        return HttpResponse(jsonutils.dumps(hosts))
    except VoyageClientException:
        LOG.error('Voyage service can not connect.')
        return HttpResponse('Not Found')
