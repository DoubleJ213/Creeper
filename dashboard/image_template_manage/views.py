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
__date__ = '2012-02-21'
__version__ = 'v2.0.2'

from django.conf import settings

if settings.DEBUG:
    __log__ = """v2.0.1 image list;
    v2.0.2 create image
    """

import logging

LOG = logging.getLogger(__name__)

#    code begin
import time
import threading

import md5
from datetime import datetime

from django import shortcuts
from django.utils.translation import ugettext_lazy as _
from django.utils.text import normalize_newlines
from django.utils.datastructures import SortedDict
from django.http import HttpResponse
from django.core.cache import cache
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from novaclient import exceptions

from dashboard import api
from dashboard.exceptions import Unauthorized, NotFound, glance_LicenseForbidden, nova_LicenseForbidden
from dashboard.usage.quotas import tenant_quota_usages
from dashboard.utils import jsonutils, ui_response, UIResponse, Pagenation, check_permission
from dashboard.utils.i18n import get_text
from dashboard.utils.ui import UI_RESPONSE_DWZ_ERROR, UI_RESPONSE_DWZ_SUCCESS, UI_RESPONSE_ERROR
from dashboard.utils.image_utils import ImageUtils
import dashboard.instance_manage as Instance_Manage
from dashboard.authorize_manage.utils import switch_tenants, get_user_role_name
from dashboard.authorize_manage import ROLE_ADMIN
from dashboard.image_template_manage.forms import UpdateImageForm, CreateImageForm, CreateImageAndLaunchForm, LaunchImageInstanceForm, LaunchImagePrepareForm
from dashboard.instance_manage.models import Distribution

from models import ImageStatus

IMAGE_UTILS = ImageUtils()
IMAGE_UTILS_INS = ImageUtils()

def get_images_data(request):
    """
    :param request: request object
    :return images: images list with meta
    """
    all_images = []
    try:
        role_name = get_user_role_name(request)

        all_images, _more_images = api.image_list_detailed(request)
        image_list = []
        if role_name != ROLE_ADMIN:
            for im in all_images:
                if im.properties.has_key('image_type'):
                    if im.properties['image_type'] != 'snapshot' and (
                        im.is_public == True or im.owner == request.user.tenant_id):
                        image_list.append(im)
                elif im.is_public == True or im.owner == request.user.tenant_id:
                    image_list.append(im)
        else:
            for im in all_images:
                if im.properties.has_key('image_type'):
                    if im.properties['image_type'] != 'snapshot':
                        image_list.append(im)
                else:
                    image_list.append(im)

        all_images = image_list

        tenants_list = api.tenant_list_not_filter(request,
                                                  request.user.is_superuser)

        tenants_dic = SortedDict(
            [(tenant.id, tenant) for tenant in tenants_list])
        for images in all_images:
            try:
                setattr(images, "tenant", tenants_dic[images.owner])
            except Exception, ex:
                LOG.error("Can't found tenant %s" % ex)
    except Unauthorized:
        raise
    except Exception, exc:
        LOG.error('Can not retrieve images !%s.' % exc)
    return all_images


@check_permission('View Image')
@require_GET
@Pagenation('image_template_manage/index.html')
def image_list(request):
    """
    :param request: request object
    :return view<'image_template/index.html'>: the view of images list
    """
    images = []
    args = {}
    try:
        images = get_images_data(request)
    except Unauthorized:
        raise
    except Exception, exc:
        LOG.info('No image can be found!%s.' % exc)

    args['list'] = images

    return args


@check_permission('Update Image')
@require_GET
def update_image_template_form(request, image_id):
    """
    :param request: request object
    :param image_id: the image's id which will be edited
    :return view<'image_template_manage/update.html OR get_image_list'>: the corresponding view
    """
    template_name = 'image_template_manage/update.html'
    try:
        form = UpdateImageForm(request, image_id)
        return shortcuts.render(request, template_name,
                                {'form': form, 'image_id': image_id})
    except Exception, exc:
        LOG.error('error is %s.' % exc)
        return shortcuts.redirect('get_image_list')

