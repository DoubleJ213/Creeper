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
__date__ = '2012-02-21'
__version__ = 'v2.0.2'

from django.conf import settings

if settings.DEBUG:
    __log__ = """v2.0.1 create [2012-01-24]
     v2.0.2 add check if fold exist or not when create and delete binary package of software
    """

import logging
LOG = logging.getLogger(__name__)

#    code begin

import datetime
import hashlib
import os
import threading
import urllib

from django import shortcuts
from django.core.servers.basehttp import FileWrapper
from django.db.models import Q
from django.http import HttpResponse
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.core.cache import cache

from dashboard.exceptions import Unauthorized, LicenseForbidden
from dashboard.utils import jsonutils, UIResponse, Pagenation, ui_response, check_permission
from dashboard.utils.ui import (UI_RESPONSE_DWZ_ERROR,
                                UI_RESPONSE_DWZ_SUCCESS,
                                UI_RESPONSE_ERROR,
                                UI_RESPONSE_NOTFOUND)
from dashboard.software_manage import (SOFTWARE_STATE_UPLOADING,
                                       SOFTWARE_STATE_CREATING,
                                       SOFTWARE_STATE_FAILED,
                                       SOFTWARE_STATE_ACTIVE)
from dashboard.software_manage.forms import SoftwareForm
from dashboard.software_manage.models import Software, SoftwareCollect


@check_permission('View Software')
@require_GET
@Pagenation('software_manage/index.html')
def software_list(request, flat='all'):
    softwares = []
    try:
        if flat == 'all':
            softwares = Software.objects.all()
        else:
            softwares = Software.objects.filter(flat=flat)

        collects = SoftwareCollect.objects.filter(userid=request.user.id)

        for software in softwares:
            setattr(software, 'is_collect', False)
            for collect in collects:
                if software.uuid == collect.softwareuuid:
                    setattr(software, 'is_collect', True)
                    break
    except Exception, e:
        LOG.error('Can not get list of softwares. %s' % e)

    args = {}
    args['list'] = softwares

    return args


@check_permission('Software Upload')
@require_GET
def create_software_form(request):
    """
    :param request:
    :return:
    """
    softwares = []
    uploading_cnt = Software.objects.filter(Q(status=SOFTWARE_STATE_UPLOADING)
                                            | Q(status=SOFTWARE_STATE_CREATING)).count()
    if uploading_cnt >= settings.SOFTWARE_UPLOADING_MAX_NUM:
        return HttpResponse(jsonutils.dumps(
            ui_response(message="uploading count is beyond max limit.")))
    try:
        softwares_cnt = Software.objects.count()
        license_cnt = cache.get('CreeperQuotas').get('SoftwareMaxNum')
    except Exception, e:
        LOG.error('Can not get total of softwares. %s' % e)
    if softwares_cnt >= license_cnt:
        raise LicenseForbidden[4]("License Forbidden")
    form = SoftwareForm(request)
    created_at = datetime.datetime.utcnow()
    uuid = hashlib.md5(str(created_at)).hexdigest()
    return shortcuts.render(request,
                            'software_manage/create.html',
                            { 'form': form, 'uuid': uuid })


class UploadfileThread(threading.Thread):

    def __init__(self, software, file):
        threading.Thread.__init__(self)
        self.software = software
        self.file = file

    def run(self):
        try:
            old_file_names = self.software.content_name.split(".")
            if len(old_file_names) > 1:
                file_name = self.software.uuid + '.' + old_file_names[-1]
            else:
                file_name = self.software.uuid

            # for delete software when creating
            self.software.file_name = file_name
            self.software.save()
        except Exception, e:
            self.software.status = SOFTWARE_STATE_FAILED
            self.software.save()
            LOG.error("UploadfileThread faild. %s" % e)
            return

        try:
            if file_name and os.path.exists(settings.MEDIA_ROOT):
                filepath = os.path.join(settings.MEDIA_ROOT, file_name)

                destination = open(filepath, 'wb+')
                md5hash = hashlib.md5()
                for chunk in self.file.chunks():
                    destination.write(chunk)
                    md5hash.update(chunk)
                destination.close()

                # update active status
                self.software.status = SOFTWARE_STATE_ACTIVE
                self.software.check_sum = md5hash.hexdigest()
                self.software.save()
            else:
                self.software.status = SOFTWARE_STATE_FAILED
                self.software.save()
                LOG.error('Error: File not existed. File name: %s' % file_name)
        except Exception, e:
            # maybe software deleted
            LOG.error(e)

