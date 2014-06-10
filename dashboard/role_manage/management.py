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


import datetime
import json

from django.utils.importlib import import_module
from django.db.models.signals import post_syncdb
from django.utils.timezone import utc
from django.conf import settings
from keystoneclient.v2_0 import client as keystone_client

from dashboard.role_manage import models as role_manage_models
from dashboard.role_manage.models import Right, Role_right



right_modules_list = [
    # add right configuration here
    'dashboard.monitor_manage.right',
    'dashboard.instance_manage.right',
    'dashboard.image_template_manage.right',
    'dashboard.hard_template_manage.right',
    'dashboard.node_manage.right',
    'dashboard.volume_manage.right',
    'dashboard.software_manage.right',
    'dashboard.project_manage.right',
    'dashboard.user_manage.right',
    'dashboard.role_manage.right',
    'dashboard.check_manage.right',
    'dashboard.virtual_network_manage.right',
    'dashboard.virtual_router_manage.right',
    'dashboard.virtual_address_manage.right',
    'dashboard.securitygroup_manage.right',
    'dashboard.notice_manage.right',
    'dashboard.log_manage.right',
]


def init_right_tb(right_modules):
    """
    init the right table in database
    :param right_modules: right module list
    :return: right list
    """
    _right_key_name = 'right_information'

    for right_module in right_modules:
        try:
            if isinstance(right_module, basestring):
                mod = import_module(right_module)

            right_information = getattr(mod, _right_key_name, None)
            if right_information != None and isinstance(right_information, list):
                add_right_in_database(right_information)
        except Exception, e:
            print "init %s data failed.please check error (%s)" % (right_module, e)
            return False

    return True

def get_roles():
    """
    Get roles in keystone
    :return: role list
    """
    insecure = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
    password = getattr(settings, 'OPENSTACK_ADMIN_TOKEN', 'admin')
    endpoint = getattr(settings, 'OPENSTACK_KEYSTONE_URL')
    try:
        client = keystone_client.Client(username=u'admin',
                                        password=password,
                                        tenant_id='',
                                        auth_url=endpoint,
                                        insecure=insecure)

        tenants = client.tenants.list()
        for tenant in tenants:
            if tenant.name == 'admin':
                client = keystone_client.Client(username=u'admin',
                                                password=password,
                                                tenant_id=tenant.id,
                                                auth_url=endpoint,
                                                insecure=insecure)
                break
        return client.roles.list()
    except Exception, e:
        print "get role list failed.please check error (%s)" % e
        return None

def add_role_right(role_id, right_name):
    right_key = Right.objects.get(name=right_name).key
    role_right = Role_right(role_id=role_id,
                            right_key=right_key)
    try:
        role_right.save()
    except Exception, e:
        print "add (%s,%s) to role_right failed.please check error (%s)" % (role_id, right_name, e)

