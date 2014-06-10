# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
# Copyright 2013 Big Switch Networks
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
Methods and interface objects used to interact with external APIs.

API method calls return objects that are in many cases objects with
attributes that are direct maps to the data returned from the API http call.
Unfortunately, these objects are also often constructed dynamically, making
it difficult to know what data is available from the API object.  Because of
this, all API calls should wrap their returned object in one defined here,
using only explicitly defined atributes and/or methods.

In other words, Horizon developers not working on openstack_dashboard.api
shouldn't need to understand the finer details of APIs for
Keystone/Nova/Glance/Swift et. al.
"""

"""
Methods and interface objects used to interact with external APIs.

API method calls return objects that are in many cases objects with
attributes that are direct maps to the data returned from the API http call.
Unfortunately, these objects are also often constructed dynamically, making
it difficult to know what data is available from the API object.  Because of
this, all API calls should wrap their returned object in one defined here,
using only explicitly defined atributes and/or methods.

In other words, Horizon developers not working on horizon.api
shouldn't need to understand the finer details of APIs for
Keystone/Nova/Glance/Swift et. al.
"""

import datetime
import hashlib
import json
import os
import sys

from django.utils.timezone import utc

#: Add by Xu Lei 2013-03-12
#: WARNING: Don't change the order
#: BEGIN #

#: Filter dict for project
DASHBOARD_SYSTEM_PROJECT = ('admin', 'service',)

#: Filter dict for user
DASHBOARD_SYSTEM_USER = (
    'admin', 'glance', 'nova', 'keystore', 'swift', 'cinder', 'quantum', 'ec2',)

#: Filter dict for role
DASHBOARD_SYSTEM_ROLE = ('KeystoneServiceAdmin',)

#: END #

#from dashboard.api.base import *
#from dashboard.api.cinder import *
#from dashboard.api.glance import *
#from dashboard.api.keystone import *
#from dashboard.api.network import *
#from dashboard.api.nova import *
#from dashboard.api.quantum import *
#from dashboard.api.lbaas import *
#from dashboard.api.swift import *
#
#from dashboard.api.creeper import *
#from dashboard.api.log import *

_ORIGIN = sys.modules[__name__]
_PATH = __path__
_PACKAGE = __package__


class ProxyModule(object):
    def __init__(self):
        global _ORIGIN
        self.origin = _ORIGIN
        self.modules = self._load_sub_modules()
        self.functions = self._load_functions()
        self.workflows = self._load_workflows()

    def __getattr__(self, item):
        if item.startswith('__'):
            return getattr(self.origin, item)
        elif item in self.modules.keys():
            return self
        else:
            if item in self.workflows:
                return self.workflows[item]
            else:
                return self.functions.get(item, None)

    def _load_sub_modules(self):
        global _PATH
        global _PACKAGE
        sub_modules = {}
        cp = _PATH[0]
        pk = _PACKAGE
        filenames = os.listdir(cp)
        for filename in filenames:
            root, ext = os.path.splitext(filename)
            if ext == '.pyc' and not root.startswith('__'):
                module_class = '%s.%s' % (pk, root)
                __import__(module_class)
                sub_modules[root] = sys.modules[module_class]
        return sub_modules

    def _load_functions(self):
        functions = {}
        for module_class, module in self.modules.items():
            origin_funcs = dir(module)
            functions.update(
                {func: getattr(module, func) for func in origin_funcs if
                 not func.startswith('__')})
        return functions

    def _load_workflows(self):
        return {'server_create': server_create_workflow}

    @property
    def _nova(self):
        return self.modules['nova']

    @property
    def _cinder(self):
        return self.modules['cinder']

    @property
    def _glance(self):
        return self.modules['glance']

    @property
    def _keystone(self):
        return self.modules['keystone']

    @property
    def _quantum(self):
        return self.modules['quantum']


def server_create_workflow(request, dist_user_id, *args, **kwargs):
    from dashboard.check_manage.models import Task

    submit_time = datetime.datetime.now(tz=utc)
    uuid = hashlib.md5(str(submit_time)).hexdigest()
    task = Task(uuid=uuid,
                name='Create Instance',
                user_id=request.user.id,
                user_name=request.user.username,
                project_id=request.user.tenant_id,
                token_id=request.user.token.id,
                api='server_create',
                args=json.dumps(args),
                kwargs=json.dumps(kwargs),
                creeper_args=json.dumps(dist_user_id),
                submit_time=submit_time,
                expire_time=submit_time+datetime.timedelta(hours=24))
    task.save()
    return True

sys.modules[__name__] = ProxyModule()