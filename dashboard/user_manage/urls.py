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

from django.conf import settings
if settings.DEBUG:
    __log__ = 'v2.0.1 create'

import logging
LOG = logging.getLogger(__name__)

#    code begin

from django.conf.urls.defaults import patterns
from dashboard.urls import url

urlpatterns = patterns('dashboard.user_manage.views',
    # show the user list
    url(r'^users/$', 'index_user', name='get_user_list', method='get'),
    url(r'^users/(?P<user_id>[^/]+)/detail/$', 'user_detail',
        name='get_user_detail', method='get'),

    # create user
    url(r'^users/new/$', 'create_user_form', name='create_user_form', method='get'),
    url(r'^users/$', 'create_user_action', name='create_user_action', method='post'),

    # update user
    url(r'^users/(?P<user_id>[^/]+)/edit/$',
        'update_user_form', name='update_user_form', method='get'),
    url(r'^users/(?P<user_id>[^/]+)/$',
        'update_user_action', name='update_user_action', method='post'),

    # delete user
    url(r'^users/(?P<user_id>[^/]+)/delete/$',
        'delete_user_form', name='delete_user_form', method='get'),
    url(r'^users/(?P<user_id>[^/]+)/$',
        'delete_user_action', name='delete_user_action', method='delete'),

    # change user password
    url(r'^users/changepassword/$',
        'change_user_password_form', name='change_user_password_form', method='get'),
    url(r'^users/(?P<user_id>[^/]+)/changepassword/$',
        'change_user_password_action', name='change_user_password_action', method='post'),

    # change user password by admin
    url(r'^users/(?P<user_id>[^/]+)/editpassword/$',
        'update_user_password_form', name='update_user_password_form', method='get'),
    url(r'^users/(?P<user_id>[^/]+)/edituserpassword/$',
        'update_user_password_action', name='update_user_password_action', method='post'),
)
