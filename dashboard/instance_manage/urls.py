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

#    code begin
from django.conf import settings
from django.conf.urls.defaults import patterns
from dashboard.urls import url

if settings.DEBUG:
    __log__ = 'v2.0.1 instance_mange,get instance list,get snapshots list,create image template quickly'

LOG = logging.getLogger(__name__)

urlpatterns = patterns('dashboard.instance_manage.views',
    url(r'^instances/$', 'instance_list',  name='get_instance_list', method='get'),
    url(r'^instances/(?P<instance_id>[^/]+)/projects/(?P<tenant_id>[^/]+)/$', 'instance_detail',
        name='get_instance_detail', method='get'),
    #url(r'^instances/(?P<instance_id>[^/]+)/action$',
    #    'get_instance_action_form', name='get_instance_action_form',
    #    method='get'),

    # get status for instance
    url(r'^instances/(?P<instance_id>[^/]+)/status/$', 'instance_status',
        name='get_instance_status', method='get'),
    # get task for instance
    #url(r'^instances/(?P<instance_id>[^/]+)/task/$', 'instance_task',
    #    name='get_instance_task', method='get'),
    # get power for instance
    #url(r'^instances/(?P<instance_id>[^/]+)/power/$', 'instance_power',
    #    name='get_instance_power', method='get'),
    # show the images list
    #url(r'^images/(?P<gotoflag>[^/]+)/$', 'image_list', name='image_list',
    #    method='get'),
    # get ip for instance
    url(r'^instances/(?P<instance_id>[^/]+)/ip/$', 'instance_ip',
        name='get_instance_ip', method='get'),

    # show the form table for creating instance
    url(r'^instances/new/$', 'launch_form_image', name='launch_form_image', method='get'),
    # submit the form table for creating instance
    url(r'^instances/$', 'launch_instance', name='launch_image', method='post'),

#    url(r'^instances/launche_image/topology/$', 'launch_instance_topology',
#        name='launch_image_topology', method='post'),
    # delete instance

    url(r'^instances/(?P<instance_id>[^/]+)/delete/$', 'instance_delete_form',
        name='instance_delete_form', method='get'),

    url(r'^instances/(?P<instance_id>[^/]+)/$', 'instance_delete',
        name='instance_delete', method='delete'),
    # action instance
    url(
        r'^instances/(?P<instance_id>[^/]+)/action/(?P<action>reboot|soft_reboot|pause|unpause|stop|resume)/$',
        'instance_action', name='instance_action', method='post'),

    url(r'^instances/(?P<instance_id>[^/]+)/action/reboot_form/$',
        'instance_reboot_form', name='instance_reboot_form', method='get'),
    url(r'^instances/(?P<instance_id>[^/]+)/action/reboot/$', 'instance_reboot',
        name='instance_reboot', method='post'),

    url(r'^instances/(?P<instance_id>[^/]+)/action/soft_reboot_form/$',
        'instance_soft_reboot_form', name='instance_soft_reboot_form',
        method='get'),
    url(r'^instances/(?P<instance_id>[^/]+)/action/soft_reboot/$',
        'instance_soft_reboot', name='instance_soft_reboot', method='post'),

    url(r'^instances/(?P<instance_id>[^/]+)/action/pause_form/$',
        'instance_pause_form', name='instance_pause_form', method='get'),
    url(r'^instances/(?P<instance_id>[^/]+)/action/pause/$', 'instance_pause',
        name='instance_pause', method='post'),

    url(r'^instances/(?P<instance_id>[^/]+)/action/unpause_form/$',
        'instance_unpause_form', name='instance_unpause_form', method='get'),
    url(r'^instances/(?P<instance_id>[^/]+)/action/unpause/$',
        'instance_unpause', name='instance_unpause', method='post'),

    url(r'^instances/(?P<instance_id>[^/]+)/action/stop_form/$',
        'instance_stop_form', name='instance_stop_form', method='get'),
    url(r'^instances/(?P<instance_id>[^/]+)/action/stop/$', 'instance_stop',
        name='instance_stop', method='post'),

    url(r'^instances/(?P<instance_id>[^/]+)/action/unstop_form/$',
        'instance_unstop_form', name='instance_unstop_form', method='get'),
    url(r'^instances/(?P<instance_id>[^/]+)/action/unstop/$', 'instance_unstop',
        name='instance_unstop', method='post'),

    # update instance information table
    url(r'^instances/(?P<instance_id>[^/]+)/edit/$', 'update_instance_form',
        name='update_instance_form', method='get'),
    # update instance information
    url(r'^instances/(?P<instance_id>[^/]+)/$', 'update_instance',
        name='update_instance', method='post'),
    # snapshot form
    url(r'^instances/(?P<instance_id>[^/]+)/snapshots/$',
        'create_snapshot_form', name='create_snapshot_form', method='get'),
    # submit snapshot
    url(r'^instances/(?P<instance_id>[^/]+)/action/snapshot/$',
        'create_snapshot', name='create_snapshot', method='post'),
    # just show the snapshot image to restore instance
    url(r'^instances/(?P<instance_id>[^/]+)/snapshots/restore/$', 'restore_instance_form',
        name='restore_instance', method='get'),
    #restore instance
    url(r'^instances/(?P<instance_id>[^/]+)/restore/$', 'restore_instance_data',
        name='restore_instance_data', method='post'),

    #instance spice
    url(r'^instances/(?P<instance_id>[^/]+)/tenants/(?P<tenant_id>[^/]+)/spice/$',
        'get_instance_spice_console', name='get_instance_spice_console',
        method='get'),

    #snapshots list
    url(r'^instances/(?P<instance_id>[^/]+)/snapshots/list/$', 'snap_to_tem_list', name='get_snapshots_list', method='get'),

    #set snapshots public
    url(r'^instances/(?P<snap_id>[^/]+)/(?P<instance_id>[^/]+)/public/$',
        'set_snapshot_public', name='set_snapshot_public', method='post'),
    #get instance monitor infos
    url(r'^instances/(?P<instance_id>[^/]+)/monitor_infos/$',
        'get_instance_monitor_info', name='get_instance_monitor_info',
        method='get'),
    #get instances detail with tenant switch
    url(r'^tenants/(?P<tenant_id>[^/]+)/instances/(?P<instance_id>[^/]+)/$',
        'instance_detail_with_tenant_switch',
        name='get_instance_detail_with_tenant_switch', method='get'),

    url(r'^instance/get/all/params/$', 'get_tenant_security_network', name='get_tenant_security_network', method='get'),

    #: Add by Xu Lei 2013-03-11instance_id
    #: Begin #
    # distribute instance to a specify user
    url(r'^instances/(?P<instance_id>[^/]+)/distribution/$',
        'distribution_instance_to_user', name='distribution_instance_to_user',
        method='post'),
    # upgrade relationship for instance and user
    # get relationship for instance and user
    url(r'^instances/(?P<instance_id>[^/]+)/distribution/detail/$',
        'get_distribution_user_form', name='get_distribution_detail',
        method='get'),

    url(r'instances/(?P<instance_id>[^/]+)/distribution/', 'distribution_instance_form',
        name='distribution_instance_form', method='get'),
    url(r'instances/(?P<instance_id>[^/]+)/undistribution/', 'delete_distribution_form',
        name='delete_distribution_form', method='get'),
    # drop relationship for instance and user
    url(r'^instances/(?P<instance_id>[^/]+)/delete/distribution/$',
        'delete_distribution', name='delete_distribution', method='delete'),
    url(r'^instances/(?P<instance_id>[^/]+)/classify/all/$',
        'get_instance_classify', name='get_instance_classify', method='get'),
    url(r'^instances/(?P<instance_id>[^/]+)/classify/$',
        'select_instance_classify', name='select_instance_classify',
        method='post'),
    url(r'^instances/classify/page/$', 'instance_classify_new',
        name="instance_classify_new", method="get"),

    #get instance classify
    url(r'^instances/classify/page/$', 'instance_classify_action',
        name="instance_classify_action", method="post"),

    url(r'^instances/classify/(?P<classify_id>[^/]+)/$',
        'instance_classify_delete', name="instance_classify_delete",
        method="get"),
    url(r'^instances/classify/(?P<classify_id>[^/]+)/$',
        'instance_classify_delete_action',
        name="instance_classify_delete_action", method="delete"),
    url(r'^instances/classify/(?P<classify_id>[^/]+)/edit/$',
        'instance_classify_update', name="instance_classify_update",
        method="get"),
    url(r'^instances/classify/(?P<classify_id>[^/]+)/$',
        'classify_update_action', name="classify_update_action", method="post"),
    url(r'^instances/(?P<instance_id>[^/]+)/flavors/$', 'instance_flavor_list',
        name="instance_flavor_list", method="get"),
    url(r'^instances/(?P<instance_id>[^/]+)/flavor/confirm/$',
        'instance_flavor_confirm', name="instance_flavor_confirm",
        method="get"),
    url(r'^instances/(?P<instance_id>[^/]+)/flavor/confirm_action/$',
        'flavor_confirm_action', name="flavor_confirm_action", method="get"),

    url(r'^instances/(?P<instance_id>[^/]+)/flavor/$', 'instance_flavor_update',
        name="instance_flavor_update", method="post"),
    url(r'^instances/changetenant/security_groups/$', 'create_instance_select_security',
        name='instance_change_tenant_form', method='get'),
    url(r'^instances/gtk/(?P<tenant_id>[^/]+)/(?P<instance_id>[^/]+)/client/$',
        'get_instance_gtk_client', name='get_instance_gtk_client',
        method='get'),
    #: End #

    url(r'^instances/network/get_network_list/$', 'instance_get_network_list',
        name='instance_get_network_list', method='get'),
    #Instance live migrate
    url(r'^instances/(?P<instance_id>[^/]+)/migrate/$', 'instance_live_migrate',
        name='instance_live_migrate', method='get'),
    url(r'^instances/(?P<instance_id>[^/]+)/handle_migrate/$',
        'handle_instance_live_migrate', name='handle_instance_live_migrate',
        method='post'),
    url(r'^instances/instance_host/$', 'get_instance_host',
        name='get_instance_host', method='get'),

    url(r'^instances/(?P<instance_id>[^/]+)/tenants/(?P<tenant_id>[^/]+)/vm_info/$',
        'update_instance_view_date', name='update_instance_view_date',
        method='get'),
    url(r'^instances/delete_instances/del/$', 'delete_instances',
        name='delete_instances', method='delete'),
    url(r'^instances/flavor/info/$','get_ins_flavor',name='get_ins_flavor',method='get'),
    url(r'^instances/project/quotas/$','get_project_usages',name='get_project_usages',method='get'),
    url(r'^instances/tenant/users/$','get_tenant_user',name='get_tenant_user',method='get'),
    url(r'^instances/terminate/console/$', 'terminate_instance_console', name='terminate_instance_console', method='get'),
    url(r'^instances/(?P<instance_id>[^/]+)/update/umask/(?P<umask>[^/]+)/$', 'update_instance_umask_form',
        name='update_instance_umask_form', method='get'),
    url(r'^instances/(?P<instance_id>[^/]+)/update/umask/(?P<umask>[^/]+)/usb/deal/$', 'update_instance_usb_umask',
        name='update_instance_usb_umask', method='post'),
    url(r'^instances/(?P<instance_id>[^/]+)/update/umask/(?P<umask>[^/]+)/audio/deal/$', 'update_instance_audio_umask',
        name='update_instance_audio_umask', method='post'),

    #Member action
)


