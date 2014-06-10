
from django.db.models.signals import post_syncdb

from datetime import datetime
from dashboard.utils.i18n import get_text
from dashboard.authorize_manage import  ROLE_ADMIN, ROLE_MEMBER, ROLE_PROJECTADMIN
from dashboard.control_manage import *
from dashboard.control_manage import models as control_manage_models

from .models import NeedToDo

# initialize





NEED_TO_DO = [
    {'need_uuid': datetime.now().utcnow(), 'title': 'Please create your first tenant',
     'parameters':'',
     'content': 'Please create your first tenant',
     'work_func': 'create_project_need_form',
     'category': 'project_manage',
     'status':'new',
     'role':ROLE_ADMIN,'tenant_id':'','prepare_id':''},
    ]


"""
         The Model of Controller
         columns:
         need_uuid : the need_uuid of action primary_key
         title : according to the page of title
         content : according to the page of content
         work_func : the action of request url
         status : the status of this action
         role : the id of role , from keystone
         tenant_id : the tenant_id of this action
"""


def init_top_menu(menus):
    top_menu_name_with_id = {}

    for top_menu in menus:
        need_to_do = NeedToDo(need_uuid=top_menu['need_uuid'],
                             title=top_menu['title'],
                             parameters =top_menu['parameters'],
                             content=top_menu['content'],
                             work_func=top_menu['work_func'],
                             status=top_menu['status'],
                             category=top_menu['category'],
                             role=top_menu['role'],
                             tenant_id=top_menu['tenant_id'],
                             prepare_id=top_menu['prepare_id'],
        )
        try:
            need_to_do.save()
            top_menu_name_with_id[need_to_do.need_uuid] = need_to_do.need_uuid
        except Exception, e:
            print "init control_manage data failed.please check error (%s)" % e
            return None
    return top_menu_name_with_id

def init_control_manage_data(sender, **kwargs):
    if sender == control_manage_models:
        try:
            NeedToDo.objects.all().delete()
        except Exception, e:
            print "flush control_manage data failed.please check error (%s)" % e
            return None
        top_menu_name_with_id = init_top_menu(NEED_TO_DO)
        if top_menu_name_with_id:
            print "create need_to_do ......... ok"
        else:
            print "create need_to_do ......... failed"
    return

post_syncdb.connect(init_control_manage_data, sender=control_manage_models)