def init_role_right_tb(role_list):
    """
    Init role_right table in database,
    role table has four default roles, role_name: admin, ProjectAdmin, Member, Auditor
    :return:
    """
    for role in role_list:
        id = role.id
        if role.name == u'admin':
            add_role_right(id, 'View Project')
            add_role_right(id, 'View Project Users')
            add_role_right(id, 'Create Project')
            add_role_right(id, 'Create Project User')
            add_role_right(id, 'Update Project')
            add_role_right(id, 'Update Project Quotas')
            add_role_right(id, 'Update Project User')
            add_role_right(id, 'Delete Project User')
            add_role_right(id, 'Delete Project')

            add_role_right(id, 'View User')
            add_role_right(id, 'Create User')
            add_role_right(id, 'Update User')
            add_role_right(id, 'Update Password')
            add_role_right(id, 'Delete User')

            add_role_right(id, 'View Role')
            add_role_right(id, 'Create Role')
            add_role_right(id, 'Update Role')
            add_role_right(id, 'Delete Role')
            add_role_right(id, 'Resume Role')

            add_role_right(id, 'View Task')
            add_role_right(id, 'Check Task')
        if role.name == u'Auditor':
            add_role_right(id, 'View Own Logs')
            add_role_right(id, 'View All Logs')
            add_role_right(id, 'Export Log List')
            add_role_right(id, 'Delete Log')
            add_role_right(id, 'View Task')
            add_role_right(id, 'Check Task')
        if role.name == u'ProjectAdmin':
            add_role_right(id, 'View Global Monitor')
            add_role_right(id, 'Update Threshold Strategy')

            add_role_right(id, 'View Own Instance')
            add_role_right(id, 'View All Instance')
            add_role_right(id, 'Add Instance')
            add_role_right(id, 'Reboot Instance')
            add_role_right(id, 'Delete Instance')
            add_role_right(id, 'Remote Desktop')
            add_role_right(id, 'Distribution Instance')
            add_role_right(id, 'Instance Classify')
            add_role_right(id, 'Live Migrate')
            add_role_right(id, 'Instance Flavor Resize')
            add_role_right(id, 'Update Instance Info')
            add_role_right(id, 'Soft Reboot Instance')
            add_role_right(id, 'Suspend Instance')
            add_role_right(id, 'Pause Instance')
            add_role_right(id, 'Backup Instance')
            add_role_right(id, 'Restore Backups')
            add_role_right(id, 'Quickly Create Image Templates')
            add_role_right(id, 'Audio Stop')
            add_role_right(id, 'USB Stop')
            add_role_right(id, 'Resume Instance')
            add_role_right(id, 'Unpause Instance')
            add_role_right(id, 'Undistribution Instance')
            add_role_right(id, 'Audio Open')
            add_role_right(id, 'USB Open')
            add_role_right(id, 'Get Backup List')

            add_role_right(id, 'View Image')
            add_role_right(id, 'Create Image')
            add_role_right(id, 'Update Image')
            add_role_right(id, 'Delete Image')
            add_role_right(id, 'ActiveAndStart')

            add_role_right(id, 'View Flavor')
            add_role_right(id, 'Add Flavor')
            add_role_right(id, 'Delete Falvor')

            add_role_right(id, 'View Node')
            add_role_right(id, 'Add Node')
            add_role_right(id, 'Delete Node')

            add_role_right(id, 'View Volume')
            add_role_right(id, 'Create Volume')
            add_role_right(id, 'Delete Volume')
            add_role_right(id, 'Attach Volume')
            add_role_right(id, 'Create Volume Snapshot')
            add_role_right(id, 'Delete Snapshot')
            add_role_right(id, 'Detach Volume')

            add_role_right(id, 'View Software')
            add_role_right(id, 'Software Upload')
            add_role_right(id, 'Delete Software')
            add_role_right(id, 'Download Software')

            add_role_right(id, 'View Project')
            add_role_right(id, 'View Project Users')
            add_role_right(id, 'Create Project User')
            add_role_right(id, 'Update Project')
            add_role_right(id, 'Update Project Quotas')
            add_role_right(id, 'Update Project User')
            add_role_right(id, 'Delete Project User')

            add_role_right(id, 'View User')
            add_role_right(id, 'Create User')
            add_role_right(id, 'Update User')
            add_role_right(id, 'Update Password')
            add_role_right(id, 'Delete User')

            add_role_right(id, 'View Network')
            add_role_right(id, 'Create Network')
            add_role_right(id, 'Edit NetWork')
            add_role_right(id, 'Delete NetWork')
            add_role_right(id, 'Create Subnet')
            add_role_right(id, 'Edit Subnet')
            add_role_right(id, 'Edit Port')
            add_role_right(id, 'Delete Port')
            add_role_right(id, 'Delete Subnet')

            add_role_right(id, 'View Router')
            add_role_right(id, 'Add RouterProject')
            add_role_right(id, 'Delete RouterProject')
            add_role_right(id, 'Set Gateway')
            add_role_right(id, 'Delete Gateway')
            add_role_right(id, 'Add Router Interface')
            add_role_right(id, 'Delete Router Interface')

            add_role_right(id, 'View Address')
            add_role_right(id, 'Allocate IP To Project')
            add_role_right(id, 'Release Floating IP')
            add_role_right(id, 'Associate IP')
            add_role_right(id, 'Disassociate IP')

            add_role_right(id, 'View SecurityGroup')
            add_role_right(id, 'Add SecurityGroup')
            add_role_right(id, 'Delete SecurityGroup')
            add_role_right(id, 'Create Rule')
            add_role_right(id, 'Delete Rule')

            add_role_right(id, 'View Notice')
            add_role_right(id, 'Create Notice')
            add_role_right(id, 'Update Notice')
            add_role_right(id, 'Delete Notice')

            add_role_right(id, 'View Own Logs')
            add_role_right(id, 'Export Log List')
            add_role_right(id, 'Delete Log')
        if role.name == u'Member':
            add_role_right(id, 'View Own Instance')
            add_role_right(id, 'Reboot Instance')
            add_role_right(id, 'Remote Desktop')
            add_role_right(id, 'Instance Classify')
            add_role_right(id, 'Update Instance Info')
            add_role_right(id, 'Soft Reboot Instance')
            add_role_right(id, 'Suspend Instance')
            add_role_right(id, 'Pause Instance')
            add_role_right(id, 'Backup Instance')
            add_role_right(id, 'Restore Backups')
            add_role_right(id, 'Resume Instance')
            add_role_right(id, 'Unpause Instance')
            add_role_right(id, 'Get Backup List')

            add_role_right(id, 'View Software')
            add_role_right(id, 'Download Software')
    return True

def add_right_in_database(right_list):
    """
    Add right data to database
    :param right_list: right list
    :return:
    """
    first_right = right_list[0]
    depends = json.dumps(first_right[2])
    mutex = json.dumps(first_right[3])
    created_at = datetime.datetime.now(tz=utc)
    right = Right(key=first_right[0],
                  name=first_right[1],
                  parent_id=-1,
                  depends=depends,
                  enabled=1,
                  created_at=created_at,
                  mutex=mutex,
                  description=first_right[4],
                  )
    try:
        right.save()
        first_id = right.id
    except Exception, e:
        print "init role manage data failed.please check error (%s)" % e
        return
    right_list.pop(0)
    for right_info in right_list:
        depends = json.dumps(right_info[2])
        mutex = json.dumps(right_info[3])
        created_at = datetime.datetime.now(tz=utc)
        right = Right(key=right_info[0],
                      name=right_info[1],
                      parent_id=first_id,
                      depends=depends,
                      enabled=1,
                      created_at=created_at,
                      mutex=mutex,
                      description=right_info[4],
                      )
        try:
            right.save()
        except Exception, e:
            print "init role manage data failed.please check error (%s)" % e
            return


def init_right_data(sender, **kwargs):
    if sender == role_manage_models:
        try:
            Right.objects.all().delete()
            Role_right.objects.all().delete()
        except Exception, e:
            print "flush role manage data failed.please check error (%s)" % e
            return None
        retval = init_right_tb(right_modules_list)
        if retval:
            print 'create rights ......... ok'
        else:
            print 'create rights ......... failed'

        role_list = get_roles()
        retval = init_role_right_tb(role_list)
        if retval:
            print 'create role_right ......... ok'
        else:
            print 'create role_right ......... failed'

    return

post_syncdb.connect(init_right_data, sender=role_manage_models)
