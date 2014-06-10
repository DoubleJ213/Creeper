# coding:utf8
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

import logging

from django import shortcuts
from django.http import HttpResponse
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from dashboard import api
from dashboard.exceptions import Unauthorized, LicenseForbidden
from dashboard.utils.i18n import get_text
from dashboard.utils import UIResponse, Pagenation
from dashboard.utils.ui import UI_RESPONSE_DWZ_ERROR, UI_RESPONSE_DWZ_SUCCESS,\
    UI_RESPONSE_ERROR, UI_RESPONSE_NOTFOUND, check_permission

from dashboard.hard_template_manage.forms import CreateFlavorForm

LOG = logging.getLogger(__name__)

@check_permission('Add Flavor')
@require_GET
def create_flavor_form(request):
    """
    :param request: request object
    :return view<'hard_template_manage/create.html'>: form table of creating flavor
    """
    form = CreateFlavorForm(request)
    return shortcuts.render(request,'hard_template_manage/create.html',{'form':form})


@require_POST
@UIResponse('HardTemplate Manage', 'get_flavor_list')
def create_flavor(request):
    """
    :param request: request object
    :return view<'hard_template_manage/create.html OR get_flavor_list'>: the responding view
    """
    form = CreateFlavorForm(request, request.POST)
    if form.is_valid():
        data = form.cleaned_data
        try:
            api.flavor_create(request,
                data['name'],
                data['memory_mb'],
                data['vcpus'],
                data['disk_gb'],
                ephemeral=data['eph_gb'])
            return HttpResponse({"message":"Create flavor Success",
                                 "statusCode":UI_RESPONSE_DWZ_SUCCESS,
                                 "object_name":data['name']},
                                status=UI_RESPONSE_DWZ_SUCCESS)
        except (Unauthorized, LicenseForbidden):
            raise
        except Exception,e:
            msg = 'Can not create flavor!'
            LOG.error('Can not create flavor,%s' % e)
            return HttpResponse({ "message":msg,
                                  "statusCode":UI_RESPONSE_DWZ_ERROR},
                                    status=UI_RESPONSE_ERROR)
    else:
        return HttpResponse({"form":form,"message":"",
                             "statusCode":UI_RESPONSE_DWZ_ERROR},
                            status=UI_RESPONSE_ERROR)

@check_permission('View Flavor')
@require_GET
@Pagenation('hard_template_manage/index.html')
def get_flavor_list(request):
    """
    :param request: require object
    :return view<'hard_template_manage/index.html'>: the flavor list view
    """
    args = {}
    flavors = []
    try:
        flavors = api.nova.flavor_list(request)
    except Unauthorized:
        raise
    except Exception, e:
        LOG.error('The method get_flavor_list raise exception: %s' % e)

#    flavors.sort(key=lambda f: (f.vcpus, f.ram, f.disk))
    args['list'] = flavors
    return args


@require_GET
def get_flavor_detail(request, flavor_id):
    """
    :param request: request object
    :param flavor_id: the flavor id
    :return view<'hard_template_manage/detail.html OR get_flavor_list'>: the corresponding view
    """
    try:
        flavor = api.flavor_get(request, flavor_id)
        return shortcuts.render(request,'hard_template_manage/detail.html',
                                {'flavor':flavor})
    except Unauthorized:
        raise
    except Exception,e:
        LOG.error('The method get_flavor detail raise exception: %s' % e)
        return shortcuts.redirect('get_flavor_list')

@check_permission('Delete Falvor')
@require_GET
def delete_flavor_form(request, flavor_id):
    return shortcuts.render(request, 'hard_template_manage/delete.html',
                            {'flavor_id':flavor_id})




@require_http_methods(['DELETE'])
@UIResponse('HardTemplate Manage', 'get_flavor_list')
def delete_flavor(request,flavor_id):
    """
    :param request: request object
    :param flavor_id: the flavor id which will be deleted
    :return view<'get_flavor_list'>: view of flavor list
    """
    oldflavor = None
    try:
        flavors = api.flavor_list(request)
        for flav in flavors:
            if flav.id == flavor_id:
                oldflavor = flav
                break
    except Unauthorized:
        raise
    except Exception,e:
        LOG.debug(e)

    try:
        api.flavor_delete(request, flavor_id)
    except Unauthorized:
        raise
    except Exception, e:
        #Fix bug 88
        if e.code == UI_RESPONSE_NOTFOUND:
            msg = "The resource could not be found."
        else:
            msg = "Can not delete flavor!"
        LOG.error('Can not delete flavor,%s' % e)
        return HttpResponse({ "message":get_text(msg),
                              "statusCode":UI_RESPONSE_DWZ_ERROR},
                                status=UI_RESPONSE_DWZ_ERROR)

    return HttpResponse({"message":"delete flavor success",
                         "statusCode":UI_RESPONSE_DWZ_SUCCESS,
                         "object_name":oldflavor.name},
                        status=UI_RESPONSE_DWZ_SUCCESS)



def search_flavor_status(request):
    """
    :param request: request object
    :return flavors list {flavor.id, flavor.disk}
    """
    try:
        flavors = api.flavor_list(request)
        flavor_list = [(flavor.id, {"fla_disk": flavor.disk, "fla_ram": flavor.ram})
                       for flavor in flavors]
    except Unauthorized:
        raise
    except Exception, e:
        flavor_list = []
        LOG.error('Unable to retrieve instance flavors.%s' % e)
    return sorted(flavor_list)



