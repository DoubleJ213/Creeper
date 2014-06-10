# coding: utf-8
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



__author__ = 'gmj'
__date__ = '2013-06-21'
__version__ = 'v2.0.9'

import md5
import re
import logging

from django.conf import settings

if settings.DEBUG:
    __log__ = '''v2.0.1 Views for instances list,instance detail and instance
            console;add the function to create image template quickly'''
LOG = logging.getLogger(__name__)
#    code begin
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponse
from django import shortcuts
from django.views.decorators.http import require_GET, require_POST, \
    require_http_methods
from django.utils.text import normalize_newlines
from django.utils import timezone
from django.core.urlresolvers import reverse
from novaclient import exceptions

from dashboard import api
from dashboard.exceptions import NotFound, Unauthorized, LicenseForbidden
from dashboard.utils import jsonutils
from dashboard.utils import UIResponse, ui_response, Pagenation
from dashboard.utils.i18n import get_text
from dashboard.authorize_manage.utils import switch_tenants
from dashboard.utils.ui import UI_RESPONSE_DWZ_ERROR, \
    UI_RESPONSE_DWZ_SUCCESS, UI_RESPONSE_ERROR, UI_RESPONSE_NOTFOUND, \
    UI_RESPONSE_BADREQUEST, UI_RESPONSE_DUPLICATE, check_permission, UI_RESPONSE_OK
from dashboard.authorize_manage import ROLE_ADMIN, ROLE_MEMBER, \
    ROLE_PROJECTADMIN
from dashboard.authorize_manage.utils import get_user_role_name, get_user_role_id
import dashboard.image_template_manage as ImageMang
from dashboard.hard_template_manage.views import search_flavor_status
from dashboard.usage import quotas
from dashboard.role_manage.api import assert_role_right

from dashboard.instance_manage.forms import LaunchForm, UpdateInstanceForm, \
    CreateSnapshot, InstanceClassify, UpdateInstanceClassify, \
    InstanceLiveMigrate
from dashboard.instance_manage.utils import *
from dashboard.instance_manage.models import Distribution, UserClassify, \
    Classify
from dashboard.instance_manage.utils import get_mask


INSTANCE_LIMIT_PER_USER = 6
ACTIVE_STATES = ("ACTIVE",)

POWER_STATE = {1: 'Running',
               3: 'Paused',
               5: 'Suspended'}
STATUS_STATE = {'ACTIVE': 1,
                'PAUSED': 3,
                'SUSPENDED': 5}


def get_instance_network(request, instance_id):
    """
    :param request: request object
    :param instance_id: the instance id
    :return: the instance's network list
    """
    ins_net = ''
    try:
        ins_net = api.nova.get_instance_network(request, instance_id)
    except Unauthorized:
        raise
    except Exception, e:
        LOG.error('Can not get instance network (%s)' % e)
    return ins_net


def get_compute_node(request, instance_id):
    """
    :param request: request object
    :param instance_id: the instance id
    :return: all the hosts name except the instance's
    """
    node = []
    nodes = ''
    instance = ''
    params = {}
    own_host = None
    own_name = None
    try:
        instance = api.server_get(request, instance_id)
        nodes = api.nova.get_all_compute_nodes(request, instance_id)
        setattr(instance, 'host',
                getattr(instance, 'OS-EXT-SRV-ATTR:host', 'None'))
        own_host = instance.host
        own_name = instance.name

    except Unauthorized:
        raise
    except Exception, e:
        LOG.error('Can not get compute nodes (%s)' % e)
    if instance and nodes:
        host = instance.host
        node = nodes['nodes']
        if host in node:
            node.remove(host)
    params = {
        'node': node,
        'host': own_host,
        'name': own_name
    }
    return params


def get_instance_data(request):
    """
    :param request: request object
    :return instances: list, all instances of Cloud
    """
    mem_ins = []
    ins_tenant = None
    role_id = get_user_role_id(request)

    righ_val = assert_role_right(role_id, 'View All Instance')

    try:
        if righ_val:
            ins_tenant = request.user.tenant_id
            project_admin_tenants = api.keystone.tenant_list(request, admin=True)
            tenant_dict = SortedDict([(t.id, t) for t in project_admin_tenants])

        else:
            member_tenants = request.user.authorized_tenants
            for member_tenant in member_tenants:
                mem_tenant_id = getattr(member_tenant, 'id', None)
                mem_ins.append(mem_tenant_id)
            tenant_dict = SortedDict([(t.id, t) for t in member_tenants])
    except Unauthorized:
        raise
    except Exception, e:
        LOG.error('The method get_instance_data raise exception: %s' % e)
        return None

    instances = []
    member_instances = []
    try:
        instances = api.nova.server_list(request, all_tenants=True)

        if len(mem_ins) != 0:
            mem_instances = [inst for inst in instances if inst.tenant_id in mem_ins]

            _relationship = []
            #            filter_instances = []
            u_id = request.user.id
            try:
                _relationship = Distribution.objects.filter(user_id=u_id)
            except Distribution.DoesNotExist, e:
                LOG.error('Distribution does Not Exist. %s' % e)
            except Exception, e:
                _msg = 'Server internal error.'
                LOG.error(_msg)
                LOG.error('error is %s' % e.message)
            for relationship in _relationship:
                for i in range(len(mem_instances)):
                    instance_id = getattr(mem_instances[i], 'id', None)
                    if _relationship and instance_id == relationship.instance_id:
                        member_instances.append(mem_instances[i])

            instances = member_instances

        if ins_tenant:
            instances = [inst for inst in instances if inst.tenant_id == ins_tenant]

    except Unauthorized:
        raise
    except Exception, e:
        LOG.error('Unable to retrieve instance list. %s' % e)
    if instances:
        for inst in instances:
            tenant = tenant_dict.get(inst.tenant_id, None)
            console = getattr(inst, 'console')
            inst.tenant_name = getattr(tenant, "name", None)
            setattr(inst, "user_name",
                    _get_username_in_relationship(request, inst.id))
            setattr(inst, "ip_link", reverse('get_instance_ip', args=[inst.id]))

            if console != '':
                setattr(inst, "console_status", "in-use")
            else:
                setattr(inst, "console_status", "available")
            mask_value = inst.umask
            mask = get_mask(mask_value)
            setattr(inst, 'usbaudo', mask)
    return instances


@check_permission('Remote Desktop')
@require_GET
def get_instance_spice_console(request, instance_id, tenant_id):
    """
    :param request: request object
    :param instance_id: the id of one instance which will be monitoring
    :return: the proxy monitoring url
    """
    role_name = get_user_role_name(request)
    if role_name == ROLE_MEMBER:
        switch_tenants(request, tenant_id)

    try:
        instance = api.server_get(request, instance_id)
    except Unauthorized:
        raise
    instance_id = getattr(instance, 'id', None)
    instance_name = getattr(instance, 'name', None)
    try:
        console = api.nova.server_spice_console(request, instance_id)
    except Unauthorized:
        raise
    except exceptions.NotFound, e:
        msg = 'Can not retrieve spice url! %s' % e
        LOG.error(msg)
        return HttpResponse(jsonutils.dumps(ui_response(message=msg)))
    except Exception, e:
        LOG.error(
            'The method get_instance_spice_console raise exception:%s' % e)
        return HttpResponse(jsonutils.dumps(ui_response(message='error')))
    vnc_url = "%s&title=%s(%s)" % (console.url,
                                   instance_name,
                                   instance_id)
    return shortcuts.render(request, 'instance_manage/vnc.html', {'vnc_url': vnc_url})


def get_instance_show_data(request, instance_id):
    """
    :param request: request object
    :param instance_id: the id of one instance,its information will show
    :return _instance: one instance object
    """
    instance = None
    try:
        instance = api.server_get(request, instance_id)
        instance.volumes = api.nova.instance_volumes_list(request, instance_id)
        # Sort by device name
        instance.volumes.sort(key=lambda vol: vol.device)
        instance.full_flavor = api.flavor_get(request, instance.flavor["id"])
        instance.security_groups = api.server_security_groups(request,
                                                              instance_id)
    except Unauthorized:
        raise
    except Exception, e:
        LOG.error('The method get_instance_show_data raise exception: %s' % e)
    return instance


def flavor_list(request):
    """
    :param request: request object
    :return flavor list: all flavor object
    """
    try:
        flavors = api.flavor_list(request)

        flavor_list = [(flavor.id, flavor.name) for flavor in flavors]
    except Unauthorized:
        raise
    except Exception, e:
        flavor_list = []
        LOG.error('Unable to retrieve instance flavors.%s' % e)
    return sorted(flavor_list)


def keypair_list(request):
    """
    :param request: request object
    :return keypair list: all keypair
    """
    try:
        keypairs = api.nova.keypair_list(request)
        keypair_list = [(kp.name, kp.name) for kp in keypairs]
    except Unauthorized:
        raise
    except Exception, e:
        keypair_list = []
        LOG.error('Unable to retrieve keypairs.%s' % e)
    return keypair_list


def security_group_list(request):
    """
    :param request: request object
    :return security group: all security groups
    """
    try:
        groups = api.nova.security_group_list(request)
        security_group_list = [(sg.name, sg.id) for sg in groups]
    except Unauthorized:
        raise
    except Exception, e:
        LOG.error('Unable to retrieve list of security groups.%s' % e)
        security_group_list = []
    return security_group_list


def volume_list(request):
    """
    :param request: request object
    :return volume: all volumes
    """
    volume_options = [("", _("Select Volume"))]

    def _get_volume_select_item(volume):
        if hasattr(volume, "volume_id"):
            vol_type = "snap"
            visible_label = _("Snapshot")
        else:
            vol_type = "vol"
            visible_label = _("Volume")
        return (("%s:%s" % (volume.id, vol_type)),
                ("%s - %s GB (%s)" % (volume.display_name,
                                      volume.size,
                                      visible_label)))

    def _get_volume_options(objects):
        objects = [obj for obj in objects if
                   obj.status == api.VOLUME_STATE_AVAILABLE]
        return volume_options.extend(
            [_get_volume_select_item(objs) for objs in objects])

    # First add volumes to the list
    try:
        volumes = api.cinder.volume_list(request)
        _get_volume_options(volumes)

    except Unauthorized:
        raise
    except Exception, e:
        LOG.error('Unable to retrieve list of volumes %s' % e)
        # Next add volume snapshots to the list
    try:
        snapshots = api.cinder.volume_snapshot_list(request)
        _get_volume_options(snapshots)

    except Unauthorized:
        raise
    except Exception, e:
        LOG.error('Unable to retrieve list of volumes. %s' % e)

    return volume_options


