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
__date__ = '2012-02-18'
__version__ = 'v2.0.1'


#    code begin
import md5
import logging

from django.conf import settings
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _
from django import shortcuts
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.utils import timezone
from cinderclient import exceptions

from dashboard import api
from dashboard.exceptions import NotFound, Unauthorized, LicenseForbidden
from dashboard.utils.i18n import get_text
from dashboard.utils import UIResponse, Pagenation, jsonutils, check_permission
from dashboard.authorize_manage.utils import switch_tenants
from dashboard.usage import quotas
from dashboard.utils import UI_RESPONSE_ERROR, UI_RESPONSE_DWZ_SUCCESS,\
    UI_RESPONSE_DWZ_ERROR, UI_RESPONSE_BADREQUEST, UI_RESPONSE_NOTFOUND
from dashboard.volume_manage.volumeutils import VolumeUtils
from dashboard.instance_manage.utils import get_instances as get_instance_list

from .forms import CreateVolumeForm, CreateVolumeSnapshot


LOG = logging.getLogger(__name__)

if settings.DEBUG:
    __log__ = 'v2.0.1 volume list;volume detail;create volume;once time delete more volumes'

DELETABLE_STATES = ("available", "error")
ACTIVE_STATES = ("ACTIVE",)
VOLUMES_CHOICE = {"small": 10, "medium": 20, "large": 50, "max": 100}
VOLUMES = [u'c', u'd', u'e', u'f', u'g', u'h', u'i', u'j', u'k', u'l', u'm',
           u'n', u'o', u'p', u'q', u'r', u's', u't',
           u'u', u'v', u'w', u'x', u'y', u'z']

vu = VolumeUtils()

#def get_instance_list(request, all_tenants=False):
#    try:
#        instance_list = api.server_list(request, all_tenants=all_tenants)
#    except Unauthorized:
#        raise
#    except Exception, ex:
#        instance_list = []
#        LOG.error("Can not retrieve instance list,%s" % ex)
#    return instance_list

@check_permission('View Volume')
@require_GET
@Pagenation("volume_manage/index.html")
def get_volume_list(request):
    """
    :param request: request object
    :return view<'volume_manage/index.html'>: the view get_volume_list
    """

    volume_name = ''
    args = {}
    if request.GET.has_key("volume_name"):
        volume_name = request.GET['volume_name']

    try:
        volumes = api.volume_list(request)
        instances = get_instance_list(request)
        tenants = api.tenant_list(request,
            getattr(request.user, 'is_superuser', True))

        instances = SortedDict([(inst.id, inst) for inst in instances])
        tenants_dic = SortedDict([(tenant.id, tenant) for tenant in tenants])

        volumes = [volume for volume in volumes if
                   volume.status != 'error_deleting']

        for volume in volumes:
            att = volume.attachments
            server_id = None
            if  len(att) != 0:
                server_id = att[0]['server_id']
                ins = instances[server_id]
                setattr(volume, "instance_name", getattr(ins, "name", None))
            else:
                setattr(volume, "instance_name", None)
            try:
                setattr(volume, "tenant", tenants_dic[getattr(volume,
                    'os-vol-tenant-attr:tenant_id', None)])
            except Exception, ex:
                LOG.error("Can't found tenant %s" % ex)
            setattr(volume, "instance_id", server_id)
            setattr(volume, "status_link",
                reverse('get_volume_status', args=[volume.id]))
    except Unauthorized:
        raise
    except Exception, ex:
        volumes = []
        LOG.error("ClientException in volume index. %s" % ex)

    if volume_name != '':
        volumes = [v for v in volumes
                   if v.display_name.find(volume_name) >= 0]

    created_at = timezone.now().utcnow()
    uuid = md5.new(str(created_at)).hexdigest()
    args['list'] = volumes
    args['volume_name'] = volume_name
    args['uuid'] = uuid
    vu.uuid = uuid
    return args

