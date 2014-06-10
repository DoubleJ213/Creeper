__author__ = 'zwd'

from django.conf import settings

if settings.DEBUG:
    __log__ = 'v2.0.5 create'

import logging

LOG = logging.getLogger(__name__)

from django.conf.urls.defaults import patterns
from dashboard.urls import url


urlpatterns = patterns('dashboard.notice_manage.views',
    # get notice list
    url(r'^notices/$', 'index_notice', name='get_notice_list', method='get'),

    # get create form of notice
    url(r'^notices/new/$', 'create_notice', name='create_notice', method='get'),

    # get action for notice
    url(r'^notices/(?P<notice_uuid>[^/]+)/(?P<type>detail|edit|delete)/$',
        'notice_action', name='notice_action', method='get'),

    # create action for notice
    url(r'^notices/new/$', 'create_notice_action', name='create_notice_action',
        method='post'),

    # update action for notice
    url(r'^notices/edit/$', 'update_notice_action', name='update_notice_action',
        method='post'),

    # delete
    url(r'^notices/(?P<notice_uuid>[^/]+)/$', 'delete_notice_action',
        name='delete_notice_action', method='delete'),
    url(r'^notices/$', 'delete_notices', name='delete_notices', method='delete'),

    # get notice list for head
    url(r'^notices/list/head/$', 'get_notice_list_for_head',
        name='get_notice_list_for_head', method='get'),

    # get notice for head
    url(r'^notices/(?P<notice_uuid>[^/]+)/detail/head/$',
        'detail_notice_for_head', name='detail_notice_for_head', method='get'),

    # get notice list for ajax
    url(r'^notices/get_list/head/$', 'get_notices',
        name='get_notices', method='get'),
)