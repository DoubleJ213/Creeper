# coding: utf-8
# vim: tabstop=4 shiftwidth=4 softtabstop=4
import sys,os
reload(sys)
sys.setdefaultencoding('utf8')
import logging
import datetime
from django.conf import settings
from dashboard import exceptions
from dashboard.log_manage.models import LoggingAction


LOG = logging.getLogger(__name__)

__all__ = ('Event','logr','get_event_name','get_event_id')
#
# The Event
#
class Event(object):
    ENT_LOGIN = 0x11
    ENT_LOGOUT = 0x12
    ENT_NEWDATA = 0x13
    ENT_DATACHG = 0x14
    ENT_ROLECHG = 0x15
    ENT_PASSCHG = 0x16
    ENT_QUOTACHG = 0x17
    ENT_FLAVORBIND = 0x18
    ENT_FLAVORCHG = 0x19
    ENT_DELETE = 0x20


_EVENTS = {
    Event.ENT_LOGIN : {'pattern' : '用户%s在%s时间登录系统.','name' : '登录事件','content' : False},
    Event.ENT_LOGOUT : {'pattern' : '用户%s在%s时间登出系统.','name': '登出事件','content' : False},
    Event.ENT_NEWDATA : {'pattern' : '用户%s在%s时间新增数据:%s','name': '新增数据','content' : True},
    Event.ENT_DATACHG : {'pattern' : '用户%s在%s时间修改数据:%s','name': '数据改变','content' : True},
    Event.ENT_ROLECHG : {'pattern' : '用户%s在%s时间改变权限:%s','name': '权限改变','content' : True},
    Event.ENT_PASSCHG : {'pattern' : '用户%s在%s时间更新密码:%s','name': '密码更改','content' : True},
    Event.ENT_FLAVORBIND : {'pattern' : '用户%s在%s时间使用配置资源:%s', 'name':'配置绑定', 'content': True},
    Event.ENT_DELETE : {'pattern' : '用户%s在%s时间进行删除操作:%s', 'name':'删除事件', 'content': True},

}

def _get_type(event):
    global _EVENTS
    return _EVENTS[event]

#
# Obtain name with a type of event.
#
def get_event_name(event):
    global _EVENTS
    return _EVENTS[event]['name']

#
# Obtain id by event-name.
#
def get_event_id(event_name):
    global _EVENTS

    for item in _EVENTS:
        if _EVENTS[item]['name'] == event_name:
            return item

    return 0

#
# The api with action log.
#
def log_record(user, event, content=None):
    #if request is None or event is None:
    if user is None or event is None:
        LOG.error('request is None')

    username = user.username
    userid = user.id
    tenantname = user.tenant_name
    tenantid = user.tenant_id
    #if event == Event.ENT_LOGIN:
        #username = request.session['user_name']
        #userid = request.session['user_id']
        #tenantname = request.session['tenant']
        #tenantid = request.session['tenant_id']


    current_time = str(datetime.datetime.now())
    format_str = ''

    ent = _get_type(event)

    if ent['content'] is True:
        format_str = ent['pattern'] % (username,current_time,content)
    else:
        format_str = ent['pattern'] % (username,current_time)

    format_str = format_str.encode('utf-8')

    try:
        LoggingAction.objects.create(event=event,
            create_at=current_time,
            content=format_str,
            username=username,
            userid=userid,
            tenant=tenantname,
            tenantid=tenantid)
    except Exception,e:
        #raise exceptions.LogFailed('Unable to record log.')
        LOG.error('Unable to record log,%s' % e)

# It's simple name for log_record
def logr(user, event, content=None):
    try:
        return log_record(user, event, content)
    except Exception,e:
        LOG.error('Unable to record log.')

    return True


# Obtain all of log with list.
def log_list(request, **conds):
    full_list = []

    if len(conds) > 0:
        if 'limit' in conds:
            full_list = LoggingAction.objects.all()[0: conds['limit']].order_by('-create_at')
        elif 'tenant_id' in conds:
            tid = None
            if conds['tenant_id'] == 'self':
                tid = request.user.tenant_id
            else:
                tid = str(conds['tenant_id'])

            full_list = LoggingAction.objects.filter(tenantid=tid).order_by('-create_at')
        elif 'create_at' in conds:
            create_at = str(conds['create_at'])
            full_list = LoggingAction.objects.filter(create_at=create_at).order_by('-create_at')
        elif 'uuid' in conds:
            uuid = str(conds['uuid'])
            full_list = LoggingAction.objects.filter(uuid=uuid).order_by('-create_at')

    else:
        full_list = LoggingAction.objects.all().order_by('-create_at')
        length = len(full_list)
    return full_list


# Clean all log
def log_clean(request, user_id=None, tenant_id=None ,create_at = None ):
    filter_conds = {}
    if user_id is not None:
        filter_conds['user_id'] = user_id
    if tenant_id is not None:
        filter_conds['tenant_id'] = tenant_id
    if create_at is not None:
        filter_conds['create_at'] = create_at
    if len(filter_conds) > 0:
        try:
            logs = log_list(request,**filter_conds)
            if logs:
                for i in range(len(logs)):
                    logs[i].delete()
            #LoggingAction.objects.filter(create_at=str(create_at)).delete()
        except Exception,e:
            LOG.error('Unable to get the filtered log list,%s.' % e)
            return False
    else:
        LoggingAction.objects.all().delete()

    return True

# Obtain log count
def log_count(request):
    return len(LoggingAction.objects.all())


# Drop log by id
def log_delete(request, log_id):
    if log_id is None:
        #raise exceptions.LogFailed('require input is null.')
        LOG.error('require input is null.')
    LoggingAction.objects.filter(id=log_id).delete()