@check_permission('View Volume')
@require_GET
@Pagenation("volume_manage/volume_index_temp.html")
def get_volume_list_temp(request):
    volume_name = ''
    args = {}
    if request.GET.has_key("volume_name"):
        volume_name = request.GET['volume_name']

    try:
        instances = get_instance_list(request)

        tenants = api.tenant_list(request,
            getattr(request.user, 'is_superuser', True))

        volumes = api.volume_list(request)

        instances = SortedDict([(inst.id, inst) for inst in instances])
        tenants_dic = SortedDict([(tenant.id, tenant) for tenant in tenants])

        volumes = [volume for volume in volumes if
                   volume.status != 'error_deleting']

        for volume in volumes:
            att = volume.attachments
            server_id = None
            if  len(att) != 0:
                server_id = att[0]['server_id']
                #instance_id_dict[volume.id] = server_id
                ins = instances[server_id]
                #attach_instance[volume.id] = getattr(ins, "name", None)
                setattr(volume, "instance_name", getattr(ins, "name", None))
            else:
            #                attach_instance[volume.id] = None
                setattr(volume, "instance_name", None)
                #instance_id_dict[volume] = None
            try:
                setattr(volume, "tenant", tenants_dic[getattr(volume,
                    'os-vol-tenant-attr:tenant_id', None)])
            except Exception, ex:
                LOG.error("Can't found tenant %s" % ex)
            setattr(volume, "instance_id", server_id)
            setattr(volume, "status_link",
                reverse('get_volume_status', args=[volume.id]))
    except Unauthorized:
        raise
    except Exception, ex:
        volumes = []
        LOG.error("ClientException in volume index. %s" % ex)

    if volume_name != '':
        volumes = [v for v in volumes
                   if v.display_name.find(volume_name) >= 0]

    args['list'] = volumes
    args['volume_name'] = volume_name

    created_at = timezone.now().utcnow()
    uuid = md5.new(str(created_at)).hexdigest()
    args['uuid'] = uuid
    vu.uuid = uuid

    return args


@require_GET
def volume_status(request, volume_id):
    if request.is_ajax():
        instance_id = None
        other_error = False
        try:
            volume = api.volume_get(request, volume_id)
            att = volume.attachments
            if len(att) > 0:
                instance_id = att[0]['server_id']
        except Unauthorized:
            raise
        except exceptions.NotFound, enf:
            volume = None
            LOG.error("the volume not found the error is %s" % enf)
        except Exception, ex:
            other_error = True
            volume = None
            LOG.error("the volume not found the error is %s" % ex)

        if volume:
            volume_status = getattr(volume, 'status', 'None')

            if volume_status == 'error_deleting':
                vu.volume_id = None
        else:
            if vu.volume_id == volume_id:
                vu.volume_id = None
            if other_error:
                volume_status = 'Failed to get state'
            else:
                volume_status = 'None'
        return HttpResponse(
            jsonutils.dumps(
                {"status": get_text(volume_status), "instance_id": instance_id,
                 "volume_id": volume_id}))
    raise NotFound


@require_GET
def volume_detail(request, volume_id):
    """
    :param request: request object
    :param volume_id: the volume's id
    :return view<'volume_manage/detail.html'>: view get_volume_detail
    """
    try:
        volume = api.volume_get(request, volume_id)
        #        create_time = (dateutil.parser.parse(volume.created_at) + abs(
        #            datetime.now() - datetime.utcnow())).strftime(
        #            "%Y-%m-%d %H:%M:%S")
        #        setattr(volume, "create_time", create_time)

        try:
            tenant_id = getattr(volume, 'os-vol-tenant-attr:tenant_id',None)
            tenant = api.tenant_get(request, tenant_id,getattr(request.user,"is_superuser",True))
        except Exception,ex:
            LOG.error("no tenant id,the error is %s" %ex)
            tenant = None

            pass

        if volume is None:
            return HttpResponse({"message": "The volume does not exist",
                                 "statusCode": UI_RESPONSE_DWZ_ERROR},
                status=UI_RESPONSE_ERROR)
    except Unauthorized:
        raise
    except Exception, ex:
        msg = 'Can not get volume detail information!'
        LOG.error('Can not get volume detail information! the error is %s' % ex)

        return HttpResponse(jsonutils.dumps(
            {"message": get_text(msg), "statusCode": UI_RESPONSE_DWZ_ERROR,
             "callbackType": "closeCurrent"}))

    else:
        tenant_name = ''
        if tenant:
            setattr(volume,"tenant_name",tenant.name)
            setattr(volume,"tenant_id",tenant_id)
        return shortcuts.render(request, 'volume_manage/detail.html',
            {'volume': volume})


