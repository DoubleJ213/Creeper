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
__date__ = '2013-02-22'
__version__ = 'v2.0.2'

import logging
import datetime
from calendar import monthrange

from django import shortcuts
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.http import require_GET, require_POST
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.utils.datastructures import SortedDict

from dashboard import api
from dashboard.api.monitor import VoyageMonitor, VoyageClient
from dashboard.exceptions import Unauthorized
from dashboard.instance_manage.utils import get_instances,\
    get_instance_simple_express
from dashboard.node_manage.models import Node
from dashboard.node_manage.views import get_nodes
from dashboard.node_manage.views import get_available_nodes
from dashboard.utils import jsonutils, UI_RESPONSE_BADREQUEST, UI_RESPONSE_ERROR
from dashboard.utils import check_permission
from dashboard.utils.i18n import get_text

if settings.DEBUG:
    __log__ = """v2.0.1 create """

LOG = logging.getLogger(__name__)

def get_start(year, month, day=1):
    """

    :param year:
    :param month:
    :param day:
    :return:
    """
    start = datetime.datetime(year, month, day, 0, 0, 0)
    return timezone.make_aware(start, timezone.utc)


def get_end(year, month, day=1):
    """

    :param year:
    :param month:
    :param day:
    :return:
    """
    days_in_month = monthrange(year, month)[1]
    period = datetime.timedelta(days=days_in_month)
    end = get_start(year, month, day) + period
    # End our calculation at midnight of the given day.
    date_end = datetime.datetime.combine(end, datetime.time(0, 0, 0))
    date_end = timezone.make_aware(date_end, timezone.utc)
    if date_end > timezone.now():
        date_end = timezone.now()
    return date_end


def get_date_range():
    """

    :return:
    """
    year = timezone.now().year
    month = timezone.now().month
    start = get_start(year, month)
    end = get_end(year, month)
    return start, end


def get_simple_express(request, usage_list):
    """

    :param request:
    :param usage_list:
    :return:
    """
    value = []
    try:
        tenants = api.keystone.tenant_list(request, admin=True)
    except Unauthorized:
        raise
    except Exception, exp:
        tenants = []
        msg = 'Unable to retrieve instance tenant information. reason: '\
              '%s' % exp
        LOG.error(msg)

    for usage in usage_list:
        usage_info = usage.get_summary()
        tenant_dict = SortedDict([(t.id, t) for t in tenants])
        tenant = tenant_dict.get(getattr(usage, 'tenant_id', None), None)
        if tenant:
            usage_info['tenant_name'] = getattr(tenant, "name", None)
            usage_info['tenant_id'] = getattr(usage, 'tenant_id', None)
            value.append(usage_info)
    return value


@require_GET
def get_system_usage(request):
    """

    :param request:
    :return:
    """
    try:
        start, end = get_date_range()
        usage_list = api.usage_list(request, start, end)
        return HttpResponse(
            jsonutils.dumps(get_simple_express(request, usage_list)))
    except Unauthorized:
        raise
    except Exception, exp:
        msg = 'Cat not get system usage, reason: %s' % (exp.message)
        LOG.error(msg)
        return HttpResponse('Not Found')


@require_GET
def get_tenant_usage_details(request, tenant_id):
    """

    :param request:
    :param tenant_id:
    :return:
    """
    try:
        start, end = get_date_range()
        usage = api.usage_get(request, tenant_id, start, end)
        return HttpResponse(jsonutils.dumps(usage))
    except Exception, exp:
        msg = 'Can not get usage of tenant, reason: %s' % (exp.message)
        LOG.error(msg)
        return HttpResponse('Not Found')


