from django.db.models.signals import post_syncdb

from dashboard.authorize_manage import  ROLE_ADMIN, ROLE_MEMBER,\
    ROLE_PROJECTADMIN
from dashboard.control_manage import *
from dashboard.control_manage import models as control_manage_models

from .models import Controller

# initialize


TOP_MENU = [
    {'label_name': 'Resource Manage', 'action_name': 'Resource Manage',
     'action_type': ACTION_MENU, 'role': ROLE_ADMIN, 'parent_id': -1,
     'token': ''},
    {'label_name': 'Organization Manage', 'action_name': 'Organization Manage',
     'action_type': ACTION_MENU, 'role': ROLE_ADMIN, 'parent_id': -1,
     'token': ''},
    {'label_name': 'Network Manage', 'action_name': 'Network Manage',
     'action_type': ACTION_MENU, 'role': ROLE_ADMIN, 'parent_id': -1,
     'token': ''},
    {'label_name': 'System Manage', 'action_name': 'System Manage',
     'action_type': ACTION_MENU, 'role': ROLE_ADMIN, 'parent_id': -1,
     'token': ''},
    {'label_name': 'Common Manage', 'action_name': 'Common Manage',
     'action_type': ACTION_MENU, 'role': ROLE_MEMBER, 'parent_id': -1,
     'token': ''},
]

SUB_MENU = {
    'Resource Manage':
        [
            {'label_name': 'Global Monitor',
             'action_name': 'monitor_manage_index', 'action_type': ACTION_MENU,
             'role': ROLE_ADMIN, 'parent_id': 0, 'token': 'View Global Monitor'},
            {'label_name': 'Instance Manage',
             'action_name': 'get_instance_list', 'action_type': ACTION_MENU,
             'role': ROLE_ADMIN, 'parent_id': 0, 'token': 'View Own Instance'},
            {'label_name': 'Image Manage', 'action_name': 'get_image_list',
             'action_type': ACTION_MENU, 'role': ROLE_ADMIN, 'parent_id': 0,
             'token': 'View Image'},
            {'label_name': 'HardTemplate Manage',
             'action_name': 'get_flavor_list', 'action_type': ACTION_MENU,
             'role': ROLE_ADMIN, 'parent_id': 0, 'token': 'View Flavor'},
            {'label_name': 'Foundation Manage', 'action_name': 'get_node_index',
             'action_type': ACTION_MENU, 'role': ROLE_ADMIN, 'parent_id': 0,
             'token': 'View Node'},
            {'label_name': 'Volume Manage', 'action_name': 'get_volume_list',
             'action_type': ACTION_MENU, 'role': ROLE_ADMIN, 'parent_id': 0,
             'token': 'View Volume'},
            {'label_name': 'Software Manage',
             'action_name': 'get_software_list', 'action_type': ACTION_MENU,
             'role': ROLE_ADMIN, 'parent_id': 0, 'token': 'View Software'},
        ],
    'Organization Manage':
        [
            {'label_name': 'Authorization Manage',
             'action_name': 'get_project_list', 'action_type': ACTION_MENU,
             'role': ROLE_ADMIN, 'parent_id': 1, 'token': 'View Project'},
            {'label_name': 'User Manage', 'action_name': 'get_user_list',
             'action_type': ACTION_MENU, 'role': ROLE_ADMIN, 'parent_id': 1,
             'token': 'View User'},
            {'label_name': 'Role Manage', 'action_name': 'get_role_list',
             'action_type': ACTION_MENU, 'role': ROLE_ADMIN,
             'parent_id': 1, 'token': 'View Role'},
            {'label_name': 'Check Manage', 'action_name': 'get_task_list',
             'action_type': ACTION_MENU, 'role': ROLE_ADMIN,
             'parent_id': 1, 'token': 'View Task'},
        ],
    'Network Manage':
        [
            {'label_name': 'Virtual NetWork Manage',
             'action_name': 'get_network_projects', 'action_type': ACTION_MENU,
             'role': ROLE_ADMIN, 'parent_id': 0, 'token': 'View Network'},
            {'label_name': 'Virtual Routers Manage',
             'action_name': 'get_routers_projects', 'action_type': ACTION_MENU,
             'role': ROLE_ADMIN, 'parent_id': 0, 'token': 'View Router'},
            {'label_name': 'Virtual Address Manage',
             'action_name': 'get_floating_ips_address',
             'action_type': ACTION_MENU, 'role': ROLE_ADMIN, 'parent_id': 0,
             'token': 'View Address'},
            {'label_name': 'Network Security Manage',
             'action_name': 'get_securitygroup_projects',
             'action_type': ACTION_MENU, 'role': ROLE_ADMIN, 'parent_id': 0,
             'token': 'View SecurityGroup'},
            #            {'label_name': 'Virtual NetWork Topology',
            #             'action_name': 'get_network_topology',
            # 'action_type': ACTION_MENU,
            #             'role': ROLE_ADMIN, 'parent_id': 0, 'token': ''},
        ],

    'System Manage':
        [
            {'label_name': 'Notice Manage', 'action_name': 'get_notice_list',
             'action_type': ACTION_MENU, 'role': ROLE_ADMIN, 'parent_id': 0,
             'token': 'View Notice'},
            {'label_name': 'Log Query', 'action_name': 'log_query_index',
             'action_type': ACTION_MENU, 'role': ROLE_ADMIN, 'parent_id': 0,
             'token': 'View Own Logs'},
        ],
    'Common Manage':
        [
            {'label_name': 'Instance Manage',
             'action_name': 'get_instance_list',
             'action_type': ACTION_MENU, 'role': ROLE_MEMBER, 'parent_id': 0,
             'token': ''},

            {'label_name': 'Software Manage',
             'action_name': 'get_software_list', 'action_type': ACTION_MENU,
             'role': ROLE_MEMBER, 'parent_id': 0,
             'token': 'log_query_index'},
        ],

}