@check_permission('Create Volume')
@require_GET
def create_volume_form(request, tenant_id, snapshot_id):
    """
    :param request: request object
    :return view<'volume_manage/create.html'>: the view create volume table
    """
    form = CreateVolumeForm()

    try:
        tenants = api.tenant_list(request,
            getattr(request.user, 'is_superuser', True))
    except Unauthorized:
        raise
    except Exception, ex:
        LOG.error('tenants not found,the error is %s' % ex)
        tenants = []

    tenants_dic = SortedDict([(tenant.id, getattr(tenant, "name")) for tenant in
                              tenants if tenant.enabled])

    current_tenant = getattr(request.user, 'tenant_id', None)

    try:
        if tenant_id != 'tenant':
            if switch_tenants(request, tenant_id):
                usages = quotas.tenant_quota_usages(request)
        else:
            usages = quotas.tenant_quota_usages(request)
    except Unauthorized:
        raise
    except Exception, ex:
        LOG.error("usages not found ,the error is %s" % ex)
        usages = None

    snapshots = []
    if snapshot_id == vu.uuid:
        snapshot = None
        snapshots = []
        try:
            if switch_tenants(request, current_tenant):
                snapshots = api.volume_snapshot_list(request)
        except Unauthorized:
            raise
        except Exception, ex:
            LOG.error("Can found snapshot list,the error is %s" % ex)

            snapshots = []
    else:
        try:
            snapshot = api.volume_snapshot_get(request, snapshot_id)
            setattr(snapshot, 'project_name', tenants_dic[tenant_id])
            setattr(snapshot, 'tenant_id', tenant_id)
        except Unauthorized:
            raise
        except Exception, ex:
            LOG.error("the snapshot is not found!the error is %s" % ex)
            snapshot = None

    return shortcuts.render(request, 'volume_manage/create.html',
        {'form': form, "tenants_dic": tenants_dic, "usages": usages,
         "snapshot": snapshot, "snapshots": snapshots,
         "current_tenant": current_tenant})


@require_GET
def fresh_progress_bar(request):
    tenant_id = None
    if request.GET.has_key('tenant_id'):
        tenant_id = request.GET['tenant_id']

    if tenant_id is not None:
        switch_tenants(request, tenant_id)

    try:
        usages = quotas.tenant_quota_usages(request)
    except Unauthorized:
        raise
    except Exception, ex:
        LOG.error("usages not found ,the error is %s" % ex)
        usages = None

    try:
        snapshots = api.volume_snapshot_list(request)
    except Unauthorized:
        raise
    except Exception, ex:
        LOG.error("Can found snapshot list,the error is %s" % ex)
        snapshots = []

    return shortcuts.render(request, "volume_manage/progress_bar_temp.html",
        {"usages": usages, "snapshots": snapshots})