@require_GET
def get_host_tree(request):
    """

    :param request:
    :return:
    """
    json_object = {}
    nodes = get_nodes(request)
    if nodes:
        available_nodes, host_tree = get_available_nodes(nodes)
        instances = get_instances(request)
        if instances:
            for instance in instances:
                host_name = getattr(instance, 'OS-EXT-SRV-ATTR:host', None)
                if host_name and available_nodes.has_key(host_name):
                    tree_data = get_instance_simple_express(instance,
                                                            available_nodes[
                                                            host_name])
                    host_tree.append(tree_data)

        json_object['host_tree'] = host_tree
        client = VoyageMonitor()
        host_cache = client.get_host_list(request.user.tenant_id,
                                          request.user.token.id)
        json_object['host_cache'] = host_cache
        return HttpResponse(jsonutils.dumps(json_object))
    else:
        return HttpResponse('Not Found')


@require_GET
@check_permission('View Global Monitor')
def index(request):
    """

    :param request:
    :return:
    """
    client = VoyageClient()
    try:
        strategies = client.get_all_os_strategy(request.user.tenant_id,
                                                request.user.token.id)
    except Exception, e:
        LOG.error('Failed to get os-strategy, reason: %s' % (e))
        raise Exception(_('Failed to get strategy, '
                          'please make sure the voyage server is running.'))
    else:
        data = {}
        for strategy in strategies['strategies']:
            if strategy['strategy_name'] in data:
                data[strategy['strategy_name']]['title'] += \
                        get_text(strategy['type_name']) + ": " + \
                        get_text('Warning Value') + " " + \
                        strategy['warning'] + " " + \
                        get_text('Critical Value') + " " + \
                        strategy['critical'] + " | "
            else:
                title = get_text(strategy['type_name']) + ": " +\
                        get_text('Warning Value') + " " +\
                        strategy['warning'] + " " +\
                        get_text('Critical Value') + " " +\
                        strategy['critical'] + " | "
                data[strategy['strategy_name']] = {"id": strategy['strategy_id'],
                                                   "enable": bool(
                                                       strategy['enable']),
                                                   "title": title}

        return shortcuts.render(request, 'monitor_manage/index.html',
                                {"threshold_data": data})


@require_GET
@check_permission('View Global Monitor')
def get_host_monitor_page(request, node_uuid, host_id):
    """

    :param request:
    :param node_uuid:
    :param host_id:
    :return:
    """
    node_name = "Unknown"
    try:
        node = Node.objects.get(uuid=node_uuid)
        node_name = node.name
    except Node.DoesNotExist:
        pass

    return shortcuts.render(request, 'monitor_manage/detail/host.html',
                            {"node_uuid": node_uuid,
                             "host_id": host_id,
                             "websock_uri": settings
                             .VOYAGE_WEBSOCKET_ADDRESS,
                             "host_name": node_name})


@require_GET
@check_permission('View Global Monitor')
def get_instance_monitor_page(request, instance_id):
    """

    :param request:
    :param instance_id:
    :return:
    """
    return shortcuts.render(request, 'monitor_manage/detail/instance.html',
                            {"instance_id": instance_id})


@require_GET
def monitor_manage_top(request):
    """

    :param request:
    :return:
    """
    return shortcuts.render(request, 'monitor_manage/detail/top.html')


@require_GET
@check_permission('View Node')
def get_hardware_info(request):
    try:
        hardware = api.nova.get_hypervisors_statistics(request)
        vcpus = hardware.vcpus
        vcpus_used = hardware.vcpus_used
        memory_mb = hardware.memory_mb
        memory_mb_used = hardware.memory_mb_used
        local_gb = hardware.local_gb
        local_gb_used = hardware.local_gb_used
        vcpus_per = (vcpus_used * 100) / vcpus
        memory_mb_per = (memory_mb_used * 100) / memory_mb
        local_gb_per = (local_gb_used * 100) / local_gb
        json_obj = {"vcpus_per": vcpus_per, "memory_mb_per": memory_mb_per,
                    "local_gb_per": local_gb_per}
        return HttpResponse(jsonutils.dumps(json_obj))
    except Unauthorized:
        raise
    except Exception, e:
        LOG.error('Can not get hypervisors statistics , error is %s' % e)
        return HttpResponse('Not Found')


