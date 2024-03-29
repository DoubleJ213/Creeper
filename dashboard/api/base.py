# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
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

from collections import Sequence
import logging

from django.conf import settings

from dashboard import exceptions


__all__ = ('APIResourceWrapper', 'APIDictWrapper',
           'get_service_from_catalog', 'url_for',)


LOG = logging.getLogger(__name__)


class APIResourceWrapper(object):
    """ Simple wrapper for api objects

        Define _attrs on the child class and pass in the
        api object as the only argument to the constructor
    """
    _attrs = []

    def __init__(self, apiresource):
        self._apiresource = apiresource

    def __getattr__(self, attr):
        if attr in self._attrs:
            # __getattr__ won't find properties
            return self._apiresource.__getattribute__(attr)
        else:
            msg = ('Attempted to access unknown attribute "%s" on '
                   'APIResource object of type "%s" wrapping resource of '
                   'type "%s".') % (attr, self.__class__,
                                    self._apiresource.__class__)
            LOG.debug(exceptions.error_color(msg))
            raise AttributeError(attr)


class APIDictWrapper(object):
    """ Simple wrapper for api dictionaries

        Some api calls return dictionaries.  This class provides identical
        behavior as APIResourceWrapper, except that it will also behave as a
        dictionary, in addition to attribute accesses.

        Attribute access is the preferred method of access, to be
        consistent with api resource objects from novclient.
    """
    def __init__(self, apidict):
        self._apidict = apidict

    def __getattr__(self, attr):
        try:
            return self._apidict[attr]
        except KeyError:
            msg = 'Unknown attribute "%(attr)s" on APIResource object ' \
                  'of type "%(cls)s"' % {'attr': attr, 'cls': self.__class__}
            LOG.debug(exceptions.error_color(msg))
            raise AttributeError(msg)

    def __getitem__(self, item):
        try:
            return self.__getattr__(item)
        except AttributeError, e:
            # caller is expecting a KeyError
            raise KeyError(e)

    def get(self, item, default=None):
        try:
            return self.__getattr__(item)
        except AttributeError:
            return default


class Quota(object):
    """Wrapper for individual limits in a quota."""
    def __init__(self, name, limit):
        self.name = name
        self.limit = limit

    def __repr__(self):
        return "<Quota: (%s, %s)>" % (self.name, self.limit)


class QuotaSet(Sequence):
    """
    Wrapper for client QuotaSet objects which turns the individual quotas
    into Quota objects for easier handling/iteration.

    `QuotaSet` objects support a mix of `list` and `dict` methods; you can use
    the bracket notiation (`qs["my_quota"] = 0`) to add new quota values, and
    use the `get` method to retrieve a specific quota, but otherwise it
    behaves much like a list or tuple, particularly in supporting iteration.
    """
    def __init__(self, apiresource=None):
        self.items = []
        if apiresource:
            for k, v in apiresource._info.items():
                if k == 'id':
                    continue
                self[k] = v

    def __setitem__(self, k, v):
            v = int(v) if v is not None else v
            q = Quota(k, v)
            self.items.append(q)

    def __getitem__(self, index):
        return self.items[index]

    def __len__(self):
        return len(self.items)

    def __repr__(self):
        return repr(self.items)

    def get(self, key, default=None):
        match = [quota for quota in self.items if quota.name == key]
        return match.pop() if len(match) else Quota(key, default)


def get_service_from_catalog(catalog, service_type):
    if catalog:
        for service in catalog:
            if service['type'] == service_type:
                return service
    return None


def url_for(request, service_type, admin=False, endpoint_type=None):
    endpoint_type = endpoint_type or getattr(settings,
                                             'OPENSTACK_ENDPOINT_TYPE',
                                             'publicURL')
    catalog = request.user.service_catalog
    service = get_service_from_catalog(catalog, service_type)
    if service:
        try:
            if admin:
                return service['endpoints'][0]['adminURL']
            else:
                return service['endpoints'][0][endpoint_type]
        except (IndexError, KeyError):
            raise exceptions.ServiceCatalogException(service_type)
    else:
        raise exceptions.ServiceCatalogException(service_type)


def is_service_enabled(request, service_type, service_name=None):
    service = get_service_from_catalog(request.user.service_catalog,
                                       service_type)
    if service and service_name:
        return service['name'] == service_name
    else:
        return service is not None