@require_POST
@UIResponse("Volume Manage", "get_volume_list")
def create_volume_action(request):
    """
    :param request: request object
    :return view<'get_volume_list OR volume_manage/create.html'>: the corresponding view
    """
    form = CreateVolumeForm(request.POST.copy())
    _status_code = UI_RESPONSE_DWZ_ERROR
    object_name = ''
    volume_type = None
    try:
        object_name = request.POST['volume_name']
    except Exception, ex:
        LOG.error("the error is %s" % ex)

    if form.is_valid():
        data = form.cleaned_data
        try:
            tenant_id = data['tenant_id']

            if data['volume_name'].find(" ") >= 0:
                _msg = "Contains one or multiple Spaces,Please enter again!"
            else:
                if tenant_id == '':
                    _msg = "Please select tenant"
                else:
                    switch_tenants(request, tenant_id)
                    try:
                        size = VOLUMES_CHOICE[data['volume_size']]
                    except Exception, ex:
                        size = VOLUMES_CHOICE['small']

                    if api.check_resource(request, size,
                        data['volume_name'],
                        data['volume_description'],
                        data['snapshot_id']):
                        snapshot_id = data['snapshot_id']
                        if not snapshot_id:
                            snapshot_id = None

                        api.volume_create(request, size, data['volume_name'],
                            data['volume_description'], volume_type,
                            snapshot_id=snapshot_id)

                        _msg = get_text(
                            'Volume %s has been created successfully!') % data[
                                                                          'volume_name']
                        _status_code = UI_RESPONSE_DWZ_SUCCESS
                    else:
                        _msg = get_text('Not enough server resources,Volume %s '
                                        'has been created failed!') % data[
                                                                      'volume_name']
                        _status_code = UI_RESPONSE_DWZ_ERROR
        except Unauthorized:
            raise
        except LicenseForbidden:
            raise
        except Exception, ex:
            LOG.exception("ClientException in CreateVolume")
            _msg = "No disk can be created!"

            if ex.message.count("status must be available") > 0:
                _msg = "Snapshot status must be available!"

            _status_code = UI_RESPONSE_DWZ_ERROR
    else:
        _msg = get_text("Volume %s has been created failed!") % ''

    return HttpResponse(jsonutils.dumps(
        {"message": get_text(_msg), "statusCode": _status_code,
         "callbackType": "closeCurrent",
         "object_name": object_name}))


@require_GET
def delete_single_volume_form(request, volume_id):
    return shortcuts.render(request, 'volume_manage/delete.html',
        {'volume_id': volume_id})


@check_permission('Delete Volume')
@require_http_methods(['DELETE'])
@UIResponse('Volume Manage', 'get_volume_list')
def delete_single_volume(request):
    status_code = UI_RESPONSE_DWZ_ERROR
    object_name = ''

    if vu.volume_id:
        try:
            volume = api.volume_get(request, vu.volume_id)

            if volume and volume.status != "deleting":
                vu.volume_id = None
        except Unauthorized:
            raise
        except Exception, ex:
            vu.volume_id = None
            LOG.error("the error is %s" % ex)

    if vu.volume_id is None:
        msg = 'Delete volume successfully!'

        try:
            volume_id = request.POST['volume_id']
            api.volume_delete(request, volume_id)
            status_code = UI_RESPONSE_DWZ_SUCCESS
        except Unauthorized:
            raise
        except Exception, ex:
            msg = 'Delete volume error!'

            if ex.message.count('dependent snapshots') > 0:
                msg = "Please delete Volume Snapshot corresponding to the Volume!"

            LOG.error(ex)
            return HttpResponse(
                {"message": get_text(msg), "statusCode": status_code},
                status=UI_RESPONSE_ERROR)

        vu.volume_id = volume_id

        try:
            volume = api.volume_get(request, volume_id)
            object_name = volume.display_name
        except Exception, ex:
            LOG.error("the error is %s" % ex)
    else:
        msg = 'Existing volume is deleted,please wait...'
        object_name = ''

    return HttpResponse(
        {"message": get_text(msg), "statusCode": status_code,
         "object_name": object_name},
        status=status_code)