def get_server_net(request, tenant_id):
    net_list = []
    try:
        networks = api.quantum.network_list_for_tenant(request, tenant_id)
        for n in networks:
            n.set_id_as_name_if_empty()
            if n.subnets:
                net_list.append((n.id, n.name))
    except Unauthorized:
        raise
    except Exception, e:
        LOG.error('Can not get network list %s' % e)
        return HttpResponse('Can not get network list')
    return net_list


def network_list(request):
    """
    :param request: request object
    :return: the network list
    """
    tenant_id = request.user.tenant_id
    network_list = get_server_net(request, tenant_id)
    return network_list


def instance_power_state(instance):
    power_state = getattr(instance, 'OS-EXT-STS:power_state', 'None')
    trans = POWER_STATE.get(power_state, 'No state')
    setattr(instance, 'power_state', trans)


@require_GET
def instance_get_network_list(request):
    """
    :param request: request object
    :return: the tenant's network
    """
    net_list = []
    if 'tenantId' in request.GET:
        tenant_id = request.GET['tenantId']
        if tenant_id:
            try:
                net_list = get_server_net(request, tenant_id)
            except Exception, e:
                LOG.error(
                    'The method instance_get_network_list raise exception: '
                    '%s' % e)
                return HttpResponse({'message': 'Can not get net list'})
        return HttpResponse(jsonutils.dumps(net_list))
    else:
        return HttpResponse({'message': 'No tenant id find'})


@require_GET
def create_instance_select_security(request):
    """
    :param request: request object
    :return dict: the tenant's security group list
    """
    security_group = ''
    if 'tenantId' in request.GET:
        tenant_id = request.GET['tenantId']
        if tenant_id:
            switch_tenants(request, tenant_id)
            security_group = security_group_list(request)
        else:
            return HttpResponse(jsonutils.dumps(security_group))
    return HttpResponse(jsonutils.dumps(security_group))


def get_tenant_security_network(request):
    user_list = []
    user_initial = ("", get_text("Please select an user"))
    user_list.append(user_initial)
    if 'tenantId' in request.GET:
        tenant_id = request.GET['tenantId']
        if tenant_id:
            try:
                security_group = security_group_list(request)
                net_list = get_server_net(request, tenant_id)
                users = api.keystone.user_list(request, tenant_id)
                for user in users:
                    user_list.append((user.id, user.name))
                data = {'groups': security_group, 'nets': net_list, 'users': user_list}
            except Unauthorized:
                raise
            except Exception, e:
                msg = 'Can not get security or network list when change tenant'
                LOG.error(msg + '%s' % e)
                return HttpResponse({'message': msg})
            return HttpResponse(jsonutils.dumps(data))
            #return HttpResponse(data)
    else:
        return HttpResponse({'message': 'Request is wrong!'})


@require_GET
def get_project_usages(request):
    usages = ''
    if 'tenantId' in request.GET:
        tenant_id = request.GET['tenantId']
        if tenant_id:
            switch_tenants(request, tenant_id)
            try:
                usages = quotas.tenant_quota_usages(request)
            except Exception, e:
                LOG.error('Can not get project usages.%s' % e)
    return shortcuts.render(request, "instance_manage/qutoa_pro_bar.html",
                            {'usages': usages})


@check_permission('View Own Instance')
@require_GET
@Pagenation('instance_manage/index.html')
def instance_list(request):
    """
    :param request: request object
    :return: view <'instance_manage/index.html'> of the instances list
    """
    args = {}
    instances = get_instance_data(request) or []
    instance_name = ''
    get_instance_classify = {}
    instance_classify_id = ''
    instance_user = ''
    role = get_user_role_name(request)

    if request.GET.has_key('instance_name'):
        instance_name = request.GET['instance_name']
        if instance_name:
            instances = [ins for ins in instances
                         if getattr(ins, 'name', None).find(instance_name) >= 0]

    if request.GET.has_key("instance_classify_id"):
        instance_classify_id = request.GET['instance_classify_id']
        if instance_classify_id != 'default' and instance_classify_id != '':
            datas = Classify.objects.filter(classify_id=instance_classify_id)
            instance_ids = []
            if datas.exists():
                for cy in datas:
                    instance_ids.append(cy.instance_id)

            instances = [ins for ins in instances
                         if getattr(ins, 'id', None) in instance_ids]

    if request.GET.has_key('instance_user'):
        instance_user = request.GET['instance_user']
        if instance_user != '':
            users = []
            try:
                users = api.keystone.user_list(request)
            except Exception, e:
                LOG.error('Can not get user list in instance_list.%s' % e)
            query_user_ids = [us.id for us in users if
                              getattr(us, 'name', 'unknown').find(
                                  instance_user) >= 0]
            ins_ids = []
            if query_user_ids != '':
                for query_user_id in query_user_ids:
                    distribution_user_obj = Distribution.objects.filter(
                        user_id=query_user_id)
                    if distribution_user_obj.exists():
                        for ins_user in distribution_user_obj:
                            ins_ids.append(ins_user.instance_id)

                instances = [ins for ins in instances if
                             getattr(ins, 'id', None) in ins_ids]

    user_id = request.user.id

    uc = UserClassify.objects.filter(user_id=user_id)

    all_user_classify = {}

    if uc.exists():
        for u in uc:
            all_user_classify[u.classify_id] = u.classify_name

    for i in range(len(instances)):
        setattr(instances[i], 'task',
                getattr(instances[i], 'OS-EXT-STS:task_state', 'None'))
        setattr(instances[i], 'host',
                getattr(instances[i], 'OS-EXT-SRV-ATTR:host', 'None'))
        setattr(instances[i], 'user_role', role)
        instance_id = instances[i].id
        classify_id = None
        try:
            classify_id = Classify.objects.get(instance_id=instance_id,
                                               user_id=user_id).classify_id
        except Exception, e:
            pass    # do not have classify
        classify_name = None
        if classify_id:
            try:
                classify_name = all_user_classify[classify_id]
            except Exception, e:
                classify_name = 'None'
                LOG.error('Can not get classify name %s' % e)

        get_instance_classify[instance_id] = classify_name
        instance_power_state(instances[i])

    classifys = get_instance_classify_data(user_id)
    args['list'] = instances
    args['instance_name'] = instance_name
    args['instance_user'] = instance_user
    args['ins_user_role'] = role
    args['get_instance_classify'] = get_instance_classify
    args['classifys'] = classifys
    args["instance_classify_id"] = instance_classify_id
    return args


@require_GET
def instance_status(request, instance_id):
    """
    :param request: request object
    :param instance_id: the instance id
    :return: the instance's status
    """
    if request.is_ajax():
        try:
            instance = api.server_get(request, instance_id)
        except Unauthorized:
            raise
        except exceptions.ClientException:
            return HttpResponse(content=instance_id,
                                status=UI_RESPONSE_NOTFOUND)
        return HttpResponse(
            jsonutils.dumps({instance_id: getattr(instance, 'status',
                                                  'None')}))
    raise NotFound


@require_GET
def instance_task(request, instance_id):
    """
    :param request: request object
    :param instance_id: the instance id
    :return: the instance's task
    """
    if request.is_ajax():
        try:
            instance = api.server_get(request, instance_id)
        except Unauthorized:
            raise
        except exceptions.ClientException:
            return HttpResponse(content=instance_id,
                                status=UI_RESPONSE_NOTFOUND)
        return HttpResponse(jsonutils.dumps(
            {instance_id: getattr(instance, 'OS-EXT-STS:task_state', 'None')}))
    raise NotFound


@require_GET
def instance_power(request, instance_id):
    """
    :param request: request object
    :param instance_id: the instance id
    :return: the instance's power
    """
    if request.is_ajax():
        try:
            instance = api.server_get(request, instance_id)
        except Unauthorized:
            raise
        except exceptions.ClientException:
            return HttpResponse(content=instance_id,
                                status=UI_RESPONSE_NOTFOUND)
        instance_power_state(instance)
        return HttpResponse(jsonutils.dumps(
            {instance_id: getattr(instance, 'power_state', 'None')}))
    raise NotFound


@require_GET
def instance_ip(request, instance_id):
    """
    :param request: request object
    :param instance_id: the instance id
    :return: the instance's ip
    """
    if request.is_ajax():
        try:
            instance = api.server_get(request, instance_id)
        except Unauthorized:
            raise
        return HttpResponse(jsonutils.dumps(
            {instance_id: getattr(instance, 'addresses', 'None')}))
    raise NotFound


@require_GET
def instance_detail(request, instance_id, tenant_id):
    """
    :param request: request object
    :param instance_id: id of the instance ,its detail information will show
    :return: view <'instance_manage/detail.html'> of the instance detail
    information and proxy monitoring
    """
    role_name = get_user_role_name(request)
    if role_name == ROLE_MEMBER:
        switch_tenants(request, tenant_id)

    msg = ''
    template_name = 'instance_manage/detail.html'
    instance = get_instance_show_data(request, instance_id)
    if not instance:
        msg = 'Can not find instance!'
    return shortcuts.render(request, template_name,
                            {'instance': instance, 'instance_id': instance_id,
                             'msg': msg})


#@require_GET
#def get_instance_action_form(request, instance_id):
#    """
#    :param request: request object
#    :param instance_id: the instance id
#    :return: the instance's state
#    """
#    instance = None
#    instance_name = None
#    instance_status = None
#    try:
#        instance = api.server_get(request, instance_id)
#    except Unauthorized:
#        raise
#    except exceptions.NotFound:
#        LOG.error('Can not find instance with instance id %s' % instance_id)
#
#    if instance:
#        instance_status = instance.status
#        instance_name = instance.name
#
#    return shortcuts.render(request, 'instance_manage/instance_action.html',
#                            {'instance_id': instance_id,
#                             'instance_status': instance_status,
#                             'instance_name': instance_name})


