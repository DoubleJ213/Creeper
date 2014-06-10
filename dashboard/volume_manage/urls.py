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
__date__ = '2012-02-20'
__version__ = 'v2.0.2'

import logging

from django.conf import settings
from django.conf.urls.defaults import patterns

from dashboard.urls import url

if settings.DEBUG:
    __log__ = 'v2.0.1 volume list;volume detail;create volume;once time delete more volumes'

LOG = logging.getLogger(__name__)
#    code begin


# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('dashboard.volume_manage.views',
    # get all the volumes
    url(r'^volumes/$', 'get_volume_list', name='get_volume_list', method='get'),
    # create volume
    url(r'^volumes/volume/page/$', 'create_volume_action',
        name='create_volume_action', method='post'),
    # delete one or more volumes
    url(r'^volumes/delete_volumes/$', 'delete_volumes', name='delete_volumes',
        method='delete'),

    # get the volume's detail information
    url(r'^volumes/volume/(?P<volume_id>[^/]+)/detail$', 'volume_detail',
        name='get_volume_detail', method='get'),
    # show the create form table
    url(r'^volumes/tenants/(?P<tenant_id>[^/]+)/volume/(?P<snapshot_id>[^/]+)/page/$',
        'create_volume_form', name='create_volume_form',
        method='get'),

#    # delete one  volume
#    url(r'^volumes/volume/(?P<volume_id>[^/]+)/delete/$',
#        'delete_single_volume_form',
#        name='delete_single_volume_form',
#        method='get'),

    url(r'^volumes/volume/forward/$', 'delete_single_volume',
        name='delete_single_volume', method='delete'),
    # attach volume to instance
    url(r'^volumes/tenants/(?P<tenant_id>[^/]+)/attach/(?P<volume_id>[^/]+)/$',
        'attach_volume_form', name='attach_volume_form',
        method='get'),
    url(r'^volumes/(?P<volume_id>[^/]+)/attached/$', 'handle_attach_volume',
        name='handle_attach_volume',
        method='post'),
    # detach volume from instance
    url(r'^volumes/(?P<volume_id>[^/]+)/instances/(?P<instance_id>[^/]+)/detach/$',
        'detach_volume', name='detach_volume',
        method='get'),
    url(r'^volumes/(?P<volume_id>[^/]+)/instances/(?P<instance_id>[^/]+)/detached/$',
        'handle_detach_volume',
        name='handle_detach_volume', method='post'),
#    # delete one or more volumes
#    url(r'^volumes/$', 'delete_volumes', name='delete_volumes',
#        method='delete'),
    #    url(r'^volumes/(?P<volume_id>[/+])/update_volume/$','update_volume',name='update_volume',method='post'),
    url(r'^volumes/(?P<volume_id>[^/]+)/status/$', 'volume_status',
        name='get_volume_status', method='get'),
    url(r'^volumes/instance/info/$', 'get_instance_name',
        name='get_instance_name', method='get'),
    url(r'^volumes/volume/types/page/$', 'get_volume_type_list',
        name='get_volume_type_list', method='get'),
    url(r'^volumes/volume/types/$', 'create_volume_type_form',
        name='create_volume_type_form', method='get'),
    url(r'^volumes/volume/types/$', 'create_volume_type_action',
        name='create_volume_type_action', method='post'),
    url(r'^volumes/volume/types/$', 'volume_type_delete_action',
        name='volume_type_delete_action', method='delete'),
    url(r'^volumes/volume/progress_bar/$', 'fresh_progress_bar',
        name='fresh_progress_bar', method='get'),
    url(r'^volumes/tenants/(?P<tenant_id>[^/]+)/(?P<volume_id>[^/]+)/snapshot/$',
        'create_volume_snapshot_form',
        name='create_volume_snapshot_form', method='get'),
    url(r'^volumes/volume/snapshot/$', 'create_volume_snapshot',
        name='create_volume_snapshot', method='post'),
    url(r'^volumes/volume/snapshots/$', 'get_snapshot_index',
        name='get_snapshot_index', method='get'),
    url(r'^volumes/volume/snapshots/$', 'snapshots_delete',
        name='snapshots_delete', method='delete'),
    url(r'^volumes/volume/(?P<snapshot_id>[^/]+)/snapshot/$', 'snapshot_delete',
        name='snapshot_delete',
        method='delete'),
    url(r'^volumes/volume/(?P<snapshot_id>[^/]+)/status/$',
        'get_snapshot_status', name='get_snapshot_status',
        method='get'),
    url(r'^volumes/volume/(?P<snapshot_id>[^/]+)/detail/$',
        'get_snapshot_detail', name='get_snapshot_detail',
        method='get'),
    #    get_volume_list_temp
    url(r'^volumes/temp/$',
        'get_volume_list_temp', name='get_volume_list_temp',
        method='get'),
)



