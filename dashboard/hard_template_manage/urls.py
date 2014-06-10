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
__version__ = 'v2.0.2'

import logging

from django.conf import settings
from django.conf.urls.defaults import patterns
from dashboard.urls import url

if settings.DEBUG:
    __log__ = 'v2.0.2 flavor list,get flavor detail,create flavor,update flavor'


LOG = logging.getLogger(__name__)

urlpatterns = patterns('dashboard.hard_template_manage.views',
    url(r'^flavor/$','get_flavor_list',name='get_flavor_list',method='get'),
    url(r'^flavor/(?P<flavor_id>[^/]+)/$','get_flavor_detail',name='get_flavor_detail',method='get'),

    url(r'^flavor/(?P<flavor_id>[^/]+)/form$','delete_flavor_form',name='delete_flavor_form',method='get'),
    url(r'^flavor/(?P<flavor_id>[^/]+)/$','delete_flavor',name='delete_flavor',method='delete'),


    url(r'^flavor/new$','create_flavor_form',name='create_flavor_form',method='get'),
    url(r'^flavor/$','create_flavor',name='create_flavor',method='post'),

)


