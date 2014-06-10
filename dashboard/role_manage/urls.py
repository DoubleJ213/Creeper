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

__author__ = 'sunyu'
__date__ = '2013-10-21'
__version__ = 'v3.1.3'

from django.conf import settings

if settings.DEBUG:
    __log__ = 'v2.0.5 create'

import logging

LOG = logging.getLogger(__name__)

from django.conf.urls.defaults import patterns
from dashboard.urls import url


urlpatterns = patterns('dashboard.role_manage.views',
                       # get role list
                       url(r'^roles/$', 'get_role_list', name='get_role_list', method='get'),

                       url(r'^roles/new/$', 'create_role_form', name='create_role_form', method='get'),

                       # get create form of role
                       url(r'^roles/create/$', 'create_role', name='create_role', method='post'),

                       url(r'^roles/edit/(?P<role_id>[^/]+)/$',
                           'edit_role_form', name='edit_role_form', method='get'),


                       url(r'^roles/edit/(?P<role_id>[^/]+)/$',
                           'edit_role', name='edit_role', method='post'),

                       url(r'^roles/delete/(?P<role_id>[^/]+)/$', 'delete_role_form', name='delete_role_form',
                           method='get'),

                       # delete action for notice
                       url(r'^roles/delete/(?P<role_id>[^/]+)/$', 'delete_role', name='delete_role',
                           method='post'),

                       url(r'^roles/resume/(?P<role_id>[^/]+)/$', 'resume_role_form', name='resume_role_form',
                           method='get'),

                       # update action for notice
                       url(r'^roles/resume/(?P<role_id>[^/]+)/$', 'resume_role', name='resume_role',
                           method='post'),

                       url(r'^roles/rights/(?P<role_id>[^/]+)/$', 'index_right', name='get_right_list',
                           method='get'),

                       url(r'^rights/ajax/$', 'ajax_checkbox_right', name='checkbox_right',
                           method='get'),


                       url(r'^roles/(?P<role_id>[^/]+)/detail/$', 'get_role_detail', name='get_role_detail',
                           method='get'),

                       url(r'^roles/rights/relation$', 'get_rights_relation', name='get_rights_relation',
                           method='get'),

                       url(r'^rights/all/$', 'all_checkbox_right', name='all_checkbox_right',
                           method='get'),

                       url(r'^rights/cancel/$', 'checkbox_right_cancel', name='checkbox_right_cancel',
                           method='get'),


                       )