@check_permission('Software Upload')
@require_POST
@UIResponse('Software Manage', 'get_software_list')
def create_software_action(request):
    """
    Create Software :
        1. add software information in database
        2. create binary package of software in fold 'settings.MEDIA_ROOT'
    :param request:
    :return:
    """
    uuid = request.GET.get('software_uuid', '')
    if not uuid:
        return HttpResponse({"message": "Create software failed.",
                             "statusCode": UI_RESPONSE_DWZ_ERROR},
                            status=UI_RESPONSE_DWZ_ERROR)

    try:
        software = Software.objects.get(uuid=uuid)
    except Exception, e:
        LOG.error('Can not get software uuid=%s. %s' % (uuid, e))
        return HttpResponse({"message": "Create software failed.",
                             "statusCode": UI_RESPONSE_DWZ_ERROR},
                            status=UI_RESPONSE_DWZ_ERROR)

    try:
        software_form = SoftwareForm(request, *[request.POST, request.FILES])
    except Unauthorized:
        software.status = SOFTWARE_STATE_FAILED
        software.save()
        raise

    if software_form.is_valid():
        data = software_form.cleaned_data
        file = data['file']

        try:
            software.name = data['name']
            software.flat = data['flat']
            software.status = SOFTWARE_STATE_CREATING
            software.content_name = getattr(file, '_name', '')
            software.content_total = getattr(file, '_size', 0)
            software.classify = data['classify']
            software.save()

            UploadfileThread(software, file).start()
        except Exception, e:
            software.status = SOFTWARE_STATE_FAILED
            software.save()
            LOG.error("Create software failed. %s" % e)

        return HttpResponse({"message": "Create software Success",
                             "statusCode": UI_RESPONSE_DWZ_SUCCESS,
                             "object_name": data['name']},
                            status=UI_RESPONSE_DWZ_SUCCESS)
    else:
        software.status = SOFTWARE_STATE_FAILED
        software.save()
        return HttpResponse({"form": software_form,
                             "message": "",
                             "statusCode": UI_RESPONSE_DWZ_ERROR},
                            status=UI_RESPONSE_ERROR)


@check_permission('Download Software')
@require_GET
def software_download(request, software_uuid):
    """
    Get binary file of Software with uuid
    :param request:
    :param software_uuid:
    :return:
    """
    try:
        software = Software.objects.get(uuid=software_uuid)
    except Exception, e:
        LOG.error('Can not get software uuid=%s. %s' % (software_uuid, e))
        return HttpResponse(jsonutils.dumps(
            ui_response(message="this software not exited")))

    download_path = os.path.join(settings.MEDIA_ROOT, software.file_name)
    if os.path.isfile(download_path):
        wrapper = FileWrapper(file(download_path))
        response = HttpResponse(wrapper)
        response['Content-Length'] = os.path.getsize(download_path)
        response['Content-Type'] = 'application/octet-stream'
        response['Content-Encoding'] = 'utf-8'

        browser = request.META.get('HTTP_USER_AGENT', '')
        if browser.find("MSIE") != -1:
            filename = urllib.quote_plus(software.content_name.encode('utf-8'))
        else:
            filename = software.content_name.encode("utf-8")
        response['Content-Disposition'] = 'attachment; filename=%s' % filename

        return response
    else:
        return HttpResponse(jsonutils.dumps(
            ui_response(message='Binary file does not exist!')))


@check_permission('Delete Software')
@require_GET
def delete_software_form(request, software_uuid):
    return shortcuts.render(request,
                            'software_manage/delete.html',
                            {'software_uuid': software_uuid})


@require_http_methods(['DELETE'])
@UIResponse('Software Manage', 'get_software_list')
def delete_software_action(request, software_uuid):
    """
    :param request: request Object
    :param software_uuid: the uuid of software which will be deleted
    :return:
    """
    try:
        softwares = Software.objects.filter(uuid=software_uuid)
        software = softwares[0]
        softwares.delete()

        filepath = os.path.join(settings.MEDIA_ROOT, software.file_name)
        if software.file_name and os.path.exists(filepath):
            os.remove(filepath)

        SoftwareCollect.objects.filter(softwareuuid=software_uuid).delete()
    except Exception, e:
        LOG.error('Can not delete software uuid=%s. %s' % (software_uuid, e))
        return HttpResponse({"message": 'delete software failed',
                             "statusCode": UI_RESPONSE_DWZ_ERROR},
                            status=UI_RESPONSE_ERROR)

    return HttpResponse({"message": "delete software success",
                         "statusCode": UI_RESPONSE_DWZ_SUCCESS,
                         "object_name": software.name},
                        status=UI_RESPONSE_DWZ_SUCCESS)


@require_http_methods(['DELETE'])
@UIResponse('Software Manage', 'get_software_list')
def delete_softwares(request):
    try:
        software_ids = request.POST.getlist('software_check')
        for id in software_ids:
            software = Software.objects.get(uuid=id)
            software.delete()

            filepath = os.path.join(settings.MEDIA_ROOT, software.file_name)
            if software.file_name and os.path.exists(filepath):
                os.remove(filepath)

            SoftwareCollect.objects.filter(softwareuuid=id).delete()
    except Exception, e:
        LOG.error(e)
        return HttpResponse({"message": 'delete software failed',
                             "statusCode": UI_RESPONSE_DWZ_ERROR},
                            status=UI_RESPONSE_ERROR)

    return HttpResponse({"message": "delete software success",
                         "statusCode": UI_RESPONSE_DWZ_SUCCESS},
                        status=UI_RESPONSE_DWZ_SUCCESS)


