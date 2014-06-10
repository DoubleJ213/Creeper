__author__ = 'zhuweidong'
__date__ = '2013-05-24'
__version__ = 'v2.0.8'

from django.conf import settings

if settings.DEBUG:
    __log__ = 'v2.0.1 create'

import logging
LOG = logging.getLogger(__name__)

from dashboard.api.creeper import dashboard_filter
from dashboard.api.keystone import keystoneclient


@dashboard_filter(lambda x: x.name not in ('glance', 'nova', 'keystore', 'swift'))
def user_list(request, tenant_id=None):
    return keystoneclient(request, admin=True).users.list(tenant_id=tenant_id)