@require_http_methods(["DELETE"])
@UIResponse("Volume Manage", "get_volume_list")
def delete_volumes(request):
    """
    :param request: request object
    :return view<'get_volume_list'>: the view get_volume_list
    """
    _status_code = UI_RESPONSE_DWZ_ERROR
    _msg = 'Delete Volumes Failed!'
    data = request.POST.getlist("delete_volume")
    if data:
        for volume_id in data:
            try:
                volume = api.volume_get(request, volume_id)
                if volume.status in DELETABLE_STATES:
                    try:
                        api.volume_delete(request, volume.id)
                        _msg = "Delete Volumes Successfully"
                        _status_code = UI_RESPONSE_DWZ_SUCCESS
                    except Unauthorized:
                        raise
                    except Exception, ex:
                        if ex.code != UI_RESPONSE_BADREQUEST:
                            LOG.error("delete volumes failed error is %s" % ex)
                        else:
                            LOG.error('BadRequest %s' % ex)
            except Unauthorized:
                raise
            except Exception, ex:
                LOG.error("Volume is not found error is %s" % ex)

    return HttpResponse({"message": get_text(_msg), "statusCode": _status_code},
        status=_status_code)


@check_permission('Attach Volume')
@require_GET
def attach_volume_form(request, tenant_id, volume_id):
    instances = []
    try:
        if switch_tenants(request, tenant_id):
            instance_list = api.server_list(request)
            for instance in instance_list:
                if instance.status in ACTIVE_STATES:
                    instances.append((instance.id, '%s' % instance.name))
    except Unauthorized:
        raise
    except Exception, ex:
        instances = []
        LOG.error("Can not get instance list %s" % ex)
    if instances:
        instances.insert(0, ("", _("Select an instance")))
    else:
        instances = (("", _("No instances available")),)
    return shortcuts.render(request, 'volume_manage/attach.html',
        {'instances': instances, 'volume_id': volume_id})


@require_POST
@UIResponse('Volume Manage', 'get_volume_list')
def handle_attach_volume(request, volume_id):
    _status_code = UI_RESPONSE_DWZ_ERROR
    flag = True
    msg = "Can not attach volume to instance!"
    try:
        used_device = []
        instance = get_instance_show_data(request, request.POST["instance_id"])
        volumes = getattr(instance, 'volumes', [])

        for volume in volumes:
            used_device.append(volume.device[7])
    except Unauthorized:
        raise
    except Exception, ex:
        flag = False
        msg = "Instance does not exist!"
        LOG.error(ex)

    if flag:
        ava_device = [c for c in VOLUMES if c not in used_device]
        try:
            api.nova.instance_volume_attach(request,
                volume_id,
                request.POST['instance_id'], "/dev/vd" + ava_device[0])
            msg = 'Attaching volume successfully!'
            LOG.info(msg)
            _status_code = UI_RESPONSE_DWZ_SUCCESS
        except Unauthorized:
            raise
        except Exception, ex:
            LOG.exception("ClientException in AttachVolume %s" % ex)
            if ex.message.count("/dev/vd" + ava_device[0]) > 0:
                def check_device(device):
                    try:
                        api.nova.instance_volume_attach(request, volume_id,
                            request.POST['instance_id'],
                            device)
                        return True
                    except Exception, ex:
                        LOG.exception("ClientException in AttachVolume %s" % ex)
                        return False

                ava_device.pop(0)

                for ad in ava_device:
                    if check_device("/dev/vd" + ad):
                        msg = 'Attaching volume successfully!'
                        _status_code = UI_RESPONSE_DWZ_SUCCESS
                        break

                return HttpResponse(
                    {"message": get_text(msg), "statusCode": _status_code},
                    status=_status_code)
        return HttpResponse(
            {"message": get_text(msg), "statusCode": _status_code},
            status=_status_code)


@require_GET
def detach_volume(request, volume_id, instance_id):
    """
    :param request:request object
    :param volume_id:the id of one volume,its information will show
    :param instance_id:the id of one instance,its information will show
    :return:
    """
    return shortcuts.render(request, 'volume_manage/detach.html',
        {'volume_id': volume_id, 'instance_id': instance_id})


