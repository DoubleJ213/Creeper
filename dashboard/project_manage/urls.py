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


__author__ = 'liu xu'
__date__ = '2013-02-05'
__version__ = 'v2.0.1'

import logging

from django.conf import settings
from django.conf.urls.defaults import patterns
from dashboard.urls import url


if settings.DEBUG:
    __log__ = 'v2.0.1 create'

LOG = logging.getLogger(__name__)


urlpatterns = patterns('dashboard.project_manage.views',
    url(r'^projects/$', 'index_project', name='get_project_list', method='get'),
    url(r'^projects/all/$', 'get_all_project', name='get_all_project', method='get'),
    url(r'^projects/get_project_menu/$',
        'get_project_menu', name='get_project_menu', method='get'),

    # create project
    url(r'^projects/new/$', 'create_project_form', name='create_project_form', method='get'),
    url(r'^projects/$', 'create_project_action', name='create_project_action', method='post'),

    # update project
    url(r'^projects/(?P<tenant_id>[^/]+)/edit/$',
        'update_project_form', name='update_project_form', method='get'),
    url(r'^projects/(?P<tenant_id>[^/]+)/$',
        'update_project_action', name='update_project_action', method='post'),

    # update the quotas of a project
    url(r'^projects/(?P<tenant_id>[^/]+)/quotas/edit/$',
        'update_project_quotas_form', name='update_project_quotas_form', method='get'),
    url(r'^projects/(?P<tenant_id>[^/]+)/quotas/$',
        'update_project_quotas_action', name='update_project_quotas_action', method='post'),

    # get project users
    url(r'^projects/(?P<tenant_id>[^/]+)/users/$',
        'get_project_users', name='get_project_users', method='get'),
    # get project user
    url(r'^projects/(?P<tenant_id>[^/]+)/users/(?P<user_id>[^/]+)/info/$',
        'get_project_user', name='get_project_user', method='get'),

    # remove a user from one project
    url(r'^projects/(?P<tenant_id>[^/]+)/users/(?P<user_id>[^/]+)/delete/$',
        'delete_project_users_form', name='delete_project_users_form', method='get'),
    url(r'^projects/(?P<tenant_id>[^/]+)/users/(?P<user_id>[^/]+)/deleteuser/$',
        'delete_project_users_action', name='delete_project_users_action', method='delete'),

    # add a user to one project
    url(r'^projects/(?P<tenant_id>[^/]+)/users/new/$',
        'add_project_users_form', name='add_project_users_form', method='get'),
    url(r'^projects/(?P<tenant_id>[^/]+)/users/$',
        'add_project_users_action', name='add_project_users_action', method='post'),

    # edit the role for a user on one project
    url(r'^projects/(?P<tenant_id>[^/]+)/users/(?P<user_id>[^/]+)/edit/$',
        'edit_project_users_form', name='edit_project_users_form', method='get'),
    url(r'^projects/(?P<tenant_id>[^/]+)/users/(?P<user_id>[^/]+)/$',
        'edit_project_users_action', name='edit_project_users_action', method='post'),

    # delete one project
    url(r'^projects/(?P<tenant_id>[^/]+)/delete/$',
        'delete_project_form', name='delete_project_form', method='get'),
    url(r'^projects/(?P<tenant_id>[^/]+)/deleteproject/$',
        'delete_project_action', name='delete_project_action', method='delete'),

    # enable project
    url(r'^projects/(?P<tenant_id>[^/]+)/enable/$',
        'enable_project_form', name='enable_project_from', method='get'),
    url(r'^projects/(?P<tenant_id>[^/]+)/enableproject/$',
        'enable_project_action', name='enable_project_action', method='post'),

    # for homepage
    url(r'^projects/summary/$', 'get_project_summary', name='get_project_summary', method='get'),
)