@require_GET
def check_software_exist(request, software_uuid):
    try:
        software = Software.objects.get(uuid=software_uuid)
    except Exception, e:
        LOG.error('Can not get software uuid=%s. %s' % (software_uuid, e))
        return HttpResponse(jsonutils.dumps(
            ui_response(message="this software not exited")))

    download_path = os.path.join(settings.MEDIA_ROOT, software.file_name)
    if os.path.isfile(download_path):
        return HttpResponse(jsonutils.dumps(
            ui_response(status_code=UI_RESPONSE_DWZ_SUCCESS,
                        message="software exists")))
    else:
        return HttpResponse(jsonutils.dumps(
            ui_response(status_code=UI_RESPONSE_NOTFOUND,
                        message="this software not exited")))


def get_software_status(request, software_uuid):
    try:
        software = Software.objects.get(uuid=software_uuid)
    except Exception, e:
        LOG.error('Can not get software uuid=%s. %s' % (software_uuid, e))
        return HttpResponse(jsonutils.dumps(
            ui_response(message="this software not exited")))

    return HttpResponse(jsonutils.dumps({"id": software.uuid,
                                         "status": software.status,
                                         "checkSum": software.check_sum}))


@require_GET
def collect_software_form(request, software_uuid):
    return shortcuts.render(request,
                            'software_manage/collect.html',
                            {'software_uuid': software_uuid})


@require_POST
@UIResponse('Software Manage', 'get_software_list')
def collect_software_action(request, software_uuid):
    software_cnt = Software.objects.filter(uuid=software_uuid).count()
    if software_cnt == 0:
        return HttpResponse({"message": "this software not exited",
                             "statusCode": UI_RESPONSE_DWZ_ERROR},
                            status=UI_RESPONSE_DWZ_SUCCESS)

    collect = SoftwareCollect.objects.filter(userid=request.user.id,
                                            softwareuuid=software_uuid)
    if collect.count() > 0:
        return HttpResponse({"message": "this software had be collected",
                             "statusCode": UI_RESPONSE_DWZ_ERROR},
                            status=UI_RESPONSE_DWZ_SUCCESS)

    try:
        collect = SoftwareCollect(userid=request.user.id,
                                softwareuuid=software_uuid)
        collect.save()
    except Exception, e:
        LOG.error('Can not collect software uuid=%s. %s' % (software_uuid, e))
        msg = 'collect software failed'
        return HttpResponse({"message": msg,
                             "statusCode": UI_RESPONSE_DWZ_ERROR},
                            status=UI_RESPONSE_ERROR)

    return HttpResponse({"message": "collect software success",
                         "statusCode": UI_RESPONSE_DWZ_SUCCESS},
                        status=UI_RESPONSE_DWZ_SUCCESS)


@require_GET
@Pagenation('software_manage/collectsindex.html')
def get_collect_software(request):
    collects = SoftwareCollect.objects.filter(userid=request.user.id)
    collect_softwares = []
    try:
        for collect in collects:
            software = Software.objects.get(uuid=collect.softwareuuid)
            collect_softwares.append(software)
    except Exception, e:
        LOG.error('Can not get list of softwares. %s' % e)

    args = {}
    args['list'] = collect_softwares

    return args


@require_GET
def del_collect_software_form(request, software_uuid, from_page):
    if from_page == 'memberindex':
        page = 'software_manage/delcollect2.html'
    else:
        page = 'software_manage/delcollect.html'
    return shortcuts.render(request, page, {'software_uuid': software_uuid})


@require_http_methods(['DELETE'])
@UIResponse('Collect Softwares', 'get_collect_software')
def del_collect_software_action(request, software_uuid):
    try:
        SoftwareCollect.objects.get(userid=request.user.id,
                                    softwareuuid=software_uuid).delete()
    except Exception, e:
        LOG.error('Can not remove collect software uuid=%s. %s' % (software_uuid, e))
        msg = 'the software maybe removed'
        return HttpResponse({"message": msg,
                             "statusCode": UI_RESPONSE_DWZ_ERROR},
                            status=UI_RESPONSE_ERROR)

    return HttpResponse({"message": "remove collect software success",
                         "statusCode": UI_RESPONSE_DWZ_SUCCESS},
                        status=UI_RESPONSE_DWZ_SUCCESS)


# del collect from index.html
@require_http_methods(['DELETE'])
@UIResponse('Software Manage', 'get_software_list')
def del_collect_software_action2(request, software_uuid):
    try:
        SoftwareCollect.objects.get(userid=request.user.id,
                                    softwareuuid=software_uuid).delete()
    except Exception, e:
        LOG.error('Can not remove collect software uuid=%s. %s' % (software_uuid, e))
        msg = 'the software maybe removed'
        return HttpResponse({"message": msg,
                             "statusCode": UI_RESPONSE_DWZ_ERROR},
                            status=UI_RESPONSE_ERROR)

    return HttpResponse({"message": "remove collect software success",
                         "statusCode": UI_RESPONSE_DWZ_SUCCESS},
                        status=UI_RESPONSE_DWZ_SUCCESS)
