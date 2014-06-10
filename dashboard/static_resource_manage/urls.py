__author__ = 'zwd'

import logging

from dashboard.urls import url

from django.conf import settings
from django.conf.urls.defaults import patterns

if settings.DEBUG:
    __log__ = 'v2.0.6 create'

LOG = logging.getLogger(__name__)

urlpatterns = patterns('dashboard.static_resource_manage.views',

    # go to resource_html
    url(r'^static_resources/(?P<type>node|project|instance)/$', 'goto_static_resource',
        name='goto_static_resource', method='get'),

    # get resource
    url(r'^static_resources/(?P<type>node|project|instance)/resource/$',
        'get_static_resource', name='get_static_resource', method='get'),

)