PROJECT_ADMIN_TOP_MENU = [
    {'label_name': 'Resource Manage', 'action_name': 'Resource Manage',
     'action_type': ACTION_MENU, 'role': ROLE_PROJECTADMIN, 'parent_id': -1,
     'token': ''},
    {'label_name': 'Organization Manage', 'action_name': 'Organization Manage',
     'action_type': ACTION_MENU, 'role': ROLE_PROJECTADMIN, 'parent_id': -1,
     'token': ''},
    {'label_name': 'Network Manage', 'action_name': 'Network Manage',
     'action_type': ACTION_MENU, 'role': ROLE_PROJECTADMIN, 'parent_id': -1,
     'token': ''},
    {'label_name': 'System Manage', 'action_name': 'System Manage',
     'action_type': ACTION_MENU, 'role': ROLE_PROJECTADMIN, 'parent_id': -1,
     'token': ''},
]

PROJECT_ADMIN_SUB_MENU = {
    'Resource Manage':
        [
            {'label_name': 'Instance Manage',
             'action_name': 'get_instance_list',
             'action_type': ACTION_MENU, 'role': ROLE_PROJECTADMIN,
             'parent_id': 0, 'token': ''},
            {'label_name': 'Image Manage', 'action_name': 'get_image_list',
             'action_type': ACTION_MENU, 'role': ROLE_PROJECTADMIN,
             'parent_id': 0, 'token': ''},
            {'label_name': 'Volume Manage', 'action_name': 'get_volume_list',
             'action_type': ACTION_MENU, 'role': ROLE_PROJECTADMIN,
             'parent_id': 0, 'token': ''},
            {'label_name': 'Software Manage',
             'action_name': 'get_software_list',
             'action_type': ACTION_MENU, 'role': ROLE_PROJECTADMIN,
             'parent_id': 0, 'token': ''},
        ],
    'Organization Manage':
        [
            {'label_name': 'Authorization Manage',
             'action_name': 'get_project_list',
             'action_type': ACTION_MENU, 'role': ROLE_PROJECTADMIN,
             'parent_id': 1, 'token': ''},
            {'label_name': 'User Manage', 'action_name': 'get_user_list',
             'action_type': ACTION_MENU, 'role': ROLE_PROJECTADMIN,
             'parent_id': 1, 'token': ''},
            {'label_name': 'Role Manage', 'action_name': 'get_role_list',
             'action_type': ACTION_MENU, 'role': ROLE_PROJECTADMIN,
             'parent_id': 1, 'token': ''},
        ],
    'Network Manage':
        [
            {'label_name': 'Virtual NetWork Manage',
             'action_name': 'get_network_projects',
             'action_type': ACTION_MENU, 'role': ROLE_PROJECTADMIN,
             'parent_id': 0, 'token': ''},
            {'label_name': 'Virtual Routers Manage',
             'action_name': 'get_routers_projects',
             'action_type': ACTION_MENU, 'role': ROLE_PROJECTADMIN,
             'parent_id': 0, 'token': ''},
            {'label_name': 'Virtual Address Manage',
             'action_name': 'get_floating_ips_address',
             'action_type': ACTION_MENU, 'role': ROLE_PROJECTADMIN,
             'parent_id': 0, 'token': ''},
            {'label_name': 'Network Security Manage',
             'action_name': 'get_securitygroup_projects',
             'action_type': ACTION_MENU, 'role': ROLE_PROJECTADMIN,
             'parent_id': 0, 'token': ''},
            #            {'label_name': 'Virtual NetWork Topology',
            #             'action_name': 'get_network_topology',
            #             'action_type': ACTION_MENU,
            # 'role': ROLE_PROJECTADMIN, 'parent_id': 0, 'token': ''},
        ],
    'System Manage':
        [
            {'label_name': 'Notice Manage', 'action_name': 'get_notice_list',
             'action_type': ACTION_MENU, 'role': ROLE_PROJECTADMIN,
             'parent_id': 0, 'token': ''},
            {'label_name': 'Log Query', 'action_name': 'log_query_index',
             'action_type': ACTION_MENU, 'role': ROLE_PROJECTADMIN,
             'parent_id': 0, 'token': ''},
        ],
}