@check_permission('Detach Volume')
@require_POST
@UIResponse('Volume Manage', 'get_volume_list')
def handle_detach_volume(request, volume_id, instance_id):
    """
    :param request: request object
    :param volume_id:the id of one volume,its information will show
    :param instance_id:the id of one instance,its information will show
    :return:
    """
    _msg = "Can not detach volume!"

    _status_code = UI_RESPONSE_DWZ_ERROR
    try:
        api.nova.instance_volume_detach(request, instance_id, volume_id)
        _status_code = UI_RESPONSE_DWZ_SUCCESS
        _msg = "Detach successfully!"
    except Unauthorized:
        raise
    except Exception, ex:
        LOG.error("detach volume failed,the error is %s" % ex)

    return HttpResponse(
        {"message": get_text(_msg), "statusCode": _status_code,
         "volume_id": volume_id},
        status=_status_code)


@require_GET
def get_instance_name(request):
    instance_name = None
    instance_id = request.GET['instance_id']
    try:
        instance = api.server_get(request, instance_id)
        instance_name = instance.name
    except Unauthorized:
        raise
    except Exception, ex:
        LOG.error("instance is not found error is %s") % ex

    return HttpResponse(jsonutils.dumps({"instance_name": instance_name}))


def get_instance_show_data(request, instance_id):
    """
    :param request: request object
    :param instance_id: the id of one instance,its information will show
    :return _instance: one instance object
    """
    try:
        instance = api.server_get(request, instance_id)
        instance.volumes = api.nova.instance_volumes_list(request,
            instance_id)
        # Sort by device name
        instance.volumes.sort(key=lambda vol: vol.device)
        instance.full_flavor = api.flavor_get(request,
            instance.flavor["id"])
        instance.security_groups = api.server_security_groups(request,
            instance_id)
    except Unauthorized:
        raise
    except Exception, ex:
        if ex.code == UI_RESPONSE_NOTFOUND:
            msg = _('Can not found instance (%s)' % ex)
        else:
            msg = _('Unable to retrieve details for instance "%s".' % ex)
        LOG.error(msg)
        instance = None
    return instance


@require_GET
def get_volume_type_list(request):
    try:
        volume_type_list = api.volume_type_list(request)
    except Unauthorized:
        raise
    except Exception, ex:
        volume_type_list = []
        LOG.error("Can found volume type list,the error is %s" % ex)

    return shortcuts.render(request, 'volume_manage/volume_type_list.html',
        {'volume_type_list': volume_type_list})


@require_GET
def create_volume_type_form(request):
    return shortcuts.render(request,
        'volume_manage/volume_type_create.html')


@require_POST
def create_volume_type_action(request):
    _name = ''
    _msg = "Create volume type Failed!"
    _status_code = UI_RESPONSE_DWZ_ERROR
    try:
        _name = request.POST['volume_type_name']
    except Unauthorized:
        raise
    except Exception, ex:
        LOG.error("volume_type_name is not found the error is %s" % ex)

    try:
        api.volume_type_create(request, _name)
        _status_code = UI_RESPONSE_DWZ_SUCCESS
        _msg = "Create volume type Successfully!"
    except Unauthorized:
        raise
    except Exception, ex:
        LOG.error("create volume type error the error is %s" % ex)

    return HttpResponse(
        jsonutils.dumps(
            {"message": get_text(_msg), "statusCode": _status_code,
             "callbackType": "closeCurrent", "object_name": _name}))


