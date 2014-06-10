__author__ = 'zwd'
__date__ = '2013-04-02'
__version__ = 'v2.0.6'


import logging

from django import shortcuts
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.http import require_GET
from django.utils.translation import ugettext as _

from dashboard import api
from dashboard.authorize_manage.utils import switch_tenants
from dashboard.exceptions import Unauthorized
from dashboard.instance_manage.views import get_instance_data
from dashboard.node_manage.views import get_nodes
from dashboard.utils import jsonutils

LOG = logging.getLogger(__name__)

if settings.DEBUG:
    __log__ = """v2.0.6 create [2013-04-02]
     v2.0.6 add check if fold exist or not when create and delete binary package of static_resource
    """

@require_GET
def goto_node_resource(request):
    """
    :param request: request Object
    :return:
    """
    return shortcuts.render(request,
        'static_resource_manage/node_resource.html')


@require_GET
def get_node_resource(request):
    nodes = get_nodes(request) or []
    instances = None
    flavors = None
    try:
        instances = api.nova.server_list(request, all_tenants=True)
        if instances:
            flavors = api.nova.flavor_list(request)
    except Unauthorized:
        raise
    except Exception, e:
        LOG.error('Unable to retrieve instance list, error is %s.' % e.message)

    node_resources = []
    if nodes != None:
        for node in nodes:
            node_uuid = node.uuid
            node_name = node.name
            try:
                host_monitor_infos = api.get_host_monitor(request, node_name)
                host = None
                cpu = None
                vcpu = 0
                memory = None
                disk = None
                cpu_used = None
                vcpu_used = 0
                memory_used = None
                disk_used = None
                for host_monitor_info in host_monitor_infos:
                    project = str(host_monitor_info.resource['project'])
                    if project == '(total)':
                        host = host_monitor_info.resource['host']
                        cpu = host_monitor_info.resource['cpu']
                        memory = host_monitor_info.resource['memory_mb']
                        disk = host_monitor_info.resource['disk_gb']
                    if project == '(used_now)':
                        cpu_used = host_monitor_info.resource['cpu']
                        memory_used = host_monitor_info.resource['memory_mb']
                        disk_used = host_monitor_info.resource['disk_gb']
                if host:
                    if instances and flavors:
                        for instance in instances:
                            if getattr(instance, 'OS-EXT-SRV-ATTR:host',
                                'None') == node_name:
                                if instance.status == "ACTIVE":
                                    flavor_id = instance.flavor['id']
                                    for flavor in flavors:
                                        if flavor.id == flavor_id:
                                            vcpu = vcpu + flavor.vcpus
                                            vcpu_used = vcpu_used + flavor.vcpus
                                else:
                                    flavor_id = instance.flavor['id']
                                    for flavor in flavors:
                                        if flavor.id == flavor_id:
                                            vcpu = vcpu + flavor.vcpus
                    node_resource = {'host': host,
                                     'vcpu': vcpu,
                                     'memory': memory,
                                     'disk': disk,
                                     'vcpu_used': vcpu_used,
                                     'memory_used': memory_used,
                                     'disk_used': disk_used}
                    node_resources.append(node_resource)
            except Unauthorized:
                raise
            except Exception, e:
                LOG.error(
                    'Can not get node (uuid=%s) monitor information , error is %s.' % (
                        node_uuid, e.message))
    try:
        return HttpResponse(jsonutils.dumps(node_resources))
    except:
        return HttpResponse('Not Found')


@require_GET
def goto_project_resource(request):
    """
    :param request: request Object
    :return:
    """
    return shortcuts.render(request,
        'static_resource_manage/project_resource.html')


