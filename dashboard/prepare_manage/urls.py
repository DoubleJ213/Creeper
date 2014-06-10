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
__date__ = '2013-02-21'
__version__ = 'v2.0.2'

from django.conf import settings

if settings.DEBUG:
    __log__ = """
            v2.0.1 create [2013-02-04]
            v2.0.2[add]: create image [2013-02-21]
            """

import logging

LOG = logging.getLogger(__name__)
#    code begin

from django.conf.urls.defaults import patterns
from dashboard.urls import url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admind
# admin.autodiscover()

urlpatterns = patterns('dashboard.prepare_manage.views',
                       url(r'^prepares$',
                           'prepare_list',
                           name='prepare_list', method='get'),
                       url(r'^prepare/list/$',
                           'get_prepare_list',
                           name='get_prepare_list', method='get'),
                       url(r'^prepare/project/need_from/(?P<need_uuid>[^/]+)/$',
                           'create_project_need_form',
                           name='create_project_need_form', method='get'),
                       url(r'^prepare/project/tenant/(?P<need_uuid>[^/]+)/$',
                           'create_project_tenant',
                           name='create_project_tenant', method='post'),
                       url(
                           r'^prepare/network/create_network/(?P<network_obj_id>[^/]+)/',
                           'create_network_index_in_prepare',
                           name='create_network_index_prepare',
                           method='get'),
                       url(
                           r'^prepare/network/(?P<tenant_id>[^/]+)/create_network_ajax/(?P<network_obj_id>[^/]+)/$',
                           'create_network_action_ajax',
                           name='create_network_action_ajax',
                           method='post'),
                       url(r'^prepare/create_sub_net/(?P<network_id>[^/]+)/(?P<network_obj_id>[^/]+)/',
                           'create_sub_net_index', name='create_sub_net_index',
                           method='get'),
                       url(
                           r'^network/(?P<network_id>[^/]+)/create_sub_net_action/(?P<network_obj_id>[^/]+)',
                           'create_sub_net_action',
                           name='create_sub_net_action',
                           method='post'),
                       url(
                           r'^prepare/(?P<tenant_id>[^/]+)/(?P<network_id>[^/]+)/network_info_list/(?P<network_obj_id>[^/]+)/$',
                           'get_network_info_list',
                           name='get_network_info_list', method='get'),
                       url(
                           r'^prepare/router_detail_index/(?P<virtual_router_obj_id>[^/]+)/$',
                           'create_router_detail_index',
                           name='create_router_detail_index',
                           method='get'),
                       url(r'^prepare/(?P<tenant_id>[^/]+)/router_action_ajax/(?P<virtual_router_obj_id>[^/]+)$', 'create_router_action_ajax',
                           name='create_router_action_ajax',
                           method='post'),
                       url(r'^prepare/(?P<tenant_id>[^/]+)/projects/(?P<router_id>[^/]+)/(?P<virtual_router_obj_id>[^/]+)/$', 'routers_projects_list',
                           name='routers_projects_list',
                           method='get'),
                       url(r'^prepare/(?P<tenant_id>[^/]+)/(?P<router_project_id>[^/]+)/router_project_detail/(?P<virtual_router_obj_id>[^/]+)/$',
                           'create_router_project_index', name='create_router_project_index', method='get'),
                       url(r'^prepare/(?P<tenant_id>[^/]+)/(?P<router_project_id>[^/]+)/router_project_info/(?P<router_topology>[^/]+)/(?P<virtual_router_obj_id>[^/]+)/$',
                           'get_router_project_info_list',
                           name='get_router_project_info_list', method='get'),
                       url(r'^prepare/(?P<router_id>[^/]+)/interface_action/(?P<virtual_router_obj_id>[^/]+)', 'create_interface_action_index',
                           name='create_interface_action_index', method='post'),
                       url(r'^prepare/(?P<router_id>[^/]+)/gateway_detail/(?P<virtual_router_obj_id>[^/]+)/$', 'create_gateway_detail_index',
                           name='create_gateway_detail_index',
                           method='get'),
                       url(r'^prepare/(?P<router_id>[^/]+)/gateway_action/$', 'create_gateway_action_ajax',
                           name='create_gateway_action_ajax',
                           method='post'),

                       url(r'^prepare/logs/(?P<log_id>[^/]+)/page/$', 'log_large_page', name='log_large_page', method='get'),

                       url(r'^prepare/query/(?P<log_id>[^/]+)/$', 'log_query_prepare_index', name='log_query_prepare_index', method='get'),

                       url(r'^prepare/export/list/(?P<log_id>[^/]+)/$', 'prepare_export_logs', name='prepare_export_logs', method='get'),

                       url(r'^prepare/logs/count$', 'logs_count_in_prepare', name='logs_count_in_prepare', method='get'),

                       url(r'^prepare/query/log/delete/(?P<log_id>[^/]+)/$', 'delete_logs_query_in_prepare', name='delete_logs_query_in_prepare', method='post'),

                       url(r'^prepare/(?P<uuid>[^/]+)/$', 'delete_log_in_prepare', name='delete_log_in_prepare', method='get'),

                       url(r'^prepare/(?P<uuid>[^/]+)/form$', 'delete_log_form_in_prepare', name='delete_log_form_in_prepare', method='get'),

                       url(r'^prepare/log/detail/(?P<uuid>[^/]+)/$', 'get_log_detail_in_prepare', name='get_log_detail_in_prepare', method='get'),

                       url(r'^prepare/log/export/(?P<log_id>[^/]+)/$', 'log_export_form_in_prepare', name='log_export_form_in_prepare', method='get'),

                       url(r'^prepare/images/init/(?P<img_obj_id>[^/]+)/$', 'image_init_page', name='image_init_page', method='get'),

                       url(r'^prepare/image/form/(?P<img_obj_id>[^/]+)/page_url/(?P<page_id>[^/]+)$', 'create_image_form_page', name='create_image_form_page', method='get'),

                       url(r'^prepare/image/index/(?P<img_obj_id>[^/]+)$', 'create_image_index', name='create_image_index', method='post'),

                       url(r'^image_manage/(?P<img_obj_id>[^/]+)/instance$', 'create_instance_index', name='create_instance_index', method='post'),

                       url(r'^prepare/image/(?P<image_id>[^/]+)/page/(?P<img_obj_id>[^/]+)/$', 'create_image_page_suc', name='create_image_page_suc', method='get'),

                       url(r'^prepare/project_manage/quotas/edit/(?P<tenant_obj_id>[^/]+)$',
                           'update_project_quotas_form_index', name='update_project_quotas_form_index', method='get'),

                       url(r'^prepare/project_manage/(?P<tenant_id>[^/]+)/quotas/(?P<tenant_obj_id>[^/]+)$',
                           'update_project_quotas_action_index', name='update_project_quotas_action_index', method='post'),

                       url(r'^prepare/project_manage/update_success/$',
                           'update_project_quotas_suc', name='update_project_quotas_suc', method='get'),

                       url(r'^prepare/soft_wares/(?P<sw_obj_id>[^/]+)/$',
                           'soft_wares_upload_success', name='soft_wares_upload_success', method='get'),

                       url(r'^prepare/volume_manage/(?P<prepare_volume_id>[^/]+)/(?P<page_id>[^/]+)/$',
                           'volume_quotas_init_page', name='volume_quotas_init_page', method='get'),

                       url(r'^prepare/volume_manage/(?P<prepare_volume_id>[^/]+)/$',
                           'volume_quotas_tab_init', name='volume_quotas_tab_init', method='get'),

                       url(r'^prepare/volume_manage/(?P<tenant_id>[^/]+)/quotas/(?P<prepare_volume_id>[^/]+)$',
                           'volume_quotas_update_action', name='volume_quotas_update_action', method='post'),

                       url(r'^prepare/volume_manage/(?P<prepare_volume_id>[^/]+)$',
                           'create_node_in_volume', name='create_node_in_volume', method='get'),

                       url(r'^prepare/volume_manage/(?P<prepare_volume_id>[^/]+)/$',
                           'create_node_form_action', name='create_node_form_action', method='post'),

                        url(r'^prepare/instance_manage/$', 'launch_instance_index', name='launch_instance_index', method='post'),
                        url(r'^prepare/instances_manage/new/(?P<image_id>[^/]+)/(?P<img_obj_id>[^/]+)/(?P<page_id>[^/]+)/$',
                            'launch_form_image_index', name='launch_form_image_index', method='get'),

                        url(r'^prepare/instance_manage/(?P<img_obj_id>[^/]+)/$', 'create_instance_action', name='create_instance_action', method='post'),

                        url(r'^prepare/service_resource/(?P<resource_id>[^/]+)/$', 'get_service_resource_info', name='get_service_resource_info', method='get'),

                        url(r'^host/instance/$', 'get_instance_and_host', name='get_instance_and_host', method='get'),

                        url(r'^host/instance/status$', 'get_instance_status', name='get_instance_status', method='get'),

                        url(r'^host/migrate/(?P<resource_id>[^/]+)$', 'handle_instance_migrate', name='handle_instance_migrate', method='post'),

                        url(r'^host/migrate/success$', 'instance_migrate_suc', name='instance_migrate_suc', method='get'),

                        url(r'^file/download$', 'software_download_in_prepare', name='software_download_in_prepare', method='get'),

                        url(r'^instance/instances_manage/new/(?P<img_obj_id>[^/]+)/$',
                            'start_image_launch_instance', name='start_image_launch_instance', method='get'),

                        url(r'^instance/image/flavor$', 'create_image_disk_and_ram', name='create_image_disk_and_ram', method='get'),

                        url(r'^list/info$', 'prepare_list_info', name='prepare_list_info', method='get'),


#                        url(r'^check/list/$',
#                            'get_check_list',
#                            name='get_check_list', method='get'),

#                        url(r'^tasks/(?P<task_id>[^/]+)/(?P<type>reject|edit|delete|resume)/$',
#                            'task_action', name='task_action', method='get'),

                        url(r'^tasks/(?P<task_id>[^/]+)/delete$',
                            'delete_task',
                            name='delete_task', method='post'),

#                        url(r'^tasks/resume$',
#                            'resume_task',
#                            name='resume_task', method='post'),


)