@require_http_methods(['DELETE'])
def volume_type_delete_action(request):
    _msg = 'Volume type delete Failed!'
    _status_code = UI_RESPONSE_DWZ_ERROR
    try:
        volume_type_id = request.POST['volume_type_id']
        volume_type_name = request.POST['volume_type_name']
        volumes = api.volume_list(request)
        flag = False
        for volume in volumes:
            if volume_type_name == volume.volume_type:
                flag = True
                break
        if flag:
            _msg = "Volume uses the type,the type cannot be deleted!"
        else:
            api.volume_type_delete(request, volume_type_id)
            _status_code = UI_RESPONSE_DWZ_SUCCESS
            _msg = "Volume type delete Successfully!"
    except Unauthorized:
        raise
    except Exception, ex:
        LOG.error("volume type delete failed the error is %s" % ex)
        volume_type_name = ''

    return HttpResponse(
        jsonutils.dumps(
            {"message": get_text(_msg), "statusCode": _status_code,
             "object_name": volume_type_name}))


@check_permission('Create Volume Snapshot')
@require_GET
def create_volume_snapshot_form(request, tenant_id, volume_id):
    return shortcuts.render(request, 'volume_manage/create_snapshot.html',
        {"volume_id": volume_id, "tenant_id": tenant_id})


@require_POST
def create_volume_snapshot(request):
    snapshot_form = CreateVolumeSnapshot(request.POST.copy())
    msg = "Create Volume Snapshot Failed!"
    _status_code = UI_RESPONSE_DWZ_ERROR
    snapshot_name = ''
    if snapshot_form.is_valid():
        data = snapshot_form.cleaned_data
        snapshot_name = data['name']
        try:
            tenant_id = data['tenant_id']
            if switch_tenants(request, tenant_id) is not None:
                api.volume_snapshot_create(request, data['volume_id'],
                    snapshot_name,
                    data['description'])
                _status_code = UI_RESPONSE_DWZ_SUCCESS
                msg = "Create Volume Snapshot Successfully!"
        except Unauthorized:
            raise
        except LicenseForbidden:
            raise
        except Exception, ex:
            LOG.error("create volume snapshot %s" % ex)

            if ex.message.count(
                "'NoneType' object has no attribute 'iteritems'") > 0:
                msg = get_text(
                    "Not enough server resources,Volume Snapshot %s has been created failed!") % snapshot_name

    return HttpResponse(
        jsonutils.dumps(
            {"message": get_text(msg), "statusCode": _status_code,
             "callbackType": "closeCurrent",
             "object_name": snapshot_name}))


@require_GET
@Pagenation('volume_manage/snapshot_index.html')
def get_snapshot_index(request):
    snapshots = []
    tenants_dic = {}
    args = {}

    if request.GET.has_key('tenant_id'):
        tenant_id = request.GET['tenant_id']
        switch_tenants(request, tenant_id)
    else:
        tenant_id = None

    try:
        tenants = api.tenant_list(request,
            getattr(request.user, 'is_superuser', True))

        snapshots = api.volume_snapshot_list(request)

        volumes = api.volume_list(request)

        volumes_dic = SortedDict([(volume.id, volume) for volume in
                                  volumes])

        tenants_dic = SortedDict(
            [(tenant.id, tenant.name) for tenant in tenants])

        for snapshot in snapshots:
            volume_name = None
            tenant_name = None
            try:
                volume_name = volumes_dic[snapshot.volume_id].display_name

                tenant_name = tenants_dic[snapshot.project_id]
            except Exception, ex:
                LOG.error("volume is not found the error is %s" % ex)
            setattr(snapshot, 'volume_name', volume_name)
            setattr(snapshot, 'project_name', tenant_name)
            setattr(snapshot, 'tenant_id', snapshot.project_id)
    except Unauthorized:
        raise
    except Exception, ex:
        LOG.error("snapshots is not found the error is %s" % ex)

    args['list'] = snapshots
    args["tenants_dic"] = tenants_dic
    args['tenant_id'] = tenant_id

    return args