#add by tom
@require_GET
def instance_detail_with_tenant_switch(request, tenant_id, instance_id):
    """
    :param request: the request object
    :param tenant_id: the tenant id
    :param instance_id: the instance id
    :return: the instance detail info
    """
    if switch_tenants(request, tenant_id):
        return instance_detail(request, instance_id)
    else:
        return HttpResponse("Not Found", status=UI_RESPONSE_ERROR)


@check_permission('Add Instance')
@require_GET
def launch_form_image(request):
    """
    :param request: request object
    :param image_id: the image id from which to launch a instance
    :return view<'instance_manage/create.html'>: the from table to create
    instance
    """
    #    image_id = None
    oldtenantid = request.user.tenant_id
    kwargs = {
        'flavor_input_list': search_flavor_status(request),
        'flavor_list': flavor_list(request),
        'security_group_list': security_group_list(request),
        'networks': network_list(request),
        'volume_list': volume_list(request)}

    form = LaunchForm(request, **kwargs)
    switch_tenants(request, oldtenantid)
    try:
        usages = quotas.tenant_quota_usages(request)
    except Exception, e:
        usages = None
        LOG.error('Can not get tenant usages. %s' % e)

    return shortcuts.render(request, 'instance_manage/create1.html',
                            {'form': form,
                             'oldtenantid': oldtenantid,
                             'usages': usages})


@require_POST
@UIResponse('Instance Manage', 'get_instance_list')
def launch_instance(request):
    """
    :param request: request object
    :return view<'instance_manage/create.html or index.html'>: if form has no
     error then create a new instance;else to the create template.
    """
    _status_code = UI_RESPONSE_DWZ_ERROR
    kwargs = {'flavor_list': flavor_list(request),
              'flavor_input_list': None,
              'security_group_list': security_group_list(request),
              'networks': network_list(request),
              'volume_list': volume_list(request)}

    try:
        instances = api.nova.server_list(request, all_tenants=True)
    except Unauthorized:
        raise
    except Exception, e:
        msg = 'Can not get instance list when create instance.'
        LOG.error('Can not get instance list when create instance. %s' % e)
        return HttpResponse({"message": msg, "statusCode": _status_code}, status=_status_code)


    for index in range(len(instances)):
        if request.POST['name'] == getattr(instances[index],'name', None):
            msg = 'instance name has exist.'
            return HttpResponse({"message": msg, "statusCode": _status_code}, status=_status_code)


    form = LaunchForm(request, request.POST.copy(), **kwargs)
    if 'user' in request.POST:
        user_id = request.POST['user']
    else:
        user_id = None
    if form.is_valid():
        data = form.cleaned_data
        object_name = data['name']
        nam_len = len(object_name)
        ins_num = int(data['count'])
        if ins_num > 1 and nam_len > 13:
            object_name = object_name[0:13]
        try:
            dev_mapping = None
            networks = data['networks']
            if networks:
                nics = [{"net-id": netid, "v4-fixed-ip": ""}
                        for netid in networks]
            else:
                nics = None
            switch_tenants(request, data['ins_tenant_id'])

            #Judge whether there instance distribution to a user
            dis_user_id = None
            _msg = ''
            if user_id:
                if Distribution.objects.filter(
                        user_id=user_id).count() >= INSTANCE_LIMIT_PER_USER:
                    dis_user_id = None
                    _msg = _("Current user's instances reach limit %d.") % (
                        INSTANCE_LIMIT_PER_USER)
                else:
                    dis_user_id = user_id

            new_server = api.server_create(request,
                                           dis_user_id,
                                           object_name,
                                           data['image_id'],
                                           data['flavor'],
                                           None,
                                           normalize_newlines(
                                               data.get('user_data')),
                                           data.get('security_groups'),
                                           dev_mapping,
                                           nics=nics,
                                           instance_count=int(data.get('count'))
            )
            #instance_id = new_server.id
            #_msg = ''
            #if user_id:
            #    if Distribution.objects.filter(
            #            user_id=user_id).count() >= INSTANCE_LIMIT_PER_USER:
            #        _msg = _("Current user's instances reach limit %d.") % (
            #            INSTANCE_LIMIT_PER_USER)
            #    else:
            #        _relationship = Distribution(instance_id=instance_id,
            #                                     user_id=user_id)
            #        try:
            #            _relationship.save()
            #        except Exception, e:
            #            LOG.error('create instance-user relationship failed.%s' % e)
            #            _msg = 'Can not create instance-user relationship.'
            #LOG.info('Instance "%s" launched.' % object_name)
            msg = "The task has submit to check" + _msg
            _status_code = UI_RESPONSE_DWZ_SUCCESS
        except Unauthorized:
            raise
        except exceptions.OverLimit, e:
            msg = "The number of the instances exceed the quotas"
            LOG.error('The number of the instances exceed the quotas. %s' % e)
        except LicenseForbidden:
            raise
        except Exception, e:
            LOG.error('Unable to launch instance.%s' % e)
            msg = 'Unable to launch instance'
            if 'InstanceExists' in e.message:
                msg = get_text('Instance %s is already exists') % object_name

            return HttpResponse({"message": msg, "statusCode": _status_code}, status=_status_code)

        #return HttpResponse({"message": msg, 'object_name': object_name,
        #                     "statusCode": _status_code}, status=_status_code)
        return HttpResponse({"message": msg, "statusCode": _status_code}, status=_status_code)
    else:
        return HttpResponse({"form": form, "message": "", "statusCode": _status_code}, status=_status_code)


@check_permission('Delete Instance')
@require_GET
def instance_delete_form(request, instance_id):
    """
    :param request: request object
    :param instance_id: the instance id
    :return: Confirm whether to delete instance
    """
    return shortcuts.render(request, 'instance_manage/delete.html',
                            {'instance_id': instance_id})


def pub_delete_instance(request, instance_ids):
    _status_code = UI_RESPONSE_ERROR
    msg = 'Delete instance failed'
    object_name = None
    for instance_id in instance_ids:
        object_name = get_instance_name(request, instance_id)
        try:
            api.nova.server_delete(request, instance_id)
            try:
                _relationship = Distribution.objects.get(
                    instance_id=instance_id)
                _relationship.delete()
            except Exception, e:
                LOG.error('Error is %s' % e)
            _status_code = UI_RESPONSE_DWZ_SUCCESS
            msg = "delete instance success"
        except Unauthorized:
            raise
        except exceptions.NotFound:
            msg = 'Instance is deleting'
            continue
        except Exception, e:
            msg = 'Delete server error! %s' % e
            LOG.error(msg)

    return HttpResponse({"message": msg, 'object_name': object_name,
                         "statusCode": _status_code}, status=_status_code)


@check_permission('Delete Instance')
@require_http_methods(['DELETE'])
@UIResponse('Instance Manage', 'get_instance_list')
def instance_delete(request, instance_id):
    """
    :param request: request object
    :param instance_id: the delete instance's id
    :return view<'get_instance_list'>: to the get_instance_list page
    """
    instance_ids = []
    instance_ids.append(instance_id)
    return pub_delete_instance(request, instance_ids)


@require_http_methods(['DELETE'])
@UIResponse('Instance Manage', 'get_instance_list')
def delete_instances(request):
    """
    :param request: request object
    :param instance_id: the instance id
    :return: Confirm whether to delete instance
    """
    if 'delete_instance' in request.POST:
        ins_ids = request.POST.getlist('delete_instance')
        if ins_ids:
            return pub_delete_instance(request, ins_ids)
        else:
            return HttpResponse('No instance selected')
    else:
        return HttpResponse('Request is wrong!')


def instance_action(request, instance_id, action):
    """
    :param request: request object
    :param instance_id: the instance id
    :param action: instance actions
    :return: depending the action name return to the coressponding function
    """
    if "reboot" == action:
        return instance_reboot(request, instance_id)
    elif "pause" == action:
        return instance_pause(request, instance_id)
    elif "unpause" == action:
        return instance_unpause(request, instance_id)
    elif "stop" == action:
        return instance_stop(request, instance_id)
    elif "resume" == action:
        return instance_unstop(request, instance_id)
    elif "soft_reboot" == action:
        return instance_soft_reboot(request, instance_id)
    else:
        LOG.error('Can not recognize the action "%s" !' % action)


@check_permission('Reboot Instance')
@require_GET
def instance_reboot_form(request, instance_id):
    """
    :param request: request object
    :param instance_id: the instance id
    :return: the confirm reboot instance template
    """
    return shortcuts.render(request, 'instance_manage/reboot_form.html',
                            {'instance_id': instance_id})


def get_response_url(request):
    try:
        role = get_user_role_name(request)
    except Exception, e:
        msg = 'Can not get the user role! %s' % e
        LOG.error(msg)
        return 'role_none'

    if role == ROLE_MEMBER:
        res_url = 'get_authorized_tenants_index'
    elif role in (ROLE_ADMIN, ROLE_PROJECTADMIN,):
        res_url = 'get_instance_list'
    else:
        res_url = None
        role = None
    return {'res_url': res_url, 'role': role}


