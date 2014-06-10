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

urlpatterns = patterns('dashboard.image_template_manage.views',
    # get all images
    url(r'^images/$', 'image_list', name='get_image_list', method='get'),
    # get update image form table
    url(r'^images/(?P<image_id>[^/]+)/edit/$', 'update_image_template_form',
        name='update_image_form', method='get'),
    # update the image information
    url(r'^images/(?P<image_id>[^/]+)/$', 'update_image_template',
        name='update_image_template', method='post'),
    # delete the image
    url(r'^images/(?P<image_id>[^/]+)/delete$', 'delete_image_form',
        name='delete_image_form', method='get'),

    url(r'^images/(?P<image_id>[^/]+)/$', 'delete_image',
        name='delete_image', method='delete'),

    url(r'^images/batch/list$', 'delete_image_batch',
        name='delete_image_batch', method='post'),
    # get the image's detail information
    url(r'^images/(?P<image_id>[^/]+)/$', 'image_detail',
        name='get_image_detail', method='get'),
    # get the image's status
    url(r'^images/(?P<image_id>[^/]+)/status', 'get_image_status',
        name='get_image_status', method='get'),
    # get create image form table
    url(r'^images/new', 'create_image_form', name='create_image_form',
        method='get'),
    # create a new image
    url(r'^images/$', 'create_image', name='create_image', method='post'),
    # create a new image and create a new instance
    url(r'^images/start/instance/$', 'create_image_goto_instance',
        name='create_image_goto_instance', method='post'),

    url(r'^images/image_form/(?P<uuid>[^/]+)/instance', 'instance_image_form',
        name="instance_image_form",
        method='get'),

    url(r'^images/instance/create_status/(?P<uuid>[^/]+)/$',
        'create_image_status', name="create_image_status",
        method='get'),

    url(r'^images/instance/(?P<instance_id>[^/]+)/search_status/$', 'search_image_status',
        name="search_image_status", method='get'),
    #update the image's status
    url(r'^images/(?P<image_id>[^/]+)/instance/update_status/$',
        'update_into_image_status',
        name="update_into_image_status", method='get'),

    url(r'^images/instance/detecting_status/(?P<uuid>[^/]+)/$',
        'detecting_image_status', name="detecting_image_status",
        method='get'),

    url(r'^images/image_form/detecting/(?P<uuid>[^/]+)/$',
        'detecting_image_form', name="detecting_image_form",
        method='get'),

    url(r'^images/image_form/instance_form_image/$', 'launch_form_image_template',
        name="launch_form_image_template",
        method='get'),

    url(r'^images/network/list/$', 'get_network_list',
        name='get_network_list', method='get'),

    url(r'^images/tenant/security_group_list$', 'change_tenant_form',
        name='change_tenant', method='get'),

    url(r'^images/switch/tenants$', 'img_fresh_progress',
        name='img_fresh_progress', method='get'),

#    url(r'^images/instance/page$',
#        'create_instance_page', name="create_instance_page",
#        method='get'),

)

