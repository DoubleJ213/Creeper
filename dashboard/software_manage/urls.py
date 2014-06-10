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
__date__ = '2012-02-20'
__version__ = 'v2.0.1'

from django.conf import settings
if settings.DEBUG:
    __log__ = 'v2.0.1 create'

import logging
LOG = logging.getLogger(__name__)

#    code begin

from django.conf.urls.defaults import patterns
from dashboard.urls import url
# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()


urlpatterns = patterns('dashboard.software_manage.views',
    # get softwares
    url(r'^softwares/$', 'software_list', name='get_software_list', method='get'),
    # get softwares with flat
    url(r'^softwares/(?P<flat>all|windows|linux|mac)/$',
        'software_list', name='get_software_list_with_type', method='get'),

    # create software
    url(r'^softwares/new/$', 'create_software_form', name='create_software_form', method='get'),
    url(r'^softwares/$', 'create_software_action', name='create_software_action', method='post'),

    # delete software
    url(r'^softwares/(?P<software_uuid>[^/]+)/delete/$',
        'delete_software_form', name='delete_software_form', method='get'),
    url(r'^softwares/(?P<software_uuid>[^/]+)/$',
        'delete_software_action', name='delete_software_action', method='delete'),
    url(r'^softwares/$', 'delete_softwares', name='delete_softwares', method='delete'),

    # get binary packages of software
    url(r'^softwares/(?P<software_uuid>[^/]+)/download/$',
        'software_download', name='software_download', method='get'),

    # check software for downloading
    url(r'^softwares/(?P<software_uuid>[^/]+)/exist/$',
        'check_software_exist', name='check_software_exist', method='get'),

    # get software status
    url(r'^softwares/(?P<software_uuid>[^/]+)/status/$',
        'get_software_status', name='get_software_status', method='get'),

    # get collected softwares by user
    url(r'^softwares/collected/$',
        'get_collect_software', name='get_collect_software', method='get'),

    # add collected software
    url(r'^softwares/(?P<software_uuid>[^/]+)/collect/$',
        'collect_software_form', name='collect_software_form', method='get'),
    url(r'^softwares/(?P<software_uuid>[^/]+)/collect/$',
        'collect_software_action', name='collect_software_action', method='post'),

    # delete collected software, two page can delete
    url(r'^softwares/(?P<software_uuid>[^/]+)/delcollect/(?P<from_page>[^/]+)/$',
        'del_collect_software_form', name='del_collect_software_form', method='get'),
    url(r'^softwares/(?P<software_uuid>[^/]+)/delcollect/$',
        'del_collect_software_action', name='del_collect_software_action', method='delete'),
    url(r'^softwares/(?P<software_uuid>[^/]+)/delcollect2/$',
        'del_collect_software_action2', name='del_collect_software_action2', method='delete'),
)