"""
         The Model of Controller
         columns:
         label_name : the name of action which will show in view
         action_name : the name of action which will be controlled,
         for exmaples 'create_user'
         action_type : the type of action , value in ['menu'|'action']
         role        : the id of role , from keystone
         parent_id   : the parent_id of this action
"""

def init_top_menu(menus):
    top_menu_name_with_id = {}

    for top_menu in menus:
        control = Controller(label_name=top_menu['label_name'],
                             action_name=top_menu['action_name'],
                             action_type=top_menu['action_type'],
                             role=top_menu['role'],
                             parent_id=top_menu['parent_id'],
                             token=top_menu['token'],
        )
        try:
            control.save()
            top_menu_name_with_id[control.label_name] = control.id
        except Exception, e:
            print "init control_manage data failed.please check error (%s)" % e
            return None
    return top_menu_name_with_id


def init_sub_menu(menus, top_menu_name_with_id):
    for name in top_menu_name_with_id:
        sub_menus = menus[name]
        if sub_menus:
            for sub_menu in sub_menus:
                control = Controller(label_name=sub_menu['label_name'],
                                     action_name=sub_menu['action_name'],
                                     action_type=sub_menu['action_type'],
                                     role=sub_menu['role'],
                                     parent_id=top_menu_name_with_id[name],
                                     token=sub_menu['token'],
                )
                try:
                    control.save()
                except Exception, e:
                    print "init control_manage data failed.please check error"\
                          " (%s)" % e
                    return False
    return True


def init_control_manage_data(sender, **kwargs):
    if sender == control_manage_models:
        try:
            Controller.objects.all().delete()
        except Exception, e:
            print "flush control_manage data failed.please check error (%s)" % e
            return None

        top_menu_name_with_id = init_top_menu(TOP_MENU)
        if top_menu_name_with_id:
            print "create top menu ......... ok"
            if init_sub_menu(SUB_MENU, top_menu_name_with_id):
                print "create sub menu ......... ok"
            else:
                print "create sub menu ......... failed"
        else:
            print "create top menu ......... failed"

        top_menu_name_with_id = init_top_menu(PROJECT_ADMIN_TOP_MENU)
        if top_menu_name_with_id:
            print "create project admin top menu ......... ok"
            if init_sub_menu(PROJECT_ADMIN_SUB_MENU, top_menu_name_with_id):
                print "create project admin sub menu ......... ok"
            else:
                print "create project admin sub menu ......... failed"
        else:
            print "create project admin top menu ......... failed"
    return

post_syncdb.connect(init_control_manage_data, sender=control_manage_models)