@require_POST
@UIResponse('Instance Manage', 'get_instance_list')
def instance_reboot(request, instance_id):
    """
    :param request: request object
    :param instance_id: the instance id which will be reboot
    :return view<'get_instance_list'>: after rebooting return instance list
    """
    object_name = None
    try:
        instance = api.server_get(request, instance_id)
        instance_status = instance.status
        object_name = getattr(instance, 'name', instance_id)
        if instance_status.lower() in (
            'active', 'shutoff', "paused", "suspended"):
            api.server_reboot(request, instance_id, api.nova.REBOOT_HARD)
            msg = "Reboot success!"
            return HttpResponse({"message": msg, 'object_name': object_name, "statusCode": UI_RESPONSE_DWZ_SUCCESS},
                                status=UI_RESPONSE_DWZ_SUCCESS)
        else:
            LOG.info('Can not reboot instance,the status is wrong!')
            msg = 'reboot failed:status is wrong'
            return HttpResponse({"message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR, 'object_name': object_name},
                                status=UI_RESPONSE_ERROR)
    # modify by Xu Lei, 2013-03-06
    # BUG ID: openstack0000167
    # BEGIN #
    except Unauthorized:
        raise
    except exceptions.NotFound, e:
        msg = 'Can not found instance (%s)' % instance_id
        LOG.error('Can not reboot instance. %s' % e)
        return HttpResponse({"message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR, 'object_name': object_name},
                            status=UI_RESPONSE_ERROR)
    except Exception, e:
        LOG.error('Can not reboot instance! %s' % e)
        msg = 'Reboot failed !'
        return HttpResponse({"message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR, 'object_name': object_name},
                            status=UI_RESPONSE_ERROR)


@check_permission('Soft Reboot Instance')
@require_GET
def instance_soft_reboot_form(request, instance_id):
    """
    :param request: request object
    :param instance_id: the instance id
    :return template: the soft reboot template
    """
    return shortcuts.render(request, 'instance_manage/soft_reboot_form.html',
                            {'instance_id': instance_id})


@require_POST
@UIResponse('Instance Manage', 'get_instance_list')
def instance_soft_reboot(request, instance_id):
    """
    :param request: request object
    :param instance_id: the instance id
    :return view<get_instance_list>: After soft rebooting the instance return
     instance list
    """
    try:
        instance = api.server_get(request, instance_id)
        instance_status = instance.status
        if instance_status.lower() in ('active',):
            api.nova.server_reboot(request, instance_id,
                                   api.nova.REBOOT_SOFT)
            msg = 'Soft reboot successfully!'
            return HttpResponse({"message": msg, "statusCode": UI_RESPONSE_DWZ_SUCCESS},
                                status=UI_RESPONSE_DWZ_SUCCESS)
        else:
            msg = 'Just the active status can be soft reboot!'
            return HttpResponse({"message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR}, status=UI_RESPONSE_ERROR)
    except Unauthorized:
        raise
    except exceptions.NotFound:
        msg = 'Can not find instance'
        return HttpResponse({"message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR},
                            status=UI_RESPONSE_ERROR)
    except Exception, e:
        msg = 'Can not soft reboot instance'
        LOG.error('Can not soft reboot instance. %s' % e)
        return HttpResponse({"message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR},
                            status=UI_RESPONSE_ERROR)


@check_permission('Pause Instance')
@require_GET
def instance_pause_form(request, instance_id):
    """
    :param request: request object
    :param instance_id: the instance's id which will be paused
    :return template: the instance pause template
    """
    return shortcuts.render(request, 'instance_manage/pause_form.html',
                            {'instance_id': instance_id})


@require_POST
@UIResponse('Instance Manage', 'get_instance_list')
def instance_pause(request, instance_id):
    """
    :param request: request object
    :param instance_id: the instance's id which will be paused
    :return view<get_instance_list>: after pause return instance list
    """
    object_name = instance_id
    try:
        instance = api.server_get(request, instance_id)
        object_name = getattr(instance, 'name', instance_id)
        instance_status = instance.status

        if instance_status.lower() in ('active',):
            api.nova.server_pause(request, instance_id)
            msg = "Pause instances Success"
            return HttpResponse({"message": msg, 'object_name': object_name, "statusCode": UI_RESPONSE_DWZ_SUCCESS},
                                status=UI_RESPONSE_DWZ_SUCCESS)
        else:
            return HttpResponse({"message": "Can not pause instances:status is not active !",
                                 "statusCode": UI_RESPONSE_DWZ_ERROR}, status=UI_RESPONSE_ERROR)
    # modify by Xu Lei, 2013-03-06
    # BUG ID: openstack0000167
    # BEGIN #
    except Unauthorized:
        raise
    except exceptions.NotFound, e:
        LOG.error('Can not find instance when pause it. %s' % e)
        return HttpResponse({"message": 'Instance not found!', "statusCode": UI_RESPONSE_DWZ_ERROR,
                             'object_name': object_name}, status=UI_RESPONSE_ERROR)
    # END #
    except Exception, e:
        LOG.error('Can not pause instance! %s' % e)
        return HttpResponse({"message": 'Can not pause instance!', "statusCode": UI_RESPONSE_DWZ_ERROR,
                             'object_name': object_name}, status=UI_RESPONSE_ERROR)
        #raise e


@check_permission('Unpause Instance')
@require_GET
def instance_unpause_form(request, instance_id):
    """
    :param request: request object
    :param instance_id: the instance id
    :return template: the unpause instance template
    """
    return shortcuts.render(request, 'instance_manage/unpause_form.html',
                            {'instance_id': instance_id})


@require_POST
@UIResponse('Instance Manage', 'get_instance_list')
def instance_unpause(request, instance_id):
    """
    :param request: request object
    :param instance_id: the instance's id which will be unpaused
    :return view<get_instance_list>: after unpause return instance list
    """

    object_name = instance_id
    try:
        instance = api.server_get(request, instance_id)
        object_name = getattr(instance, 'name', instance_id)
        instance_status = instance.status
        if instance_status.lower() in ('paused', 'active', 'shutoff'):
            api.server_unpause(request, instance_id)
            msg = "Unpause instances Success"
            return HttpResponse({"message": msg, 'object_name': object_name, "statusCode": UI_RESPONSE_DWZ_SUCCESS},
                                status=UI_RESPONSE_DWZ_SUCCESS)
        else:
            return HttpResponse({"message": 'Can not unpause instance:status is not paused !',
                                 "statusCode": UI_RESPONSE_DWZ_ERROR, 'object_name': object_name},
                                status=UI_RESPONSE_ERROR)
    # modify by Xu Lei, 2013-03-06
    # BUG ID: openstack0000167
    # BEGIN #
    except Unauthorized:
        raise
    except exceptions.NotFound, e:
        LOG.error('Can not unpause instance when unpause. %s' % e)
        return HttpResponse({"message": 'Instance not found!', "statusCode": UI_RESPONSE_DWZ_ERROR,
                             'object_name': object_name}, status=UI_RESPONSE_ERROR)
    # END #
    except Exception, e:
        LOG.error('Can not unpause instance! %s' % e)
        return HttpResponse({"message": 'Can not unpause instance!', "statusCode": UI_RESPONSE_DWZ_ERROR,
                             'object_name': object_name}, status=UI_RESPONSE_ERROR)


@check_permission('Suspend Instance')
@require_GET
def instance_stop_form(request, instance_id):
    """
    :param request: request object
    :param instance_id: the instance id
    :return template: the instance stop template
    """
    return shortcuts.render(request, 'instance_manage/stop_form.html',
                            {'instance_id': instance_id})


@require_POST
@UIResponse('Instance Manage', 'get_instance_list')
def instance_stop(request, instance_id):
    """
    :param request: request object
    :param instance_id: the instance's id which will be stoped
    :return view<get_instance_list>: after stop return instance list
    """
    object_name = instance_id
    try:
        instance = api.server_get(request, instance_id)
        object_name = getattr(instance, 'name', instance_id)
        instance_status = instance.status
        if instance_status.lower() in ('active', 'error'):
            api.nova.server_suspend(request, instance_id)
            msg = "Stop instance Success"
            return HttpResponse({"message": msg, 'object_name': object_name, "statusCode": UI_RESPONSE_DWZ_SUCCESS},
                                status=UI_RESPONSE_DWZ_SUCCESS)

        else:
            msg = 'Can not suspend instance whose status is not active'
            LOG.error(msg)
            return HttpResponse({"message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR, 'object_name': object_name},
                                status=UI_RESPONSE_ERROR)

    # modify by Xu Lei, 2013-03-06
    # BUG ID: openstack0000167
    # BEGIN #
    except Unauthorized:
        raise
    except exceptions.NotFound, e:
        msg = 'Can not found instance (%s) ' % instance_id
        LOG.error('Can not find instance when stop. %s' % e)
        return HttpResponse({"message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR, 'object_name': object_name},
                            status=UI_RESPONSE_ERROR)
    # END #
    except Exception, e:
        LOG.error('Can not suspend instance! %s' % e)
        return HttpResponse({"message": 'Can not stop instance!', "statusCode": UI_RESPONSE_DWZ_ERROR,
                             'object_name': object_name}, status=UI_RESPONSE_ERROR)


@check_permission('Resume Instance')
@require_GET
def instance_unstop_form(request, instance_id):
    """
    :param request: request object
    :param instance_id: the instance id
    :return template: the unstop template
    """
    return shortcuts.render(request, 'instance_manage/unstop_form.html',
                            {'instance_id': instance_id})


@require_POST
@UIResponse('Instance Manage', 'get_instance_list')
def instance_unstop(request, instance_id):
    """
    :param request: request object
    :param instance_id: the instance's id which will be resumed
    :return view<get_instance_list>: after resuming instance return the
    instance list
    """

    object_name = instance_id
    try:
        instance = api.server_get(request, instance_id)
        object_name = getattr(instance, 'name', instance_id)
        instance_status = instance.status
        if instance_status.lower() in ('suspended', 'shutoff', 'active'):
            api.nova.server_resume(request, instance_id)
            return HttpResponse({"message": "unstop instance success",
                                 'object_name': object_name, "statusCode": UI_RESPONSE_DWZ_SUCCESS},
                                status=UI_RESPONSE_DWZ_SUCCESS)
        else:
            msg = 'Can not resume instance whose status is not suspended'
            LOG.error(msg)
            return HttpResponse({"message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR,
                                 'object_name': object_name}, status=UI_RESPONSE_ERROR)

    # modify by Xu Lei, 2013-03-06
    # BUG ID: openstack0000167
    # BEGIN #
    except Unauthorized:
        raise
    except exceptions.NotFound, e:
        msg = ('Can not found instance (%s)') % instance_id
        LOG.error('Can not find instance when unstop. %s' % e)
        return HttpResponse({"message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR, 'object_name': object_name},
                            status=UI_RESPONSE_ERROR)
    # END #
    except Exception, e:
        msg = 'Can not resume instance!'
        LOG.error('Something is wrong when resume instance. %s' % e)
        return HttpResponse({"message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR,
                             'object_name': object_name}, status=UI_RESPONSE_ERROR)


@check_permission('Update Instance Info')
@require_GET
def update_instance_form(request, instance_id):
    """
    :param request: request object
    :param instance_id: the instance id which will be updated
    :return view<'instance_manage/update.html'>: return theswitch_tenant form
     table
    """
    #instance = _is_instance_exist(request, instance_id)
    template_name = 'instance_manage/update.html'

    #if not instance:
    #    return shortcuts.redirect('get_instance_list')
    #else:
    #    status = instance.status
    #    if status.lower() in ('active'):
    #        flag = True
    form = UpdateInstanceForm(request, instance_id)
    return shortcuts.render(request, template_name,
                            {'form': form, 'instance_id': instance_id})


@require_POST
@UIResponse('Instance Manage', 'get_instance_list')
def update_instance(request, instance_id):
    """
    :param request: request object
    :param instance_id: the instance id
    :return view<'instance_manage/<index.html><update.html>'>: return
    corresponding view
    """
    name = request.POST['name']
    try:
        instances = api.server_list(request, all_tenants=True)
    except Unauthorized:
        raise
    except Exception, e:
        LOG.error('Can not get instance list when update instance. %s' % e)
        return HttpResponse(
            {"message": 'Can not get instance list', "statusCode": UI_RESPONSE_DWZ_ERROR, 'object_name': name},
            status=UI_RESPONSE_ERROR)

    if re.search(r'\s', name):
        msg = 'no blank space allowed during instance name'
        return HttpResponse({"message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR, 'object_name': name},
                            status=UI_RESPONSE_ERROR)
    for index in range(len(instances)):
        if name == getattr(instances[index], 'name', None):
            msg = 'instance name has exist.'
            return HttpResponse({"message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR, 'object_name': name},
                                status=UI_RESPONSE_ERROR)

    try:
        api.server_update(request, instance_id, name)

        msg = "Update instance name successfully!"
        LOG.info(msg)
    except Unauthorized:
        raise
    except Exception, e:
        msg = "Can not update instance name %s" % e
        LOG.error(msg)
        return HttpResponse({"message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR, 'object_name': name},
                            status=UI_RESPONSE_ERROR)
    return HttpResponse({"message": msg, 'object_name': name, "statusCode": UI_RESPONSE_DWZ_SUCCESS},
                            status=UI_RESPONSE_DWZ_SUCCESS)


def is_deleting(request, instance_id):
    task_state = None
    instance_status = None
    try:
        instance = api.server_get(request, instance_id)
        instance_status = instance.status
        task_state = getattr(instance, "OS-EXT-STS:task_state", None)
    except Unauthorized:
        raise
    except Exception, e:
        LOG.error('Can not instance in function is_deleting. (%s)' % e)
    if task_state != 'is_deleting' and instance_status in ACTIVE_STATES:
        return False
    return True


@check_permission('Backup Instance')
@require_GET
def create_snapshot_form(request, instance_id):
    """
    :param request: request object
    :param instance_id: the instance which will be created snapshot
    :return view<'instance_manage/create_snapshot.html'>: return the form table
    """
    kwargs = {
        'tenant_id': request.user.tenant_id
    }
    try:
        instance = api.server_get(request, instance_id)
    except Unauthorized:
        raise
    except exceptions.NotFound:
        return HttpResponse('NotFound')
    except Exception, e:
        msg = 'Can not create snapshot! %s' % e
        LOG.error(msg)
        return HttpResponse('Error')
    if instance.status != api.nova.INSTANCE_ACTIVE_STATE:
        msg = 'To create a snapshot, the instance status must be in ACTIVE'
        LOG.error(msg)
        return HttpResponse(get_text(msg))
    else:
        form = CreateSnapshot(**kwargs)
    return shortcuts.render(request, 'instance_manage/create_snapshot.html',
                            {'form': form, 'instance_id': instance_id,
                             'tenant_id': request.user.tenant_id})


@require_POST
@UIResponse('Instance Manage', 'get_instance_list')
def create_snapshot(request, instance_id):
    """
    :param request: request object
    :param instance_id: the instance id
    :return view<'instance_manage/<index.html><create_snapshot.html>'>:
    return the corresponding view
    """
    kwargs = {
        'tenant_id': getattr(request.POST, 'tenant_id', None)
    }
    _status_code = UI_RESPONSE_DWZ_ERROR
    form = CreateSnapshot(request.POST.copy(), **kwargs)

    if form.is_valid():
        data = form.cleaned_data
        object_name = data['snapshot_name']
        is_deleted = is_deleting(request, instance_id)
        if not is_deleted:
            try:
                api.snapshot_create(request, instance_id,
                                    data['snapshot_name'])
                msg = 'Create snapshots successfully!'
                LOG.info(msg)
                return HttpResponse({"message": msg, 'object_name': object_name, "statusCode": UI_RESPONSE_DWZ_SUCCESS},
                                    status=UI_RESPONSE_DWZ_SUCCESS)
            except Unauthorized:
                raise
            except LicenseForbidden:
                raise
            except Exception, e:
                # Add by Xu Lei 2013-03-06
                # BUG ID: openstack0000167
                # BEGIN #
                msg = 'Can not create snapshot!'
                LOG.error('Can not create snapshot! %s' % e)
                # END #
            return HttpResponse({"message": msg, "statusCode": _status_code, 'object_name': _status_code},
                                status=_status_code)
        msg = 'The instance task is deleting can not create snapshot'
        return HttpResponse({"message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR},
                            status=UI_RESPONSE_ERROR)

    else:
        return HttpResponse({"form": form, "message": "Form has error!", "statusCode": UI_RESPONSE_DWZ_ERROR},
                            status=UI_RESPONSE_ERROR)


def snapshots_list(request, instance_id):
    """
    :param request:
    :param instance_id:
    :return:
    """
    args = {}
    try:
        snaps, _more_snapshots = api.glance.snapshot_list_detailed(request,
                                                                   marker=None)
    except Unauthorized:
        raise
    except Exception, e:
        LOG.error('Can not get instance snapshots list. (%s)' % e)
    snaps_filter = []
    for i in range(len(snaps)):
        dict_snapshot = snaps[i].properties
        uuid = dict_snapshot.get('instance_uuid', None)
        sta = getattr(snaps[i], 'status', None)
        if uuid:
            if dict_snapshot[
                'instance_uuid'] == instance_id and sta == 'active':
                snaps_filter.append(snaps[i])
        else:
            continue

    args['list'] = snaps_filter
    args['instance_id'] = instance_id
    return args


@check_permission('Restore Backups')
@require_GET
@Pagenation('instance_manage/restore.html')
def restore_instance_form(request, instance_id):
    """
    :param request:
    :param instance_id:
    :return:
    """
    return snapshots_list(request, instance_id)


@check_permission('Get Backup List')
@require_GET
@Pagenation('instance_manage/snapshots_list.html')
def snap_to_tem_list(request, instance_id):
    """
    :param request:
    :param instance_id:
    :return:
    """
    return snapshots_list(request, instance_id)


#add by zhuweidong
def controller_distribution_instance_to_user(request, instance_id):
    """

    :param request:
    :param instance_id:
    :return:
    """
    _user_id = getattr(request.user, 'id', None)
    if not _user_id:
        _msg = u"Missing parameter user_name"
        LOG.error(_msg)
        return False
    else:
        _relationship = None
        try:
            _relationship = Distribution.objects.get(instance_id=instance_id)
        except Distribution.DoesNotExist:
            pass

        if _relationship:
            return False

        _relationship = Distribution(instance_id=instance_id, user_id=_user_id)
        try:
            _relationship.save()
            _msg = u'Create relationship between instance and user ' \
                   u'successfully.'
            LOG.debug(_msg)
        except Exception, e:
            _msg = u'Fail to create relationship between instance and user ' \
                   u'successfully.'
            LOG.error(_msg)
            LOG.error('error is %s' % e.message)
            return False
        return True


@require_POST
@UIResponse('Instance Manage', 'get_instance_list')
def restore_instance_data(request, instance_id):
    """
    :param request: request object
    :param instance_id: the instance id
    :return view<'get_instance_list'>: return the instance list
    """

    # get all the data to restore instance
    data = request.POST.copy()
    instance = get_instance_show_data(request, instance_id)
    object_name = instance.name
    ins_net = get_instance_network(request, instance_id)
    ins_id = []
    if ins_net:
        for net in ins_net:
            net_id = net['network']['id']
            ins_id.append(net_id)

    if len(ins_id) != 0:
        nics = [{"net-id": netid, "v4-fixed-ip": ""}
                for netid in ins_id]
    else:
        nics = None

    if "restore" in data:
        snapshot_id = data['restore']
        #instance = get_instance_show_data(request, instance_id)
        if instance:
            full_flavor = instance.flavor['id']
            group_list = []
            groups = instance.security_groups
            for grp in groups:
                group_list.append(grp.name)
            name = instance.name
            image_id = snapshot_id
            dev_mapping = None
            keyname = instance.key_name
            data_count = {'count': 1}
            user_data = 'restore instance'
            #Judge whether the instance distribution to a user
            dis_user_id = None
            ins = None
            try:
                ins = Distribution.objects.filter(ins_name=name)
            except:
                pass
            if ins:
                dis_user_id = ins[0].user_id
            # launch instance from snapshot image
            try:
                switch_tenants(request, getattr(instance, 'tenant_id', None))
                api.server_create(request,
                                 dis_user_id,
                                 name,
                                 image_id,
                                 full_flavor,
                                 keyname,
                                 user_data,
                                 group_list,
                                 dev_mapping,
                                 nics=nics,
                                 instance_count=data_count.get('count'))

                msg = "The task has submit to check"
                _status_code = UI_RESPONSE_DWZ_SUCCESS
                #msg = 'Restore instance successfully!'
                LOG.info(msg)
                #ins = None
                #try:
                #    ins = Distribution.objects.filter(ins_name=name)
                #except:
                #    pass
                #
                #if ins:
                #    ins_new_id = getattr(instance_new, 'id', None)
                #    if ins_new_id:
                #        controller_distribution_instance_to_user(request,
                #                                                 ins_new_id)
                #        return HttpResponse(
                #            {"message": msg, 'object_name': object_name,
                #             "statusCode": UI_RESPONSE_DWZ_SUCCESS},
                #            status=UI_RESPONSE_DWZ_SUCCESS)
                return HttpResponse(
                    {"message": msg, 'object_name': object_name,
                     "statusCode": _status_code},
                    status=_status_code)
            except Unauthorized:
                raise
            except LicenseForbidden:
                raise
            except Exception, e:
                LOG.error('Can not restore instance! (%s)' % e)
                return HttpResponse({"message": 'Can not restore instance!',
                                     "statusCode": UI_RESPONSE_DWZ_ERROR,
                                     'object_name': object_name},
                                    status=UI_RESPONSE_ERROR)
        else:
            msg = 'Instance does not exist!'
            LOG.error(msg)
            return HttpResponse({"message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR,
                                 'object_name': object_name},
                                status=UI_RESPONSE_ERROR)
    else:
        msg = "No snapshot exist!"
        LOG.error(msg)
        return HttpResponse({"message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR,
                             'object_name': object_name},
                            status=UI_RESPONSE_ERROR)


@check_permission('Quickly Create Image Templates')
@require_POST
@UIResponse('Instance Manage', 'get_instance_list')
def set_snapshot_public(request, snap_id, instance_id):
    """
    :param request: request object
    :param snap_id: the snap's id which is_public status is False
    :param instance_id: instance id
    :return view<'get_snapshots_list'/'image_list'>: the responding template
    """
    image_id = snap_id
    kwargs = {'is_public': True}
    try:
        data = api.image_get(request, image_id)
    except Unauthorized:
        raise
    except Exception, e:
        LOG.error('Can not get snapshot status. %s' % e)
        msg = 'Can not get snapshot status'
        return HttpResponse({"message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR}, status=UI_RESPONSE_ERROR)

    status = data.status
    object_name = get_instance_name(request, instance_id)
    if status.lower() in ('active',):
        try:
            api.image_update(request, image_id, **kwargs)
        except Unauthorized:
            raise
        except Exception, e:
            msg = 'Can not update image. %s' % e
            LOG.error(msg)
            return HttpResponse({"message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR},
                                status=UI_RESPONSE_ERROR)
    else:
        msg = 'The snapshots status must be active !'
        LOG.error(msg)
        return HttpResponse({"message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR, 'object_name': object_name},
                            status=UI_RESPONSE_ERROR)
    return HttpResponse({"message": "Set snapshot public Success", 'object_name': object_name,
                         "statusCode": UI_RESPONSE_DWZ_SUCCESS}, status=UI_RESPONSE_DWZ_SUCCESS)


@require_GET
def get_instance_monitor_info(request, instance_id):
    try:
        server_diagnostic = api.server_diagnostics(request, instance_id)
        if server_diagnostic:
            return HttpResponse(jsonutils.dumps(server_diagnostic))
        else:
            return HttpResponse(get_text('Can not retrieve instance detail'),
                                status=UI_RESPONSE_ERROR)
    except Unauthorized:
        raise
    except Exception, e:
        LOG.error('Can not get diagnostics of instance(%s),Error is %s' % (
            instance_id, e))
        return HttpResponse(get_text('Can not retrieve instance detail'),
                            status=UI_RESPONSE_ERROR)


# Add by Xu Lei 2013-03-06
# BUG ID: openstack0000168
# BEGIN #
def _is_instance_exist(request, instance_id):
    _instance = None
    try:
        _instance = api.server_get(request, instance_id)
    except Unauthorized:
        raise
    except Exception, e:
        msg = 'Can not found instance (%s), %s' % (instance_id, e)
        LOG.error(msg)
    return _instance

# END #


@check_permission('Distribution Instance')
@require_GET
def distribution_instance_form(request, instance_id):
    return shortcuts.render(request, 'instance_manage/relationship.html', {'instance_id': instance_id})


#: Add by Xu Lei 2013-03-11
#: BEGIN #
@require_POST
@UIResponse('Instance Manage', 'get_instance_list')
def distribution_instance_to_user(request, instance_id):
    """
    :param request: request object
    :param instance_id: the instance id
    :return view: get instance list
    """
    _status_code = UI_RESPONSE_DWZ_SUCCESS
    if request.POST.has_key('user_name'):
        _user_id = request.POST['user_name']
    else:
        return HttpResponse({'message': 'The request is wrong'})
    object_name = get_instance_name(request, instance_id)
    if not _user_id:
        _msg = u"Missing parameter user_name"
        _status_code = UI_RESPONSE_BADREQUEST
        LOG.error(_msg)
        return HttpResponse(
            {"message": get_text(_msg), "statusCode": _status_code,
             'object_name': object_name},
            status=_status_code)
    else:
        _relationship = None
        try:
            _relationship = Distribution.objects.get(instance_id=instance_id)
        except Distribution.DoesNotExist:
            pass

        if _relationship:
            _status_code = UI_RESPONSE_DUPLICATE
            _msg = "Duplicate relationship between instance %s and user %s" % (
                instance_id, _user_id)
            return HttpResponse(
                {"message": _msg, "statusCode": UI_RESPONSE_DWZ_ERROR,
                 'object_name': object_name},
                status=_status_code)

        if Distribution.objects.filter(
                user_id=_user_id).count() >= INSTANCE_LIMIT_PER_USER:
            _msg = _("Current user's instances reach limit %d.") % (
                INSTANCE_LIMIT_PER_USER)
            LOG.debug(_msg)
            return HttpResponse(
                content={"message": get_text(_msg),
                         "statusCode": UI_RESPONSE_DWZ_ERROR,
                         'object_name': object_name})

        _relationship = Distribution(instance_id=instance_id, user_id=_user_id, ins_name=object_name)
        try:
            _relationship.save()
            _msg = u'Create relationship between instance and user ' \
                   u'successfully.'
            LOG.debug(_msg)
        except Exception, e:
            _msg = u'Fail to create relationship between instance and user ' \
                   u'successfully.'
            _status_code = UI_RESPONSE_ERROR
            LOG.error(_msg)
        return HttpResponse(
            content={"message": get_text(_msg), "statusCode": _status_code,
                     'object_name': object_name})


@require_GET
def get_distribution_user_form(request, instance_id):
    """
    :param request: request object
    :param instance_id: the instance id
    :return view: get instance list
    """
    _msg = u'There is no relationship for instance '
    _status_code = UI_RESPONSE_DWZ_SUCCESS
    try:
        _relationship = Distribution.objects.filter(instance_id=instance_id)
        if _relationship:
            _status_code = UI_RESPONSE_DUPLICATE
            _msg = "Duplicate relationship for instance"

    except Exception, e:
        _msg = u'Server internal error'
        _status_code = UI_RESPONSE_ERROR
        LOG.error('Get distribution relationship. %s' % e)

    # query user list for <select>
    users = None
    try:
        _instance = api.server_get(request, instance_id)
        users = api.keystone.user_list(request, tenant_id=_instance.tenant_id)
    except Unauthorized:
        raise
    except Exception, e:
        LOG.error('Can not get user list when distribution instance to user! %s' % e)
        _status_code = UI_RESPONSE_ERROR
        _msg = 'Unable to retrieve user list.'
        LOG.error(_msg)
    if not users:
        users = list()

    # Error
    _response_data = {"message": get_text(_msg), "users": {user.id: user.name for user in users}}
    return HttpResponse(jsonutils.dumps(_response_data))


@check_permission('Undistribution Instance')
@require_GET
def delete_distribution_form(request, instance_id):
    return shortcuts.render(request, 'instance_manage/delete_relationship.html', {'instance_id': instance_id})


@require_http_methods(['DELETE'])
@UIResponse('Instance Manage', 'get_instance_list')
def delete_distribution(request, instance_id):
    """
    :param request: request object
    :param instance_id: the instance id
    :return view: get instance list
    """
    _status_code = UI_RESPONSE_DWZ_SUCCESS
    object_name = get_instance_name(request, instance_id)
    try:
        _relationship = Distribution.objects.get(instance_id=instance_id)
        _relationship.delete()
        _msg = "Delete relationship with instance_id successfully"
        LOG.debug(_msg)
    except Exception, e:
        _status_code = UI_RESPONSE_ERROR
        _msg = "Fail to delete relationship with instance_id ."
        LOG.error("Fail to delete relationship with instance_id . %s" % e)

    return HttpResponse({"message": get_text(_msg), "statusCode": _status_code,
                         'object_name': object_name},
                        status=_status_code)


def _get_username_in_relationship(request, instance_id):
    """
    :param request: request object
    :param instance_id: the instance id
    :return list: the instance's user
    """
    if not instance_id:
        raise Distribution.DoesNotExist

    _relationship = None

    try:
        _relationship = Distribution.objects.get(instance_id=instance_id)
    except:
        pass

    if _relationship:
        try:
            user = api.user_get(request, _relationship.user_id, admin=True)
            return getattr(user, 'name', '')
        except Unauthorized:
            raise
        except Exception, e:
            LOG.error(
                'Can not get user in _get_username_in_relationship %s' % e)
            return ""
    else:
        return ""


@require_GET
def get_instance_classify(request, instance_id):
    """
    :param request: request object
    :param instance_id: the instance id
    :return template: the instance classify template
    """

    template_name = 'instance_manage/instance_classify.html'
    user_id = getattr(request, "user").id
    classifys = get_instance_classify_data(user_id)
    calssify_id = ''
    try:
        calssify_id = Classify.objects.get(instance_id=instance_id,
                                           user_id=user_id).classify_id
    except Exception, e:
        LOG.error('Error in get_instance_classify %s' % e)
    return shortcuts.render(request, template_name,
                            {'classifys': classifys, "instance_id": instance_id,
                             "old_classify_id": calssify_id})


@require_POST
@UIResponse('Instance Manage', 'get_instance_list')
def select_instance_classify(request, instance_id):
    """
    :param request: request object
    :param instance_id: the instance id
    :return view: After classify the instance return to the instance list
    """

    datas = None
    user_id = request.user.id
    object_name = get_instance_name(request, instance_id)
    try:
        datas = Classify.objects.filter(instance_id=instance_id,
                                        user_id=user_id)
    except Exception, e:
        LOG.error('select_instance_classify raise exception. %s' % e)

    _status_code = UI_RESPONSE_DWZ_ERROR
    _msg = 'Can not get classify id'

    if request.POST.has_key('classify_id'):
        classify_id = request.POST['classify_id']
        if len(datas) == 0:
            classify = Classify(instance_id=instance_id,
                                classify_id=classify_id, user_id=user_id)
            try:
                classify.save()
                _msg = 'save classify success with instance_id'
                _status_code = UI_RESPONSE_DWZ_SUCCESS
            except Exception, e:
                _msg = 'save classify failed with instance_id. %s' % e
                _status_code = UI_RESPONSE_DWZ_ERROR
                LOG.error(_msg)
        else:
            try:
                datas.update(classify_id=classify_id)
                _msg = 'update classify success with instance_id'
                _status_code = UI_RESPONSE_DWZ_SUCCESS
            except Exception, e:
                LOG.error('update classify falied. %s' % e)
                _msg = 'update classify falied with instance_id'
                _status_code = UI_RESPONSE_DWZ_ERROR

    return HttpResponse({"message": get_text(_msg), "statusCode": _status_code,
                         'object_name': object_name}, status=_status_code)


def get_instance_classify_data(user_id):
    """
    :param user_id: request object
    :param classifys: the dict
    :return dict: the instance classify data
    """
    data = None
    classifys = {}
    try:
        data = UserClassify.objects.filter(user_id=user_id)
    except Exception, e:
        LOG.error('get_instance_classify_data raise exception.%s' % e)

    for cu in data:
        classifys[cu.classify_id] = cu.classify_name
    return classifys


@check_permission('Instance Classify')
@require_GET
def instance_classify_new(request):
    """
    :param request: request object
    :return template: the template using in creating new classify
    """
    template_name = "instance_manage/instance_classify_new.html"
    return shortcuts.render(request, template_name)


@require_POST
@UIResponse('Instance Manage', 'get_instance_list')
def instance_classify_action(request):
    """
    :param request: request object
    :return view: After creating classify,return to instance list
    """
    object_name = ''
    form = InstanceClassify(request.POST.copy())

    if form.is_valid():
        data = form.cleaned_data
        object_name = data["classify"]
        created_at = timezone.now().utcnow()
        uuid = md5.new(str(created_at)).hexdigest()
        user_id = getattr(request, "user").id

        try:
            UserClassify.objects.get(user_id=user_id,
                                     classify_name=data["classify"])
            _msg = get_text("%s has already exist") % data["classify"]
            _status_code = UI_RESPONSE_DWZ_ERROR
        except Exception, e:
            LOG.error('Get classify raise exception. %s' % e)
            uc = UserClassify(uuid, user_id, data["classify"])
            try:
                uc.save()
                _status_code = UI_RESPONSE_DWZ_SUCCESS
                _msg = 'save instance classify success'
            except Exception, e:
                _msg = 'save instance classify failed %s' % e
                _status_code = UI_RESPONSE_DWZ_ERROR

        return HttpResponse({"message": get_text(_msg), "statusCode": _status_code, 'object_name': object_name},
                            status=_status_code)
    else:
        return HttpResponse({"form": form, "message": "The form is wrong", "statusCode": UI_RESPONSE_DWZ_ERROR,
                             "object_name": object_name}, status=UI_RESPONSE_DWZ_ERROR)


@check_permission('Instance Classify')
@require_GET
def instance_classify_delete(request, classify_id):
    """
    :param request: request object
    :param classify_id: the classify id
    :return template: confirm whether to delete classify
    """

    template_name = "instance_manage/delete_classify.html"
    return shortcuts.render(request, template_name,
                            {"classify_id": classify_id})


@require_http_methods(["DELETE"])
@UIResponse('Instance Manage', 'get_instance_list')
def instance_classify_delete_action(request, classify_id):
    """
    :param request: request object
    :param classify_id: the classify id
    :return view: After deleting the classify return to instance list
    """
    uc = UserClassify.objects.filter(classify_id=classify_id)
    classify = Classify.objects.filter(classify_id=classify_id)
    object_name = classify_id
    _msg = 'delete instance classify failed'
    _status_code = UI_RESPONSE_DWZ_SUCCESS
    if len(uc) == 0:
        _msg = ('instance classify  is not found')
        _status_code = UI_RESPONSE_DWZ_ERROR
    else:
        object_name = uc[0].classify_name
        try:
            uc.delete()
            if len(classify) != 0:
                classify.delete()
            _msg = 'delete instance classify success'
        except Exception, e:
            LOG.error("delete instance classify failed error is %s" % e)
            _status_code = UI_RESPONSE_DWZ_ERROR

    return HttpResponse({"message": get_text(_msg), "statusCode": _status_code,
                         'object_name': object_name}, status=_status_code)


@check_permission('Instance Classify')
@require_GET
def instance_classify_update(request, classify_id):
    """
    :param request: request object
    :param classify_id: the classify id
    :return template: update classify template
    """

    template_name = "instance_manage/update_instance_classify.html"
    user_id = request.user.id
    classify_name = ''
    try:
        uc = UserClassify.objects.get(user_id=user_id, classify_id=classify_id)
        classify_name = uc.classify_name
    except Exception, e:
        LOG.error('instance_classify_update raise exception. %s' % e)

    return shortcuts.render(request, template_name, {"classify_id": classify_id,
                                                     "classify_name": classify_name})


@require_POST
@UIResponse('Instance Manage', 'get_instance_list')
def classify_update_action(request, classify_id):
    """
    :param request: request object
    :param classify_id: the classify id
    :return view: After editing the classify return to instance list
    """
    _status_code = UI_RESPONSE_DWZ_ERROR
    object_name = None

    uic = UpdateInstanceClassify(request.POST.copy())
    _msg = "update instance classify name  failed"
    if uic.is_valid():
        data = uic.cleaned_data
        user_id = getattr(request, "user", None).id
        uc = UserClassify.objects.filter(user_id=user_id,
                                         classify_id=classify_id)
        if len(uc) != 0:
            try:
                object_name = uc[0].classify_name
                try:
                    UserClassify.objects.get(user_id=user_id,
                                             classify_name=data["classify_name"])
                    _msg = get_text("%s has already exist") % data["classify_name"]
                except Exception, e:
                    try:
                        uc.update(classify_name=data["classify_name"])
                        _msg = "update instance classify name  success"
                        _status_code = UI_RESPONSE_DWZ_SUCCESS
                    except Exception, e:
                        LOG.error(
                            "update instance classify name  failed error is "
                            "%s" % e)

            except Exception, e:
                LOG.error(
                    "update instance classify name  failed error is %s" % e)

        return HttpResponse({"message": get_text(_msg), "statusCode": _status_code, 'object_name': object_name},
                            status=_status_code)
    else:
        return HttpResponse({"form": uic, "statusCode": _status_code, 'object_name': object_name}, status=_status_code)


@check_permission('Instance Flavor Resize')
@require_GET
def instance_flavor_list(request, instance_id):
    """
    :param request: request object
    :param instance_id: the instance id
    :return template: flavor list except the instance's
    """
    flavor_data = flavor_list(request)
    instances = []
    instance_flavor = ''

    try:
        instances = api.nova.server_get(request, instance_id)
    except Unauthorized:
        raise
    except Exception, e:
        LOG.error("%s is not found %s" % (instance_id, e))
    if instances:
        # Gather our flavors to correlate against IDs
        try:
            current_flavor = getattr(instances, "flavor", None)

            if current_flavor:
                instance_flavor = current_flavor['id']
        except Exception, e:
            msg = _('flavor id is not found %s' % e)
            LOG.error(msg)

    template_name = "instance_manage/update_instance_flavor.html"

    return shortcuts.render(request, template_name,
                            {"flavor_list": flavor_data,
                             "instance_flavor": instance_flavor,
                             "instance_id": instance_id})


@require_POST
@UIResponse('Instance Manage', 'get_instance_list')
def instance_flavor_update(request, instance_id):
    """
    :param request: request object
    :param instance_id: the instance id
    :return view: After editing instance flavor return instance list
    """
    _msg = ''
    _status_code = UI_RESPONSE_DWZ_ERROR
    object_name = get_instance_name(request, instance_id)

    if request.POST.has_key("flavor_id"):
        flavor_id = request.POST["flavor_id"]
        try:
            api.nova.server_resize(request, instance_id, flavor_id)
            _msg = "Submit the request of flavor resize,wait please!"
            _status_code = UI_RESPONSE_DWZ_SUCCESS

        except Unauthorized:
            raise
        except LicenseForbidden:
            raise
        except exceptions.BadRequest, e:
            _status_code = UI_RESPONSE_DWZ_ERROR
            _message = e.message
            LOG.error('instance_flavor_update bad request. %s' % e)
            return HttpResponse(
                {"message": _message, "statusCode": _status_code,
                 'object_name': object_name},
                status=_status_code)

        except Exception, e:
            LOG.error('update instance flavor failed. %s' % e)
            _msg = "update instance flavor failed"
            _status_code = UI_RESPONSE_DWZ_ERROR
            return HttpResponse({"message": _msg, "statusCode": _status_code},
                                status=_status_code)

    return HttpResponse({"message": _msg, "statusCode": _status_code,
                         'object_name': object_name},
                        status=_status_code)


@require_GET
def instance_flavor_confirm(request, instance_id):
    """
    :param request: request object
    :param instance_id: the instance id
    :return template: confirm whether to resize instance flavor
    """
    template_name = "instance_manage/confirm_flavor.html"
    return shortcuts.render(request, template_name,
                            {"instance_id": instance_id})


@require_GET
@UIResponse('Instance Manage', 'get_instance_list')
def flavor_confirm_action(request, instance_id):
    """
    :param request: request object
    :param instance_id: the instance id
    :return view: after confirming resize instnace return instance list
    """
    _status_code = UI_RESPONSE_DWZ_SUCCESS

    try:
        api.nova.server_confirm_resize(request, instance_id)
        _msg = "confirm flavor resize success"
    except Unauthorized:
        raise
    except Exception, e:
        LOG.error('Error in flavor_confirm_action is %s' % e)
        _msg = "confirm flavor resize failed"
        _status_code = UI_RESPONSE_DWZ_ERROR

    return HttpResponse({"message": get_text(_msg), "statusCode": _status_code},
                        status=_status_code)


def get_instance_name(request, instance_id):
    """
    :param request: request object
    :param instance_id: the instance id
    :return instance_name: the instance name
    """
    try:
        instance = api.server_get(request, instance_id)
        instance_name = getattr(instance, 'name', instance_id)
    except Unauthorized:
        raise
    except Exception, e:
        LOG.error('Can not get_instance_name. %s' % e)
        return instance_id
    return instance_name


@require_GET
def get_instance_gtk_client(request, tenant_id, instance_id):
    """
    :param request: request object
    :param instance_id: the id of one instance which will be monitoring
    :return: the proxy monitoring url
    """

    if request.is_ajax():
        switch_tenants(request, tenant_id)
        try:
            instance = api.server_get(request, instance_id)
            instance_id = getattr(instance, 'id', None)
            console = api.nova.server_gtk_console(request, instance_id)

            # save token
            #            records = ConsoleToken.objects.filter(host=request.META['REMOTE_ADDR']).all()
            #            if records:
            #                records.update(token=console['token'])
            #            else:
            #                c = ConsoleToken(host=request.META['REMOTE_ADDR'],
            #                                 token=console['token'])
            #                c.save()
            return HttpResponse(
                jsonutils.dumps({"ip": getattr(console, 'host', 'None'),
                                 "port": getattr(console, 'port', 'None'),
                                 "umask": instance.umask}))
        except Unauthorized:
            raise
        except Exception, e:
            LOG.error("Get spice gtk console info error.")
            raise e
    raise NotFound


@require_GET
def get_instance_host(request):
    host = ''
    if 'instance_id' in request.GET:
        try:
            instance = api.server_get(request, request.GET['instance_id'])
            host = getattr(instance, 'OS-EXT-SRV-ATTR:host', 'None')
        except Unauthorized:
            raise
        except Exception, e:
            LOG.error('Can not get instance host. %s' % e)
    return HttpResponse(jsonutils.dumps({"host": host}))


@check_permission('Live Migrate')
@require_GET
def instance_live_migrate(request, instance_id):
    """
    :param request: request object
    :param instance_id: the instance id
    :return template: the instance live migration template
    """
    param = get_compute_node(request, instance_id)
    compute_list = param['node']
    ins_name = param['name']
    ins_host = param['host']
    kwargs = {'instance_id': instance_id,
              'compute_list': compute_list
    }
    form = InstanceLiveMigrate(**kwargs)
    return shortcuts.render(request, 'instance_manage/live_migrate.html',
                            {'form': form, 'instance_id': instance_id,
                             'ins_name': ins_name, 'ins_host': ins_host})


@require_POST
@UIResponse('Instance Manage', 'get_instance_list')
def handle_instance_live_migrate(request, instance_id):
    """
    :param request: request object
    :param instance_id: the instance id
    :return view: after live migration return instance list
    """
    nodes = get_compute_node(request, instance_id)
    kwargs = {
        'instance_id': instance_id,
        'compute_list': nodes['node']
    }
    form = InstanceLiveMigrate(request.POST.copy(), **kwargs)
    if form.is_valid():
        data = form.cleaned_data
        host_name = data['host']
        instance = get_instance_show_data(request, instance_id)
        task = getattr(instance, 'OS-EXT-STS:task_state', None)
        if instance and instance.status == 'ACTIVE' and task in (None, 'No Valid Host'):
            try:
                api.nova.server_live_migrate(request, instance_id, host_name,
                                             block_migration=True,
                                             disk_over_commit=False)
                msg = 'Live migrate instance successfully!'
            except Unauthorized:
                raise
            except LicenseForbidden:
                raise
            except Exception, e:
                msg = 'Can not live migrate the instance'
                LOG.error('Can not live migrate the instance. %s' % e)
                return HttpResponse(
                    {"message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR},
                    status=UI_RESPONSE_ERROR)

            return HttpResponse(
                {'message': msg, "statusCode": UI_RESPONSE_DWZ_SUCCESS},
                status=UI_RESPONSE_DWZ_SUCCESS)
        else:
            msg = 'Can not live migrate the instance,its status is not active' \
                  ' or task is not None'
            return HttpResponse(
                {"message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR},
                status=UI_RESPONSE_ERROR)
    else:
    #        form = InstanceLiveMigrate()
        msg = 'The form is wrong when live migration instance,check please!'
        return HttpResponse(
            {"form": form, "message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR},
            status=UI_RESPONSE_ERROR)


@require_GET
def update_instance_view_date(request, instance_id, tenant_id):
    role_name = get_user_role_name(request)
    if role_name == ROLE_MEMBER:
        switch_tenants(request, tenant_id)
    try:
        instance = api.nova.server_get(request, instance_id)
        host = getattr(instance, 'OS-EXT-SRV-ATTR:host', 'None')
        if host == 'None':
            host = get_text(host)
        addresses = getattr(instance, 'addresses', 'None')
        ips = ''
        for i in addresses:
            if len(addresses[i]) != 0:
                for j in range(len(addresses[i])):
                    ips += addresses[i][j]['addr'] + ","
        status = getattr(instance, 'status', 'None')
        status = get_text(status)
        task = getattr(instance, 'OS-EXT-STS:task_state', 'None')
        remote_status = getattr(instance, 'console')
        if remote_status == '':
            setattr(instance, "console_status", "available")
        else:
            setattr(instance, "console_status", "in-use")
        remote_status = get_text(instance.console_status)
        task = get_text(task)
        virt_power_state = getattr(instance, 'OS-EXT-STS:power_state', 'None')
        power = POWER_STATE.get(virt_power_state, 'No state')
        power = get_text(power)

        user_name = ""
        try:
            _relationship = Distribution.objects.get(instance_id=instance_id)
            if _relationship:
                user_id = _relationship.user_id
                user = api.user_get(request, user_id, admin=True)
                user_name = getattr(user, "name", None)
        except Exception, e:
            LOG.info('Can not get user when refresh the instance list.%s' % e)
            pass

        view_data = {"vm_id": instance_id,
                     "ip": ips,
                     "host": host,
                     "vm_state": status,
                     "task_state": task,
                     "power_state": power,
                     "remote_status": remote_status,
                     "console": instance.console,
                     "user_name": user_name}
        return HttpResponse(jsonutils.dumps(view_data))
    except Unauthorized:
        raise
    except exceptions.ClientException, e:
        LOG.error('Unable to request instance %s detail. %s' % (instance_id, e))
        if isinstance(e, (exceptions.NotFound, exceptions.Forbidden)):
            return HttpResponse(content=instance_id,
                                status=UI_RESPONSE_NOTFOUND)
        else:
            return HttpResponse(content=e.message, status=UI_RESPONSE_ERROR)


@require_GET
def get_ins_flavor(request):
    flavor_info = {}
    if 'flavorId' in request.GET:
        flavor_id = request.GET['flavorId']
        try:
            flavor = api.flavor_get(request, flavor_id)
            flavor_info = {
                "name": flavor.name,
                "disk": flavor.disk,
                "ram": flavor.ram,
                "vcpus": flavor.vcpus,
                "ephemeral": flavor.ephemeral
            }
        except Exception, e:
            LOG.error("Can not get flavor detail. %s" % e)
        return HttpResponse(jsonutils.dumps(flavor_info))
    else:
        return HttpResponse('Request is something wrong!')


@require_GET
def get_tenant_user(request):
    user_list = []
    user_initial = ("", get_text("Please select an user"))
    user_list.append(user_initial)
    if 'tenantId' in request.GET:
        tenant_id = request.GET['tenantId']
    else:
        return HttpResponse('Not find tenant id,request is wrong')
    if tenant_id:
        try:
            users = api.keystone.user_list(request, tenant_id)
            for user in users:
                user_list.append((user.id, user.name))
        except Exception, e:
            LOG.error('Can not get tenant user when create instance.%s' % e)
    return HttpResponse(jsonutils.dumps(user_list))


@require_GET
def terminate_instance_console(request):
    if 'instance_id' in request.GET:
        instance_id = request.GET['instance_id']
    else:
        return HttpResponse('Request is wrong,check please!')
    try:
        api.server_terminate_spice_console(request, instance_id)
    except Exception, e:
        LOG.error('Can not terminate instance console. %s' % e)
        return HttpResponse(jsonutils.dumps({"status": "FAIL"}))
    return HttpResponse(jsonutils.dumps({"status": "OK"}))


@require_GET
def update_instance_umask_form(request, instance_id, umask):
    return shortcuts.render(request, "instance_manage/update_umask.html", {'instance_id': instance_id, 'umask': umask})


@UIResponse('Instance Manage', 'get_instance_list')
def update_instance_umask(request, instance_id, umask):
    msg = 'update instance umask successfully!'
    _status_code = UI_RESPONSE_DWZ_SUCCESS
    u_type = None
    us_right = None
    aud_right = None
    role_id = get_user_role_id(request)
    if request.POST.has_key("t"):
        u_type = request.POST["t"]

    if u_type == 'usb':
        us_right_op = assert_role_right(role_id, 'USB Open')
        us_right_st = assert_role_right(role_id, 'USB Stop')
        us_right = us_right_op & us_right_st
    else:
        aud_right_op = assert_role_right(role_id, 'Audio Open')
        aud_right_st = assert_role_right(role_id, 'Audio Stop')
        aud_right = aud_right_op & aud_right_st

    try:
        instance = api.server_get(request, instance_id)
        val = instance.umask - int(umask) if instance.umask & int(umask) else instance.umask + int(umask)
        umask = val & int(umask)
        api.server_update_umask(request, instance_id, val)
    except Exception, e:
        LOG.error('Can not update server umask.%s' % e)
        msg = ('Update instance umask failed!')
        _status_code = UI_RESPONSE_DWZ_ERROR

    return HttpResponse(jsonutils.dumps({"message": get_text(msg), "statusCode": _status_code, "type": u_type,
                        "instance_id": instance_id, "umask": umask, "us_right": us_right, "aud_right": aud_right }))


@check_permission(_or=('USB Stop', 'USB Open', ))
@require_POST
def update_instance_usb_umask(request, instance_id, umask):
    """
    :param request:
    :param instance_id:
    :param umask:
    :return:
    """
    return update_instance_umask(request, instance_id, umask)


@check_permission(_or=('Audio Stop', 'Audio Open', ))
@require_POST
def update_instance_audio_umask(request, instance_id, umask):
    """
    :param request:
    :param instance_id:
    :param umask:
    :return:
    """
    return update_instance_umask(request, instance_id, umask)

