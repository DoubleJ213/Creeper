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
__author__ = 'xulei'
__date__ = '2013-04-07'
__version__ = 'v2.0.6'

import logging

from django import shortcuts
from django.conf import settings
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_GET, require_POST

from dashboard.api import monitor
from dashboard.utils import UIResponse, Pagenation, UI_RESPONSE_ERROR,\
    UI_RESPONSE_DWZ_ERROR, UI_RESPONSE_DWZ_SUCCESS

if settings.DEBUG:
    __log__ = 'v2.0.6 Views for thresholds operations'

LOG = logging.getLogger(__name__)


@require_GET
@Pagenation('thresholds_manage/index.html')
def get_thresholds_list(request):
    """
    List all of the thresholds without deleted.
    See @Pagenation for more information of pagenation
    :param request:
    :return: dict
    """
    args = dict()

    client = monitor.VoyageClient()
    try:
        strategies = client.get_all_os_strategy(request.user.tenant_id,
                                                request.user.token.id)
    except Exception, e:
        LOG.error('Failed to get os-strategy, reason: %s' % (e))
        raise Exception(_('Failed to get strategy, '
                          'please make sure the voyage server is running.'))
    else:
        thresholds = strategies['strategies']
        args['list'] = thresholds
        args['numPerPage'] = 50
    return args


@require_GET
def update_form(request):
    """
    Forward request to update.html for updating an existing threshold.
    :param request:
    :param thresholds_id:
    :return:
    """
    client = monitor.VoyageClient()
    try:
        strategies = client.get_all_os_strategy(request.user.tenant_id,
                                                request.user.token.id)
    except Exception, e:
        LOG.error('Failed to get os-strategy, reason: %s' % (e))
        msg = _('Failed to get strategy, '
                'please make sure the voyage server is running.')
        return HttpResponse(status=UI_RESPONSE_ERROR, content=msg)
    else:
        thresholds = strategies['strategies']
        ui_data = {}
        enable_data = None
        for data in thresholds:
            if data['strategy_name'] not in ui_data and data['enable'] == 0:
                ui_data[data['strategy_name']] = data['strategy_id']
            if not enable_data and data['enable'] == 1:
                enable_data = data['strategy_name']

    return shortcuts.render(request, 'thresholds_manage/update.html',
                            {'ui_data': ui_data, 'enable_data': enable_data})


@require_POST
@UIResponse('Thresholds Manage', 'get_thresholds_list')
def update_thresholds(request):
    """
    Modify an existing threshold.
    :param request:
    :param thresholds_id:
    :return:
    """
    post = request.POST.copy()
    new_strategy = post.get('new_strategy', None)
    if not new_strategy:
        msg = 'Invalid request data.'
        LOG.error(msg)
        return HttpResponse({"message": msg,
                             "statusCode": UI_RESPONSE_DWZ_ERROR},
                            status=UI_RESPONSE_ERROR)
    else:
        client = monitor.VoyageClient()
        try:
            strategies = client.get_all_os_strategy(request.user.tenant_id,
                                                    request.user.token.id)[
                         'strategies']
        except Exception, e:
            LOG.error('Failed to get os-strategy, reason: %s' % (e))
            msg = 'Failed to get strategy, '\
                  'please make sure the voyage server is running.'
            return HttpResponse({"message": msg,
                                 "statusCode": UI_RESPONSE_DWZ_ERROR},
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
                msg = 'Invalid request data.'
                LOG.error(msg)
                return HttpResponse({"message": msg,
                                     "statusCode": UI_RESPONSE_DWZ_ERROR},
                                    status=UI_RESPONSE_ERROR)
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
            return HttpResponse(
                {"message": "Fail to update stragety.",
                 "statusCode": UI_RESPONSE_DWZ_ERROR},
                status=UI_RESPONSE_ERROR)
        else:
            LOG.debug('Update threshold successfully.')
            return HttpResponse(
                {"message": "Update threshold successfully.",
                 "statusCode": UI_RESPONSE_DWZ_SUCCESS},
                status=UI_RESPONSE_ERROR)