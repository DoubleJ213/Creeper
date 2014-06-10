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


__author__ = 'tangjun'
__date__ = '2013-02-18'
__version__ = 'v2.0.1'

from django.conf import settings

if settings.DEBUG:
    __log__ = 'v2.0.1 create'

import logging

LOG = logging.getLogger(__name__)

#    code begin

from novaclient import base
from novaclient.v1_1 import client as nova_client

from functools import wraps

from .base import url_for


class HostMonitorInfo(base.Resource):
    """
    Monitor contains infomartion about physical hosts
    """

    def __repr__(self):
        return "<monitor>"

    def to_json(self):
        return {'project': self.resource['project'],
                'memory_mb': self.resource['memory_mb'],
                'host': self.resource['host'],
                'cpu': self.resource['cpu'],
                'disk_gb': self.resource['disk_gb'],
        }


class MonitorManager(base.ManagerWithFind):
    """
    Manage :class:`Monitor` resources.
    """
    resource_class = HostMonitorInfo

    def _get_with_no_keywords(self, url):
        _resp, body = self.api.client.get(url)
        if _resp:
            return body
        else:
            return None

    def list(self):
        return self._list("/os-hosts",
            "hosts")

    def get(self, host_name):
        """
        Get monitor information for a specific host.
        :param tenant_id: Tenant ID to fetch usage for
        :param host_name: The name of host which will be monitored
        """
        return self._list("/os-hosts/%s" %
                          host_name,
            "host")

    def instance_diagnostics(self, instance_id):
        return self._get_with_no_keywords(
            "/servers/%s/diagnostics" % base.getid(instance_id))


def novaclient(request):
    c = nova_client.Client(request.user.username,
        request.user.token.id,
        project_id=request.user.tenant_id,
        auth_url=url_for(request, 'compute'))
    c.client.auth_token = request.user.token.id
    c.client.management_url = url_for(request, 'compute')
    return c


def get_host_monitor(request, host_name):
    return MonitorManager(novaclient(request)).get(host_name)


def get_hosts(request):
    return MonitorManager(novaclient(request)).list()

######################################################################

#add by tom : for diagnostics
def server_diagnostics(request, instance):
    return MonitorManager(novaclient(request)).instance_diagnostics(instance)

#: Add by Xu Lei 2013-0312
#: filter decorator for list view
#: BEGIN #
def dashboard_filter(statement):
    def decorator(func):
        @wraps(func)
        def _deco(*args, **kwargs):
            ret = func(*args, **kwargs)
            if ret:
                ret = filter(statement, ret)
            return ret

        return _deco

    return decorator

#: END #

#: Add by Xu Lei 2013-03-19
#: sort user list by name asc.
#: BEGIN #
def sort_by_name():
    def decorator(func):
        @wraps(func)
        def _deco(*args, **kwargs):
            ret = func(*args, **kwargs)
            if ret:
                #ret.sort(key=operator.attrgetter("name"))
                ret = sorted(ret, cmp=lambda x, y: cmp(x.name, y.name))
            return ret

        return _deco

    return decorator

#: END #

############################################################
# add by Tom 2013-04-28

"""
def get_free_disk_size():

    Get size of pv named "vrv-volumes"
    :return: the free size of pv,(GB)
             -1 indicate error when getting free size
    result = None
    try:
        data = subprocess.Popen("pvdisplay",stdout=subprocess.PIPE)
        result = data.stdout.read()
    except Exception,e:
        print "Error when get free disk size . the error is %s" % e
        return -1

    disk_value = re.findall('vrv-volumes\s+.*\s+.*\s+PE\sSize\s+(\d)\.\d{2}\sMiB\s+.*\s+.*\s+Free\sPE\s+(\d+)',result)
    for value in disk_value:
        free_size = int(value[0])*int(value[1])/1024

    #print "free size is %s GB" % free_size\
    return free_size

# add End
"""


# deprecated
def projectadmin_filter():
    def decorator(func):
        @wraps(func)
        def _deco(*args, **kwargs):
            from dashboard.authorize_manage import ROLE_PROJECTADMIN
            from dashboard.authorize_manage.utils import get_user_role_name

            request = args[0]
            list = func(*args, **kwargs)

            if get_user_role_name(request) != ROLE_PROJECTADMIN:
                return list

            ret_list = []
            tenant_role_map = request.user.tenant_role_map
            for item in list:
                for tenant_role in tenant_role_map:
                    tenant_id = None

                    if hasattr(item, 'tenant_id'):
                        tenant_id = item.tenant_id
                    elif hasattr(item, 'os-vol-tenant-attr:tenant_id'):
                        tenant_id = getattr(item,
                            'os-vol-tenant-attr:tenant_id', None)
                    elif hasattr(item, 'project_id'):
                        tenant_id = getattr(item, 'project_id', None)

                    if tenant_id == tenant_role['tenant_id']:
                        for role in tenant_role['roles']:
                            if role.name == ROLE_PROJECTADMIN:
                                ret_list.append(item)
            return ret_list

        return _deco

    return decorator
