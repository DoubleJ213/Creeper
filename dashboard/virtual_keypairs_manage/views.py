# Copyright 2013 Beixinyuan(Nanjing), All Rights Reserved.
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


__author__ = 'zhaolei'
__date__ = '2013-06-20'
__version__ = 'v2.0.9'

from django.conf import settings

if settings.DEBUG:
    __log__ = 'v2.0.9 create'

import logging
LOG = logging.getLogger(__name__)

#    code begin

import re
from django import shortcuts
from django.views.decorators.http import require_GET , require_POST, require_http_methods
from django.http import HttpResponse
from django.template.defaultfilters import slugify
from dashboard import api
from dashboard.exceptions import Unauthorized
from dashboard.utils import UIResponse , Pagenation
from dashboard.utils.ui import *
from .forms import CreateKeypair, ImportKeypair

NUMBERS_PER_PAGE = 10

NEW_LINES = re.compile(r"\r|\n")

@require_GET
@Pagenation('virtual_keypairs_manage/keypair_list.html')
def get_project_keypairs_list(request):
    """
    :param request:request object
    :return:view<'virtual_keypairs_manage/keypair_list.html'>::list of keypairs
    """
    args = {}
    keypairlist = []
    try:
        keypairlist = api.nova.keypair_list(request)
    except Unauthorized:
        raise
    except Exception , exe:
        LOG.error('Unable to retrieve keypair list.Error:%s' % exe.message)

    args['list'] = []
    args['keypairlist'] = keypairlist
    return args

@require_GET
def create_keypair_index(request):
    """
    :param request:request object
    :return:view<'virtual_keypairs_manage/keypair_list.html'>::index for create keypair
    """
    form = CreateKeypair()
    return shortcuts.render(request, 'virtual_keypairs_manage/keypair_create.html', {'form': form})

@require_POST
@UIResponse('Virtual Keypairs Manage', 'download_keypair_index')
def create_keypair_action(request):
    """
    :param request:request object
    :return:view<'virtual_keypairs_manage/keypair_download.html'>::get keypair name and forword to keypair_download.html
    """
    args = []
    form = CreateKeypair(request.POST)
    if form.is_valid():
        data = form.cleaned_data
    args.append(data['name'])
    return HttpResponse({"message":"create keypair successfully!", "statusCode":UI_RESPONSE_DWZ_SUCCESS , "args":args}, status = UI_RESPONSE_DWZ_SUCCESS)


@require_GET
def download_keypair_index(request, keypair_name):
    """
    :param request:request object,keypair_name
    :return:view<'virtual_keypairs_manage/keypair_download.html'>::index for download keypair
    """
    return shortcuts.render(request, 'virtual_keypairs_manage/keypair_download.html', {'keypair_name': keypair_name})

@require_GET
def create_keypair_download(request, keypair_name):
    """
    :param request:request object,keypair_name
    :return:view<'virtual_keypairs_manage/keypair_download.html'>::create a keypair and download
    """
    try:
        keypair = api.nova.keypair_create(request, keypair_name)
    except Unauthorized:
        raise
    except Exception, exe:
        LOG.error('return download keypair error,%s.' % exe)
        return HttpResponse({"message":"download keypair error", "statusCode":UI_RESPONSE_DWZ_ERROR}, status = UI_RESPONSE_ERROR)
    response = HttpResponse(mimetype= 'application/binary')
    response['Content-Disposition'] = \
    'attachment; filename=%s.pem' % slugify(keypair.name)
    response.write(keypair.private_key)
    response['Content-Length'] = str(len(response.content))
    return response

@require_GET
def import_keypair_index(request):
    """
    :param request:request object
    :return:view<'virtual_keypairs_manage/keypair_import.html'>::index for import keypair
    """
    form = ImportKeypair()
    return shortcuts.render(request, 'virtual_keypairs_manage/keypair_import.html', {'form': form})


@require_POST
@UIResponse('Virtual Keypairs Manage', 'get_project_keypairs_list')
def import_keypair_action(request):
    """
    :param request:request object
    :return:view<'virtual_keypairs_manage/keypair_list.html'>::action for import keypair
    """
    form =  ImportKeypair(request.POST)
    if form.is_valid():
        data = form.cleaned_data
        try:
            data['public_key'] = NEW_LINES.sub("", data['public_key'])
            api.nova.keypair_import(request,
                                                data['name'],
                                                data['public_key'])
        except Unauthorized:
            raise
        except Exception , exe:
            msg = 'Failed to import keypair'
            LOG.error("Failed to import keypair,the error is %s" % exe.message)
            return HttpResponse({"message":msg, "statusCode":UI_RESPONSE_DWZ_ERROR}, status = UI_RESPONSE_ERROR)
        LOG.info('import keypair successfully!')
        return HttpResponse({"message":"import keypair successfully!", "statusCode":UI_RESPONSE_DWZ_SUCCESS , "object_name":data['name']}, status = UI_RESPONSE_DWZ_SUCCESS)
    else:
        return HttpResponse({"form":form, "message":"", "statusCode":UI_RESPONSE_DWZ_ERROR}, status = UI_RESPONSE_ERROR)

@require_GET
def delete_keypair_form(request, keypair_name):
    """
    :param request:request object, keypair_name
    :return:view<'virtual_keypairs_manage/keypair_import.html'>::index for delete keypair
    """
    return shortcuts.render(request, 'virtual_keypairs_manage/keypair_delete.html', {'keypair_name': keypair_name})


@require_http_methods(['DELETE'])
@UIResponse('Virtual Keypairs Manage', 'get_project_keypairs_list')
def delete_keypair_action(request, keypair_name):
    """
    :param request:request object, keypair_name
    :return:view<'virtual_keypairs_manage/keypair_list.html'>::action for delete keypair
    """
    try:
        api.nova.keypair_delete(request, keypair_name)
    except Unauthorized:
        raise
    except Exception, exe:
        LOG.error('Can not delete keypair,error is %s' % exe.message )
        msg = 'Can not delete keypair %s' % keypair_name
        return HttpResponse({"message":msg, "statusCode":UI_RESPONSE_DWZ_ERROR}, status= UI_RESPONSE_ERROR)

    return HttpResponse({"message":"delete keypair success", "statusCode":UI_RESPONSE_DWZ_SUCCESS,
                         "object_name":keypair_name}, status= UI_RESPONSE_OK)