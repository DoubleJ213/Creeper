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
URL mapping for django
"""

__author__ = 'xulei'
__date__ = '2013-04-07'
__version__ = 'v2.0.6'

import logging

from django.conf import settings
from django.conf.urls.defaults import patterns
from dashboard.urls import url

if settings.DEBUG:
    __log__ = 'v2.0.6 thresholds manage'

LOG = logging.getLogger(__name__)

urlpatterns = patterns('dashboard.thresholds_manage.views',
                       url(r'^thresholds/$', 'get_thresholds_list',
                           name='get_thresholds_list', method='get'),
                       # forward html
                       url(r'^forward/update_form/$',
                           'update_form', name='update_form', method='get'),
                       # ajax
                       url(r'^threshold/os-strategy/$',
                           'update_thresholds', name='update_thresholds',
                           method='post'),
)