#: Modify by lingkang 2013-03-14 auto refresh after doing sth
@check_permission('Update Image')
@require_POST
@UIResponse('Image Manage', 'get_image_list')
def update_image_template(request, image_id):
    """
    :param request: request object
    :param image_id: the image's id which will be update
    :return view<get_image_list OR hard_template_manage/update.html>: the corresponding view
    """
    form = UpdateImageForm(request, image_id, request.POST)
    if form.is_valid():
        data = form.cleaned_data
        kwargs = {'is_public': data['enabled'],
                  'min_disk': data['min_disk'],
                  'min_ram': data['min_ram'],
                  'name': data['name'],
                  'disk_format': data['disk_format'],
                  'properties': {}}
        try:
            api.image_update(request, image_id, **kwargs)
            LOG.info('Update image successfully ! ')
            return HttpResponse({"message": "update image template Success",
                                 "statusCode": UI_RESPONSE_DWZ_SUCCESS,
                                 "object_name": data['name']},
                                status=UI_RESPONSE_DWZ_SUCCESS)
        except Unauthorized:
            raise
        except Exception, exc:
            msg = _('Can not update image !')
            LOG.error('Can not update image,error is %s !' % exc)
            return HttpResponse(
                {"message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR},
                status=UI_RESPONSE_ERROR)

    else:
        return HttpResponse(
            {"form": form, "message": "", "statusCode": UI_RESPONSE_DWZ_ERROR},
            status=UI_RESPONSE_ERROR)


@require_GET
def image_detail(request, image_id):
    """
    :param request: request object
    :param image_id: the image's id
    :return view<'image_template_manage/detail.html'>: the detail view
    """
    try:
        image = api.glance.image_get(request, image_id)
        tenant_img = api.tenant_get(request, tenant_id=image.owner, admin=True)
        setattr(image, "tenant", tenant_img.name)
    except Unauthorized:
        raise
    except Exception, exc:
        LOG.error('error is %s.' % exc)
    else:
        return shortcuts.render(request, 'image_template_manage/detail.html',
                                {'image': image})


@check_permission('Delete Image')
@require_GET
def delete_image_form(request, image_id):
    return shortcuts.render(request, 'image_template_manage/delete.html',
                            {'image_id': image_id})


#: Modify by lingkang 2013-03-14 auto refresh after doing sth
@check_permission('Delete Image')
@require_http_methods(['DELETE'])
@UIResponse('Image Manage', 'get_image_list')
def delete_image(request, image_id):
    """
    :param request: request object
    :param image_id: the image's id which will be deleted
    :return view<'get_image_list'>: the view of images list
    """
    try:
        image = api.glance.image_get(request, image_id)
        if image.deleted:
            return HttpResponse({"message": "Image has been already deleted.",
                                 "statusCode": UI_RESPONSE_DWZ_ERROR,
                                 "object_name": image.name},
                                status=UI_RESPONSE_ERROR)
        api.image_delete(request, image_id)

        return HttpResponse({"message": "delete image template success",
                             "statusCode": UI_RESPONSE_DWZ_SUCCESS,
                             "object_name": image.name},
                            status=UI_RESPONSE_DWZ_SUCCESS)

    except Unauthorized:
        raise
    except Exception, exc:
        msg = _('Can not delete image !')
        LOG.error('Can not delete image ! error is %s' % exc)
        return HttpResponse(
            {"message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR},
            status=UI_RESPONSE_ERROR)


@check_permission('Delete Image')
@require_POST
@UIResponse('Image Manage', 'get_image_list')
def delete_image_batch(request):
    """
    :param request: request object
    :param image_id: the image's id which will be deleted
    :return view<'get_image_list'>: the view of images list
    """
    try:
        image_check = request.POST.getlist('image_check')
        for image_id in image_check:
            image = api.glance.image_get(request, image_id)
            #            api.image_delete(request, image_id)
            image.delete()
        return HttpResponse({"message": "delete image template success",
                             "statusCode": UI_RESPONSE_DWZ_SUCCESS},
                            status=UI_RESPONSE_DWZ_SUCCESS)

    except Unauthorized:
        raise
    except Exception, exc:
        msg = _('Can not delete image !')
        LOG.error('Can not delete image ! error is %s' % exc)
        return HttpResponse(
            {"message": msg, "statusCode": UI_RESPONSE_DWZ_ERROR},
            status=UI_RESPONSE_ERROR)


def get_image_status(request, image_id):
    if request.is_ajax():
        image = api.glance.image_get(request, image_id)
        return HttpResponse(getattr(image, 'status', default=None))
    raise NotFound


@check_permission('ActiveAndStart')
@require_GET
def launch_form_image_template(request):
    """
    :param request: request object
    :param image_id: the image id from which to launch a instance
    :return view<'instance_manage/create.html'>: the from table to create instance
    """
    old_tenant_id = request.user.tenant_id
    kwargs = {
        'flavor_input_list': search_flavor_status(request),
        'flavor_list': Instance_Manage.views.flavor_list(request),
        'keypair_list': Instance_Manage.views.keypair_list(request),
        'security_group_list': security_group_list(
            request),
        'networks': Instance_Manage.views.network_list(request),
        'volume_list': Instance_Manage.views.volume_list(request)}

    form = LaunchImageInstanceForm(request, **kwargs)
    return shortcuts.render(request,
                            'image_template_manage/create_instance.html',
                            {'form': form, "old_tenant_id": old_tenant_id})


#@require_GET
#def create_instance_page(request):
#    """
#    :param request: request object
#    :return view<'prepare_manage/image_create.html'>: the view create image form
#    """
#    oldtenantid = request.user.tenant_id
#    kwargs = {
#        'flavor_input_list': Instance_Manage.views.search_flavor_status(
#            request),
#        #        'image_id': image_id,
#        'flavor_list': Instance_Manage.views.flavor_list(request),
#        'keypair_list': Instance_Manage.views.keypair_list(request),
#        'security_group_list': Instance_Manage.views.security_group_list(
#            request),
#        'networks': Instance_Manage.views.network_list(request),
#        'volume_list': Instance_Manage.views.volume_list(request)}
#
#    switch_tenants(request, oldtenantid)
#    try:
#        usages = tenant_quota_usages(request)
#    except Exception, e:
#        usages = None
#        LOG.error('Can not get tenant usages. %s' % e)
#    form = LaunchImagePrepareForm(request, **kwargs)
#    created_at = datetime.now().utcnow()
#    uuid = md5.new(str(created_at)).hexdigest()
#    return shortcuts.render(request,
#                            'image_template_manage/create1.html',
#                            {'form': form,
#                             'oldtenantid': oldtenantid, 'usages': usages,
#                             'uuid': uuid})


def security_group_list(request):
    """
    :param request: request object
    :return security group: all security groups
    """
    try:
        groups = api.nova.security_group_list(request)
        security_group_list = [(sg.name,sg.name) for sg in groups]
    except Unauthorized:
        raise
    except Exception, e:
        LOG.error('Unable to retrieve list of security groups.%s' % e)
        security_group_list = []
    return security_group_list

@check_permission('Create Image')
@require_GET
def create_image_form(request):
    """
    :param request: request object
    :return view<'image_template_manage/create.html'>: the view create image form
    """
    software_name = request.GET.get('software_name', '')
    old_tenant_id = request.user.tenant_id
    form = CreateImageForm(request)

    created_at = datetime.now().utcnow()
    uuid = md5.new(str(created_at)).hexdigest()
    return shortcuts.render(request, 'image_template_manage/create.html',
                            {'form': form, 'old_tenant_id': old_tenant_id,
                             'uuid': uuid, 'software_name': software_name})

TIME_CHECK_PER_IMAGE_STATUS_SECONDS = 5
UI_CYCLE_IMG_IMAGE_TIME = 25
UI_CYCLE_IMG_INSTANCE_TIME = 50

UI_CREATE_PER_IMAGE_CREATING = 1
UI_CREATE_PER_IMAGE_CREATED = 2
UI_CREATE_PER_INSTANCE_CREATING = 3
UI_CREATE_PER_INSTANCE_CREATED = 4
UI_CREATE_IMAGE_AND_INSTANCE_FAILED = 5
UI_NOT_FIND_CREATE_FILE = 6
UI_CREATE_PER_INSTANCE_FAILED = 7
UI_CREATE_PER_IMAGE_TIMEOUT = 8
UI_CREATE_PER_INSTANCE_TIMEOUT = 9
UI_CREATE_IMAGE_FAILED = 11
UI_INSTANCE_LIMIT_FAILED = 13
UI_INSTANCE_RESOURCE_NOT_ENOUGH = 14
UI_IMAGE_DISK_NOT_ENOUGH = 15
# define end
class  CreateInstanceThread(threading.Thread):
    _instance = None

    def __init__(self, request, data):
        threading.Thread.__init__(self)
        self.request = request
        self.data = data

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(CreateInstanceThread, cls).__new__(cls, *args,
                                                                     **kwargs)

        return cls._instance

    def run(self):
        image_status = None
        try:
            uuid = self.data['u_uid']
            image_status = ImageStatus(uuid=uuid,
                                       status=UI_CREATE_PER_IMAGE_CREATING)
            image_status.save()
            img_status = create_image_thread(self, image_status)

            if not img_status:
                IMAGE_UTILS_INS.threadObj = None
                IMAGE_UTILS_INS.timezone = None
                return

            instance = create_instance_thread(self, image_status, img_status)
#            if instance is None:
#                image = api.glance.image_get(self.request, img_status.id)
#                image.delete()

            IMAGE_UTILS_INS.threadObj = None
            IMAGE_UTILS_INS.timezone = None
        except Unauthorized:
            IMAGE_UTILS_INS.threadObj = None
            IMAGE_UTILS_INS.timezone = None
            raise
        except Exception, exc:
            LOG.error("UploadfileThread failed.%s." % exc)
            IMAGE_UTILS_INS.threadObj = None
            IMAGE_UTILS_INS.timezone = None
            try:
                image_status.status = UI_CREATE_IMAGE_AND_INSTANCE_FAILED
                image_status.save()
            except exceptions, ex:
                LOG.error('error is:%s' % ex)

            return

#Just as an argument
#begin
PARAMETER_NUMBER_ZERO = 0
PARAMETER_NUMBER_ONE = 1
PARAMETER_NEGATIVE_ONE = -1
PARAMETER_NEGATIVE_TWO = -2
PARAMETER_NEGATIVE_THREE = -3

INSTANCE_LIMIT_PER_USER = 6
UI_IMAGE_STATUS_ACTIVE = "active"
UI_INSTANCE_STATUS_ACTIVE = "ACTIVE"
UI_INSTANCE_STATUS_ERROR = "ERROR"
UI_INSTANCE_STATUS_RESOURCE_IS_NOT_ENOUGH = "RESOURCE_IS_NOT_ENOUGH"
#end
#create instance
def create_instance_thread(self, image_instance_status_thr, img_status):
    user_id = None
    dist_user_id = None
    if 'user' in self.request.POST:
        user_id = self.request.POST['user']
    if self.data[
       'name_launch'] != ''  and img_status.status == UI_IMAGE_STATUS_ACTIVE:
        image_instance_status_thr.status = UI_CREATE_PER_INSTANCE_CREATING
        image_instance_status_thr.save()
        try:
            instance = None
            if len(self.data['volume']) > PARAMETER_NUMBER_ZERO:
                if self.data['delete_on_terminate']:
                    delete_on_terminate = PARAMETER_NUMBER_ONE
                else:
                    delete_on_terminate = PARAMETER_NUMBER_ZERO
                dev_mapping = {self.data['device_name']: (
                    "%s::%s" % (self.data['volume'], delete_on_terminate))}
            else:
                dev_mapping = None
            networks = self.data['networks']
            if networks:
                nic_s = [{"net-id": net_id, "v4-fixed-ip": ""}
                         for net_id in networks]
            else:
                nic_s = None

            switch_tenants(self.request, self.data['tenant_id'])
            instance_test = api.server_create(self.request,
                                              dist_user_id,
                                              self.data['name_launch'],
                                              img_status.id,
                                              self.data['flavor'],
                                              self.data.get('keypair'),
                                              normalize_newlines(
                                                  self.data.get('user_data')),
                                              self.data.get('security_groups'),
                                              dev_mapping, nics=nic_s,
                                              instance_count=self.data.get(
                                                  'count'))
            if user_id:
                if Distribution.objects.filter(
                    user_id=user_id).count() >= INSTANCE_LIMIT_PER_USER:
                    _msg = _("Current user's instances reach limit %d.") % (
                        INSTANCE_LIMIT_PER_USER)
                else:
                    _relationship = Distribution(instance_id=instance_test.id,
                                                 user_id=user_id)
                    try:
                        _relationship.save()
                    except Exception, e:
                        LOG.error(
                            'create instance-user relationship failed.%s' % e)
                        _msg = 'Can not create instance-user relationship.'
#            if_con = UI_CYCLE_IMG_INSTANCE_TIME
#            while if_con > PARAMETER_NUMBER_ZERO:
#                instance = api.server_get(self.request, instance_test.id)
#                if_con -= PARAMETER_NUMBER_ONE
#                if instance.status == UI_INSTANCE_STATUS_ACTIVE:
#                    if_con = PARAMETER_NEGATIVE_ONE
#                    image_instance_status_thr.instance_id = instance.id
#                    image_instance_status_thr.save()
#                    break
#                if instance.status == UI_INSTANCE_STATUS_ERROR:
#                    if_con = PARAMETER_NEGATIVE_TWO
#                    break
#                if instance.status == UI_INSTANCE_STATUS_RESOURCE_IS_NOT_ENOUGH:
#                    if_con = PARAMETER_NEGATIVE_THREE
#                    break
#                time.sleep(TIME_CHECK_PER_IMAGE_STATUS_SECONDS)

#            if PARAMETER_NEGATIVE_THREE == if_con:
#                try:
#                    image = api.glance.image_get(self.request, img_status.id)
#                    image.delete()
#                except Unauthorized:
#                    raise
#                except Exception, exc:
#                    msg = _('Can not delete image !')
#                    LOG.error('%s,%s' % (msg, exc))
#                image_instance_status_thr.status = UI_INSTANCE_RESOURCE_NOT_ENOUGH
#                image_instance_status_thr.save()
#                return None

#            if PARAMETER_NEGATIVE_TWO == if_con:
#                try:
#                    image = api.glance.image_get(self.request, img_status.id)
#                    image.delete()
#                except Unauthorized:
#                    raise
#                except Exception, exc:
#                    msg = _('Can not delete image !')
#                    LOG.error('%s,%s' % (msg, exc))
#                image_instance_status_thr.status = UI_CREATE_PER_INSTANCE_FAILED
#                image_instance_status_thr.save()
#                return None

#            if PARAMETER_NEGATIVE_ONE != if_con:
#                image_instance_status_thr.status = UI_CREATE_PER_INSTANCE_TIMEOUT
#                image_instance_status_thr.save()
#                return None
            if instance_test == True:
                image_instance_status_thr.status = UI_CREATE_PER_INSTANCE_CREATED
#            image_instance_status_thr.instance_id = instance_test.id
                image_instance_status_thr.save()
                LOG.info('Instance "%s" has submit to check.' % self.data["name"])
            else:
                image_instance_status_thr.status = UI_CREATE_IMAGE_AND_INSTANCE_FAILED
                image_instance_status_thr.save()
#            return instance
        except Unauthorized:
            raise
        except exceptions.OverLimit, exc:
            LOG.error('Over the limit,%s' % exc)
            image_instance_status_thr.status = UI_INSTANCE_LIMIT_FAILED
            image_instance_status_thr.save()
            return None
        except Exception, exc:
            LOG.error('Unable to launch instance: %s' % exc)
            image_instance_status_thr.status = UI_CREATE_PER_INSTANCE_FAILED
            image_instance_status_thr.save()
            return None

#create image
def create_image_thread(self, image_status_thr):
    if self.data['disk_format'] in ('ami', 'aki', 'ari',):
        container_format = self.data['disk_format']
    else:
        container_format = 'bare'
    kwargs = {
        'name': self.data['name'],
        'container_format': container_format,
        'disk_format': self.data['disk_format'],
        'min_disk': (self.data['min_disk'] or 0),
        'min_ram': (self.data["min_ram"] or 0),
        'is_public': self.data['is_public']
    }

    try:
        image_file = open(self.data['image_data'], 'rb')
        kwargs['data'] = image_file
        try:
            image_create = api.image_create(self.request, **kwargs)

            image_status_thr.status = UI_CREATE_PER_IMAGE_CREATED
            image_status_thr.save()
        except Unauthorized:
            image_status_thr.threadObj = None
            image_status_thr.timezone = None
            raise
        except Exception, exc:
            LOG.error(exc)
            image_status_thr.status = UI_IMAGE_DISK_NOT_ENOUGH
            image_status_thr.save()
            return None
    except Exception, exc:
        LOG.error(
            'Can not open the software or image_file format wrong,%s !' % exc)
        image_status_thr.status = UI_CREATE_IMAGE_FAILED
        image_status_thr.save()
        return None

    img_cre_time = UI_CYCLE_IMG_IMAGE_TIME
    while img_cre_time > PARAMETER_NUMBER_ZERO:
        img_status = api.glance.image_get(self.request, image_create.id)
        img_cre_time -= PARAMETER_NUMBER_ONE
        if img_status is None:
            LOG.error('Image is None:Failed')
        if img_status.status == UI_IMAGE_STATUS_ACTIVE:
            img_cre_time = PARAMETER_NEGATIVE_ONE
            break

        time.sleep(TIME_CHECK_PER_IMAGE_STATUS_SECONDS)

    if PARAMETER_NEGATIVE_ONE != img_cre_time:
        image_status_thr.status = UI_CREATE_PER_IMAGE_TIMEOUT
        image_status_thr.save()
        return None

    return image_create


#: Modify by liuh 2013-05-30 auto refresh after doing sth
@require_POST
@UIResponse('Image Manage', 'get_image_list')
def create_image_goto_instance(request):
    """
    :param request: request object
    :return view<'get_image_list OR image_template_manage/create.html'>: the corresponding view
    """
    kwargs = {'flavor_list': Instance_Manage.views.flavor_list(request),
              'keypair_list': Instance_Manage.views.keypair_list(request),
              'security_group_list': security_group_list(
                  request),
              'networks': Instance_Manage.views.network_list(request),
              'volume_list': Instance_Manage.views.volume_list(request)}
    time_zone_ins = datetime.now().utcnow()
    form = CreateImageAndLaunchForm(request, request.POST.copy(), **kwargs)

    try:
        ##check_can_custom_image
        license_custom = cache.get('CreeperQuotas').get('Is_CustomImage')
        ##check_image_max_num
        license_image_num = cache.get('CreeperQuotas').get('ImageMaxNum')

        ##check_can_custom_image
        license_instance_max_num = cache.get('CreeperQuotas').get('InstanceMaxNum')

        instances = api.nova.server_list(request, all_tenants=True)
        if len(instances) >= license_instance_max_num:
            raise glance_LicenseForbidden

        if license_custom == 0:
            raise glance_LicenseForbidden

        all_images, _more_images = api.image_list_detailed(request)
        image_list = []
        for im in all_images:
            if im.properties.has_key('image_type'):
                if im.properties['image_type'] != 'snapshot':
                    image_list.append(im)
            else:
                image_list.append(im)
        all_images = image_list
        if len(all_images) >= license_image_num:
            raise glance_LicenseForbidden
    except glance_LicenseForbidden:
        raise glance_LicenseForbidden
    except Exception, exc:
        LOG.error(exc)
        return  HttpResponse(
            {"message": get_text('Found no license.'),
             "statusCode": UI_RESPONSE_DWZ_ERROR},
            status=UI_RESPONSE_ERROR)

    if form.is_valid():
        status = UI_RESPONSE_DWZ_SUCCESS
        statusCode = UI_RESPONSE_DWZ_SUCCESS
        msg = "Start image Success"
        if not IMAGE_UTILS_INS.timezone:
            create_instance_thread_cls = CreateInstanceThread(request,
                                                              form.cleaned_data)
            IMAGE_UTILS_INS.timezone = time_zone_ins
            IMAGE_UTILS_INS.threadObj = create_instance_thread_cls
            create_instance_thread_cls.start()
        else:
            if IMAGE_UTILS_INS.timeLen > time_zone_ins - IMAGE_UTILS_INS.timezone:
                msg = "Have a Image is created,can not create image"
                status = UI_RESPONSE_ERROR
                statusCode = UI_RESPONSE_DWZ_ERROR
        try:
            if IMAGE_UTILS_INS.timeLen < time_zone_ins - IMAGE_UTILS_INS.timezone:
                create_instance_thread_cls = CreateInstanceThread(request,
                                                                  form.cleaned_data)
                IMAGE_UTILS_INS.threadObj = create_instance_thread_cls
                create_instance_thread_cls.start()

        except Exception, exc:
            LOG.error('error is %s.' % exc)
            status = UI_RESPONSE_ERROR
            statusCode = UI_RESPONSE_DWZ_ERROR
            if IMAGE_UTILS_INS.threadObj:
                IMAGE_UTILS_INS.threadObj = None
        object_name = form.cleaned_data['name'] + " " + get_text(
            "Create_at Instance Name") + form.cleaned_data['name_launch']
        return HttpResponse({"message": msg, 'object_name': object_name,
                             "statusCode": statusCode},
                            status=status)
    else:
        return  HttpResponse(
            {"form": form, "message": "", "statusCode": UI_RESPONSE_DWZ_ERROR},
            status=UI_RESPONSE_ERROR)


class CreateImageThread(threading.Thread):
    objs = {}
    objs_locker = threading.Lock()

    def __init__(self, request, data):
        threading.Thread.__init__(self)
        self.request = request
        self.data = data

    def __new__(cls, *args, **kwargs):
        if cls in cls.objs:
            return cls.objs[cls]['obj']

        cls.objs_locker.acquire()
        try:
            if cls in cls.objs:
                return cls.objs[cls]['obj']
            obj = object.__new__(cls)
            cls.objs[cls] = {'obj': obj}

            return cls.objs[cls]['obj']
        finally:
            cls.objs_locker.release()

    @classmethod
    def decorate_init(cls, fns):
        def init_wrap(*args):
            if not cls.objs[cls]['init']:
                fns(*args)
                cls.objs[cls]['init'] = True
            return

        return init_wrap

    def run(self):
        image_status_thread = None
        try:
            uuid = self.data['u_uid']
            image_status_thread = ImageStatus(uuid=uuid,
                                              status=UI_CREATE_PER_IMAGE_CREATING)
            image_status_thread.save()

            create_image_thread(self, image_status_thread)

            IMAGE_UTILS.threadObj = None
            IMAGE_UTILS.timezone = None
            return
        except Unauthorized:
            IMAGE_UTILS.threadObj = None
            IMAGE_UTILS.timezone = None
            raise
        except exceptions, exc:
            LOG.error(
                'Can not use the parameter or parameter format wrong !,%s !' % exc)
            try:
                image_status_thread.status = UI_CREATE_IMAGE_FAILED
                image_status_thread.save()
            except exceptions, ex:
                LOG.error('error is:%s' % ex)

            IMAGE_UTILS.threadObj = None
            IMAGE_UTILS.timezone = None

            return


@check_permission('Create Image')
@require_POST
@UIResponse('Image Manage', 'get_image_list')
def create_image(request):
    """
    :param request: request object
    :return view<'get_image_list OR image_template_manage/create.html'>: the corresponding view
    """
    form = CreateImageForm(request, request.POST.copy())
    time_zone = datetime.now().utcnow()

    try:
        ##check_can_custom_image
        license_custom = cache.get('CreeperQuotas').get('Is_CustomImage')
        ##check_image_max_num
        license_image_num = cache.get('CreeperQuotas').get('ImageMaxNum')

        if license_custom == 0:
            raise glance_LicenseForbidden

        all_images, _more_images = api.image_list_detailed(request)
        image_list = []
        for im in all_images:
            if im.properties.has_key('image_type'):
                if im.properties['image_type'] != 'snapshot':
                    image_list.append(im)
            else:
                image_list.append(im)
        all_images = image_list
        if len(all_images) >= license_image_num:
            raise glance_LicenseForbidden
    except glance_LicenseForbidden:
        raise glance_LicenseForbidden
    except Exception, exc:
        LOG.error(exc)
        return  HttpResponse(
            {"message": get_text('Found no license.'),
             "statusCode": UI_RESPONSE_DWZ_ERROR},
            status=UI_RESPONSE_ERROR)

    if form.is_valid():
        create_image_thr = CreateImageThread(request, form.cleaned_data)

        msg = "Start image Success"
        status = UI_RESPONSE_DWZ_SUCCESS
        statusCode = UI_RESPONSE_DWZ_SUCCESS
        if not IMAGE_UTILS.timezone:
            IMAGE_UTILS.timezone = time_zone
            IMAGE_UTILS.threadObj = create_image_thr
            create_image_thr.start()
        else:
            if IMAGE_UTILS.timeLen > time_zone - IMAGE_UTILS.timezone:
                msg = "can not create image"
                status = UI_RESPONSE_ERROR
                statusCode = UI_RESPONSE_DWZ_ERROR

        try:
            if IMAGE_UTILS.timeLen < time_zone - IMAGE_UTILS.timezone:
                create_image_thr = CreateImageThread(request, form.cleaned_data)
                IMAGE_UTILS.threadObj = create_image_thr
                create_image_thr.start()

        except Exception, exc:
            LOG.error('error is %s.' % exc)
            if IMAGE_UTILS.threadObj:
                IMAGE_UTILS.threadObj = None
                status = UI_RESPONSE_ERROR
                statusCode = UI_RESPONSE_DWZ_ERROR

        return HttpResponse(
            {"message": msg, "statusCode": statusCode,
             "object_name": form.cleaned_data['name']},
            status=status)
    else:
        return  HttpResponse(
            {"form": form, "message": get_text('Can not create image!'),
             "statusCode": UI_RESPONSE_DWZ_ERROR},
            status=UI_RESPONSE_ERROR)

DETECTING_STATUS_IMAGE_CREATING = '1'
DETECTING_STATUS_IMAGE_CREATED = '2'
DETECTING_STATUS_INSTANCE_CREATING = '3'
DETECTING_STATUS_INSTANCE_CREATED = '4'
DETECTING_STATUS_ALL_TO_FAILED = '5'
DETECTING_STATUS_NOT_FIND_IMAGE = '6'
DETECTING_STATUS_IMA_SUC_INS_FAIL = '7'
DETECTING_STATUS_IMAGE_TIMEOUT = '8'
DETECTING_STATUS_INSTANCE_TIMEOUT = '9'
DETECTING_STATUS_FAILED = '11'
DETECTING_INSTANCE_LIMIT = '13'
DETECTING_RESOURCE_NOT_ENOUGH = '14'
DETECTING_STATUS_FIRST_IF_NONE = 1
DETECTING_IMAGE_DISK_NOT_ENOUGH = '15'

def image_status_dict(request):
    DETECTING_STATUS = [('1', ["wait for Instance Creating", "Image Creating"]),
                        ('2', ["wait for Instance Creating", "Image Created"]),
                        ('3', ["Instance Task Sumbitting", "Image Created"]),
                        ('4', ["Instance Task Submitted", "Image Created"]),
                        ('5',
                         ["Instance Create Failed", "Image Created Failed"]),
                        ('6',
                         ["Instance Create Failed", "Can not find the image"]),
                        ('7',
                         ["Instance Create Failed", "Image Created"]),
                        ('8',
                         ["Instance Create Failed", "Image Create Timeout"]),
                        ('9',
                         ["Instance Create Timeout", "Image Created Failed"]),
                        ('11',
                         ["Instance Create Failed", "Image Created Failed"]),
                        ('13', ["Over the limit", "Image Create Success"]),
                        ('14', ["Instance resource is not enough",
                                "Image Created Failed"]),
                        ('15', ["Image created failed,Image disk is not enough",
                                "Image Created Failed"]),]
    return dict(DETECTING_STATUS)


@require_GET
def create_image_status(request, uuid):
    try:
        image_status_instance = ImageStatus.objects.get(uuid=uuid)
    except Exception, exc:
        LOG.error('error is %s.' % exc)
        image_status_instance = None

    if image_status_instance:
        status = image_status_instance.status
    else:
        status = DETECTING_STATUS_FAILED
    instance_id = ''

    status_dic = image_status_dict(request)
    if status in status_dic:
        instance_check_sum = status_dic[status][0]
        image_check_sum = status_dic[status][1]
        instance_id = image_status_instance.instance_id
    else:
        instance_check_sum = status_dic['11'][0]
        image_check_sum = status_dic['11'][1]
        status = '11'
    return HttpResponse(jsonutils.dumps(
        {"status": status, "image_checkSum": get_text(image_check_sum),
         "instance_checkSum": get_text(instance_check_sum),
         "instance_id": instance_id}))


@require_GET
def search_image_status(request, instance_id):
    """
     :param request: request object
     :return view<'image_template_manage/create.html'>: the view create image form
     """

    try:
        instance = api.server_get(request, instance_id)
        instance_id = getattr(instance, 'id', None)
        instance_name = getattr(instance, 'name', None)
        console = api.nova.server_spice_console(request, instance_id)

    except Unauthorized:
        raise
    except exceptions.NotFound, exc:
        msg = _('Can not retrieve spice url!')
        LOG.error('Can not retrieve spice url!error is %s.' % exc)
        return HttpResponse(jsonutils.dumps(ui_response(message=msg)))
    except Exception, exc:
        LOG.error('error is %s.' % exc)
        return HttpResponse(jsonutils.dumps(ui_response(message='error')))
    vnc_url = "%s&title=%s(%s)" % (console.url,
                                   instance_name,
                                   instance_id)
    return shortcuts.render(request,
                            'image_template_manage/create_and_instance.html',
                            {'vnc_url': vnc_url})


@require_GET
def instance_image_form(request, uuid):
    """
    :param request: request object
    :param uuid: the id of ImageStatus which will be detected
    :return: the status of instance
    """
    return shortcuts.render(request, 'image_template_manage/launch_status.html',
                            {'uuid': uuid})


@require_GET
def update_into_image_status(request, image_id):
    status = "saving"
    try:
        image = api.glance.image_get(request, image_id)
        status = image.status
    except Unauthorized:
        raise
    except Exception, exc:
        LOG.error('error is %s.' % exc)

    return HttpResponse(
        jsonutils.dumps({"status": status, "image_id": image_id}))


@require_GET
def detecting_image_form(request, uuid):
    """
    :param request: request object
    :param uuid: the id of ImageStatus
    :return: the id of ImageStatus
    """
    return shortcuts.render(request,
                            'image_template_manage/image_launch_status.html',
                            {'uuid': uuid})


@require_GET
def detecting_image_status(request, uuid):
    """
    :param request: request object
    :param uuid: the id of ImageStatus which will be detecting
    :return: the status of image
    """
    try:
        image_status_det = ImageStatus.objects.get(uuid=uuid)
    except Exception, exc:
        LOG.error('error is %s.' % exc)
        image_status_det = None

    if image_status_det:
        status = image_status_det.status
    else:
        status = DETECTING_STATUS_FAILED

    status_dic = image_status_dict(request)
    if status in status_dic:
        image_check_sum = status_dic[status][1]
    else:
        image_check_sum = status_dic['11'][1]
        status = '11'

    return HttpResponse(jsonutils.dumps(
        {"status": status, "image_checkSum": get_text(image_check_sum)}))


@require_GET
def get_network_list(request):
    """
    :param request: request object
    :return: the tenant's network
    """
    net_list = []
    if 'tenantId' in request.GET:
        tenant_id = request.GET['tenantId']
        if tenant_id:
            try:
                net_list = Instance_Manage.views.get_server_net(request,
                                                                tenant_id)
            except Exception, e:
                LOG.error(
                    'The method instance_get_network_list raise exception: '
                    '%s' % e)
                return HttpResponse({'message': 'Can not get net list'})
        return HttpResponse(jsonutils.dumps(net_list))
    else:
        return HttpResponse({'message': 'No tenant id find'})


@require_GET
def change_tenant_form(request):
    """
    :param request: request object
    :return dict: the tenant's security group list
    """
    group_list = ''
    if 'tenantId' in request.GET:
        tenant_id = request.GET['tenantId']
        if tenant_id != "" and tenant_id is not None:
            switch_tenants(request, tenant_id)
            group_list = security_group_list(request)
    return HttpResponse(jsonutils.dumps(group_list))


@require_GET
def search_flavor_status(request):
    """
        :param request: request object
        :return flavors list {flavor.id, flavor.disk}
    """
    try:
        flavors = api.flavor_list(request)
        flavor_list = []
        for flavor in flavors:
            flavor_list.append((flavor.id + "disk", flavor.disk))
            flavor_list.append((flavor.id + 'ram', flavor.ram))
    except Unauthorized:
        raise
    except Exception, exc:
        flavor_list = []
        LOG.error('Unable to retrieve instance flavors.%s' % exc)
    return sorted(flavor_list)


# for project delete, not need catch exception
def delete_project_images(request, tenant_id):
    filters = {"all_tenants": tenant_id}
    all_images, _more_images = api.image_list_detailed(request, filters=filters)

    for images in all_images:
        if images.owner == tenant_id:
            api.image_delete(request, images.id)


@require_GET
def img_fresh_progress(request):
    tenant_id = None
    if request.GET.has_key('img_tenant_id'):
        tenant_id = request.GET['img_tenant_id']

    try:
        if tenant_id is not None:
            switch_tenants(request, tenant_id)
    except Exception, exc:
        LOG.error('Error is :%s.' % exc)
        return HttpResponse(
            jsonutils.dumps({"status": '2'}))
    if tenant_id is None:
        return HttpResponse(
            jsonutils.dumps({"status": '2'}))
    return HttpResponse(
        jsonutils.dumps({"status": '1'}))
