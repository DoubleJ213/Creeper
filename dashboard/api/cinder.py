# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Openstack, LLC
# Copyright 2012 Nebula, Inc.
# Copyright (c) 2012 X.commerce, a business unit of eBay Inc.
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

from __future__ import absolute_import

import logging

from django.conf import settings
from django.utils.translation import ugettext as _

from cinderclient.v1 import client as cinder_client

from dashboard.api.base import url_for
from dashboard.api import nova
from dashboard.api.base import QuotaSet
from dashboard import exceptions

LOG = logging.getLogger(__name__)


# API static values
VOLUME_STATE_AVAILABLE = "available"

#update by zhaolei request.user.token.id -> request.user.token
def cinderclient(request):
    insecure = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
    cinder_url = ""
    try:
        cinder_url = url_for(request, 'volume')
    except exceptions.ServiceCatalogException:
        LOG.debug('no volume service configured.')
        return None
    LOG.debug('cinderclient connection created using token "%s" and url "%s"' %
              (request.user.token.id, cinder_url))
    c = cinder_client.Client(request.user.username,
        request.user.token.id,
        project_id=request.user.tenant_id,
        auth_url=cinder_url,
        insecure=insecure,
        http_log_debug=settings.XXX_CLIENT_DEBUG)
    c.client.auth_token = request.user.token.id
    c.client.management_url = cinder_url
    return c

def volume_list(request, search_opts=None):
    """
    To see all volumes in the cloud as an admin you can pass in a special
    search option: {'all_tenants': 1}
    """
    c_client = cinderclient(request)
    if c_client is None:
        return []
    return c_client.volumes.list(search_opts=search_opts)

# add by lishiquan 2013.7.2
def check_resource(request, size, display_name, volume_description,
                   volume_type=None,
                   snapshot_id=None):
    """
    volume_create_resource
    :param request:
    :return:
    """
    c_client = cinderclient(request)
    if c_client is None:
        return -1

    user_id = request.user.id
    tenant_id = request.user.tenant_id

    response = c_client.volumes.volume_create_resource(size, display_name,
        volume_description, volume_type, snapshot_id, user_id, tenant_id)

    try:
        response_code = response[0]

        if response_code.status_code == 200:
            try:
                response_status = response[1]['status']
            except Exception, ex:
                LOG.error(
                    'Unable to get the server available disks,the error is %s' % ex)
                response_status = False

    except Exception, ex:
        LOG.error(
            "Unable to get the server response status code ,the error is %s" % ex)
        response_status = False

    return response_status


def volume_get(request, volume_id):
    volume_data = cinderclient(request).volumes.get(volume_id)

    for attachment in volume_data.attachments:
        if "server_id" in attachment:
            # update by lishiquan 2013.6.28
            try:
                instance = nova.server_get(request, attachment['server_id'])
                attachment['instance_name'] = instance.name
            except Exception, ex:
                attachment['instance_name'] = _("Unknown instance")
                LOG.error("instance not found ,the error is %s" % ex)
        else:
            # Nova volume can occasionally send back error'd attachments
            # the lack a server_id property; to work around that we'll
            # give the attached instance a generic name.
            attachment['instance_name'] = _("Unknown instance")
    return volume_data


def volume_create(request, size, name, description, volume_type,
                  snapshot_id=None, metadata=None):
    return cinderclient(request).volumes.create(size, display_name=name,
        display_description=description, volume_type=volume_type,
        snapshot_id=snapshot_id, metadata=metadata)


def volume_delete(request, volume_id):
    return cinderclient(request).volumes.delete(volume_id)


def volume_snapshot_get(request, snapshot_id):
    return cinderclient(request).volume_snapshots.get(snapshot_id)


def volume_snapshot_list(request, search_opts=None):
    c_client = cinderclient(request)
    if c_client is None:
        return []
    return c_client.volume_snapshots.list(search_opts=search_opts)


def volume_snapshot_create(request, volume_id, name, description):
    return cinderclient(request).volume_snapshots.create(
        volume_id, display_name=name, display_description=description)


def volume_snapshot_delete(request, snapshot_id):
    return cinderclient(request).volume_snapshots.delete(snapshot_id)


def cinder_tenant_quota_get(request, tenant_id):
    c_client = cinderclient(request)
    if c_client is None:
        return QuotaSet()
    return QuotaSet(c_client.quotas.get(tenant_id))


def cinder_tenant_quota_update(request, tenant_id, **kwargs):
    return cinderclient(request).quotas.update(tenant_id, **kwargs)


def default_quota_get(request, tenant_id):
    return QuotaSet(cinderclient(request).quotas.defaults(tenant_id))


def volume_type_list(request):
    return cinderclient(request).volume_types.list()


def volume_type_create(request, name):
    return cinderclient(request).volume_types.create(name)


def volume_type_delete(request, volume_type_id):
    return cinderclient(request).volume_types.delete(volume_type_id)


def get_all_hosts_resources(request):
    return cinderclient(request).resources.get()