@require_GET
def get_project_resource(request):
    projects = None
    try:
        projects = api.tenant_list(request, admin=True)
    except Unauthorized:
        raise
    except Exception, e:
        LOG.error('Unable to retrieve project list,%s.' % e.message)

    project_resources = []
    if projects:
        instances_obj = None
        flavors = None
        try:
            instances_obj = api.nova.server_list(request, all_tenants=True)
            if instances_obj:
                flavors = api.nova.flavor_list(request)
        except Unauthorized:
            raise
        except Exception, e:
            LOG.error(
                'Unable to retrieve instance list , error is %s.' % e.message)

        for project in projects:
            tenant_id = project.id
            project_name = project.name
            cores = 0
            ram = 0
            instances = 0
            gigabytes = 0
            volumes = 0
            floating_ips = 0
            instances_used = 0
            cores_used = 0
            ram_used = 0
            gigabytes_used = 0
            volumes_used = 0
            floating_ips_used = 0
            try:
                quota = api.nova.nova_tenant_quota_get(request, tenant_id)
                quota2 = api.cinder.cinder_tenant_quota_get(request, tenant_id)
                quotasItems = {}
                for item in quota:
                    quotasItems[item.name] = item.limit
                for item in quota2:
                    quotasItems[item.name] = item.limit
                if quotasItems != None and quotasItems != {}:
                    cores = quotasItems['cores']
                    ram = quotasItems['ram']
                    instances = quotasItems['instances']
                    gigabytes = quotasItems['gigabytes']
                    volumes = quotasItems['volumes']
                    floating_ips = quotasItems['floating_ips']
            except Unauthorized:
                raise
            except Exception, e:
                msg = 'Unable to get tenant %(tenant)s info , error is %s.' % (
                    {'tenant': tenant_id}, e.message)
                LOG.error(msg)
            if instances_obj and flavors:
                for instance_obj in instances_obj:
                    if instance_obj.tenant_id == tenant_id:
                        instances_used += 1
                        flavor_id = instance_obj.flavor['id']
                        for flavor in flavors:
                            if flavor.id == flavor_id:
                                cores_used = cores_used + flavor.vcpus
                                ram_used = ram_used + flavor.ram
                                gigabytes_used = gigabytes_used + flavor.disk
                        try:
                            intance_volumes = api.nova.instance_volumes_list(
                                request, instance_obj.id)
                            volumes_used += len(intance_volumes)
                        except Exception, e:
                            msg = 'Can not found instance (%s) , error is %s.' % (
                                instance_obj.id, e.message)
                            LOG.error(msg)
            try:
                if project.enabled and None != switch_tenants(request,
                    tenant_id):
                    floating_ipsObj = api.network.tenant_floating_ip_list(
                        request)
                    for floating_ipObj in floating_ipsObj:
                        if floating_ipObj.instance_id != None and floating_ipObj.tenant_id == tenant_id:
                            floating_ips_used += 1
            except Unauthorized:
                raise
            except Exception, e:
                floating_ips_used = 0
                LOG.exception("ClientException in floating ip index")
                LOG.error('error is %s.' % e.message)

            project_resource = {
                'project_name': project_name,
                'cores': cores,
                'ram': ram,
                'instances': instances,
                'gigabytes': gigabytes,
                'volumes': volumes,
                'floating_ips': floating_ips,
                'cores_used': cores_used,
                'ram_used': ram_used,
                'instances_used': instances_used,
                'gigabytes_used': gigabytes_used,
                'volumes_used': volumes_used,
                'floating_ips_used': floating_ips_used
            }
            project_resources.append(project_resource)
    try:
        return HttpResponse(jsonutils.dumps(project_resources))
    except:
        return HttpResponse('Not Found')


@require_GET
def goto_instance_resource(request):
    """
    :param request: request Object
    :return:
    """
    return shortcuts.render(request,
        'static_resource_manage/instance_resource.html')


@require_GET
def get_instance_resource(request):
    instances = []
    try:
        instances = get_instance_data(request)
    except Unauthorized:
        raise
    except Exception, e:
        LOG.error(e)

    active_num = 0
    suspend_num = 0
    pause_num = 0
    shutoff_num = 0
    resource_not_enough_num = 0
    error_num = 0
    for instance in instances:
        status = instance.status
        if status == 'ACTIVE':
            active_num += 1
        elif status == 'SUSPENDED':
            suspend_num += 1
        elif status == 'PAUSED':
            pause_num += 1
        elif status == 'SHUTOFF':
            shutoff_num += 1
        elif status == 'RESOURCE_IS_NOT_ENOUGH':
            resource_not_enough_num += 1
        elif status == 'ERROR':
            error_num += 1

    instance_resources = []
    instance_resources.append({'status': _('Active'),
                               'status_num': active_num})
    instance_resources.append({'status': _('Suspend'),
                               'status_num': suspend_num})
    instance_resources.append({'status': _('Paused'),
                               'status_num': pause_num})
    instance_resources.append({'status': _('Shutoff'),
                               'status_num': shutoff_num})
    instance_resources.append({'status': _('RESOURCE_IS_NOT_ENOUGH'),
                               'status_num': resource_not_enough_num})
    instance_resources.append({'status': _('ERROR'),
                               'status_num': error_num})

    return HttpResponse(jsonutils.dumps(instance_resources))


@require_GET
def goto_static_resource(request, type='node'):
    if type == 'node':
        return goto_node_resource(request)
    elif type == 'project':
        return goto_project_resource(request)
    elif type == 'instance':
        return goto_instance_resource(request)


@require_GET
def get_static_resource(request, type='node'):
    if type == 'node':
        return get_node_resource(request)
    elif type == 'project':
        return get_project_resource(request)
    elif type == 'instance':
        return get_instance_resource(request)