@require_http_methods(['DELETE'])
@UIResponse('Snapshot Manage', 'get_snapshot_index')
def snapshots_delete(request):
    snapshots_ids = request.POST.getlist('delete_snapshot')
    _status_code = UI_RESPONSE_DWZ_ERROR
    _msg = 'Delete Volume Snapshots Failed!'
    if snapshots_ids:
        for snapshots_id in snapshots_ids:
            try:
                api.volume_snapshot_delete(request, snapshots_id)
                _status_code = UI_RESPONSE_DWZ_SUCCESS
                _msg = 'Delete Volume Snapshots Successfully!'
            except Unauthorized:
                raise
            except Exception, ex:
                LOG.error("delete snapshot failed,the error is %s" % ex)

    return HttpResponse({"message": _msg, "statusCode": _status_code},
        status=_status_code)


@check_permission('Delete Snapshot')
@require_http_methods(['DELETE'])
@UIResponse('Snapshot Manage', 'get_snapshot_index')
def snapshot_delete(request, snapshot_id):
    _status_code = UI_RESPONSE_DWZ_ERROR

    if vu.snapshot_id:
        try:
            api.volume_snapshot_get(request, vu.snapshot_id)
        except Unauthorized:
            raise
        except exceptions.NotFound, enf:
            LOG.error("volume snapshot not found %s" % enf)
            vu.snapshot_id = None

    if vu.snapshot_id is None:
        _msg = 'Delete Volume Snapshot Failed!'
        snapshot_name = ''
        if snapshot_id:
            try:
                api.volume_snapshot_delete(request, snapshot_id)
                _status_code = UI_RESPONSE_DWZ_SUCCESS
                _msg = 'Delete Volume Snapshot Successfully!'
                vu.snapshot_id = snapshot_id
            except Unauthorized:
                raise
            except Exception, ex:
                LOG.error("delete snapshot failed,the error is %s" % ex)

            try:
                snapshot = api.volume_snapshot_get(request, snapshot_id)
                snapshot_name = snapshot.display_name
            except Unauthorized:
                raise
            except Exception, ex:
                LOG.error(ex)
    else:
        _msg = 'Existing volume snapshot is deleted,please wait...'
        snapshot_name = ''

    return HttpResponse({"message": _msg, "statusCode": _status_code,
                         "object_name": snapshot_name},
        status=_status_code)


@require_GET
def get_snapshot_status(request, snapshot_id):
    other_error = False
    try:
        snapshot = api.volume_snapshot_get(request, snapshot_id)
    except Unauthorized:
        raise
    except exceptions.NotFound, enf:
        LOG.error("volume snapshot not found %s" % enf)
        snapshot = None
    except Exception, ex:
        other_error = True
        LOG.error("volume snapshot not found %s" % ex)
        snapshot = None

    snapshot_status = 'None'
    if snapshot:
        snapshot_status = snapshot.status
        if snapshot_status == 'error_deleting':
            vu.snapshot_id = None
    else:
        vu.snapshot_id = None
        if other_error:
            snapshot_status = 'Failed to get state'

    return HttpResponse(jsonutils.dumps(
        {"status": get_text(snapshot_status), "snapshot_id": snapshot_id}))


@require_GET
def get_snapshot_detail(request, snapshot_id):
    _status_code = UI_RESPONSE_DWZ_ERROR
    _msg = None
    if snapshot_id:
        try:
            snapshot = api.volume_snapshot_get(request, snapshot_id)

            if snapshot:
                volume = api.volume_get(request, snapshot.volume_id)
                volume_name = None
                if volume:
                    volume_name = volume.display_name

                setattr(snapshot, 'volume_name', volume_name)
        except Unauthorized:
            raise
        except Exception, ex:
            LOG.error("Get Snapshot detail failed,the error is %s" % ex)
            _msg = 'Get Snapshot detail failed'
    if _msg:
        return HttpResponse({'message': _msg, "statusCode": _status_code},
            _status_code=UI_RESPONSE_ERROR)
    return shortcuts.render(request, 'volume_manage/snapshot_detail.html',
        {'snapshot': snapshot})