@require_GET
@check_permission('View Global Monitor')
def get_facility_info(request):
    json_obj = []
    try:
        client = VoyageMonitor()
        facilitys = api.nova.get_hypervisors_list(request)
        facilitys.extend(api.cinder.get_all_hosts_resources(request))
        node_type_dict = {node.name: node.type for node in get_nodes(request)}
        nagios_host_dict = client.get_host_dict(
            tenant_id=request.user.tenant_id, token=request.user.token.id)
        nagios_host_state = client.get_host_status(
            tenant_id=request.user.tenant_id, token=request.user.token.id)
        show_set = set()
        i = 0
        for facility in facilitys:
            if i < 5:
                instance_name = facility.hypervisor_hostname
                if instance_name not in show_set:
                    show_set.add(instance_name)
                else:
                    continue

                if instance_name not in nagios_host_dict \
                    or instance_name not in node_type_dict:
                    continue

                memory_mb = facility.memory_mb * 1.5
                memory_mb_used = facility.memory_mb_used
                memory_mb_per = int((memory_mb_used * 100) / memory_mb)
                instance_online = getattr(facility, 'num_vm_active', 0)
                num_instances = getattr(facility, 'num_instances', 0)
                cpu_use = facility.cpu_usage
                if nagios_host_dict and nagios_host_state:
                    host_state = nagios_host_state[
                                 nagios_host_dict[instance_name]]
                else:
                    host_state = "offline"

                facility_obj = {"instance_name": instance_name,
                                "memory_mb_per": memory_mb_per,
                                "instance_online": instance_online,
                                "instance_offline": num_instances -
                                                    instance_online,
                                "host_type": get_text(
                                    node_type_dict[instance_name]),
                                "host_state": get_text(host_state),
                                "cpu_use": cpu_use}
                json_obj.append(facility_obj)
                i += 1

        return HttpResponse(jsonutils.dumps(json_obj))
    except Unauthorized:
        raise
    except Exception, e:
        LOG.error('Can not get hypervisors list , error is %s' % e)
        return HttpResponse('Not Found')


@require_POST
@check_permission('Update Threshold Strategy')
def update_threshold_strategy(request):
    """
    Modify an existing threshold.
    :param request:
    :param thresholds_id:
    :return:
    """
    if request.is_ajax():
        post = request.POST.copy()
        new_strategy = post.get('new_strategy', None)
        if not new_strategy:
            LOG.error('Invalid request data.')
            return HttpResponse(content=get_text('Invalid request data.'),
                                status=UI_RESPONSE_BADREQUEST)
        else:
            client = VoyageClient()
            try:
                strategies = client.get_all_os_strategy(request.user.tenant_id,
                                                        request.user.token.id)[
                             'strategies']
            except Exception, e:
                LOG.error('Failed to get os-strategy, reason: %s' % (e))
                msg = get_text('Failed to get strategy, '
                        'please make sure the voyage server is running.')
                return HttpResponse(content=msg,
                                    status=UI_RESPONSE_ERROR)
            else:
                old_id = None
                available_ids = []
                for data in strategies:
                    if not old_id and data['enable'] == 1:
                        old_id = data['strategy_id']
                    if str(data['strategy_id']) not in available_ids:
                        available_ids.append(str(data['strategy_id']))

                if new_strategy not in available_ids:
                    LOG.error('Invalid request data.')
                    return HttpResponse(content=get_text('Invalid request data.'),
                                        status=UI_RESPONSE_BADREQUEST)
            data = {
                "old_id": old_id,
                "set_strategy": {
                    "newid": int(new_strategy)
                }
            }
            try:
                client.update_os_strategy(request.user.tenant_id,
                                          request.user.token.id,
                                          data)
            except Exception, e:
                LOG.error("Fail to update stragety, reason: %s" % (e))
                return HttpResponse(content=get_text("Fail to update stragety."),
                                    status=UI_RESPONSE_ERROR)
            else:
                LOG.debug('Update threshold successfully.')
                return HttpResponse(content=get_text("Update threshold successfully."))
    else:
        return HttpResponse(content='Bad Request',
                            status=UI_RESPONSE_BADREQUEST)
