__author__ = 'wangqing'

import logging

LOG = logging.getLogger(__name__)

from datetime import datetime, timedelta
import dateutil.parser

def log_search_str(request):
    search_str = ''

    username = request.POST.get('username', '')
    if username != '':
        search_str += " AND username='" + username + "'"

    module = request.POST.get('module', '')
    if module != '':
        search_str += " AND module='" + module + "'"

    event = request.POST.get('event', '')
    if event != '':
        search_str += " AND event='" + event + "'"

    tenant = request.POST.get('tenant', '')
    if tenant != '':
        search_str += " AND tenant='" + tenant + "'"
#    tenant_name = request.user.tenant_name
#    if tenant =='':
#        if tenant_name is not None and tenant_name != '':
#            search_str += " AND tenant='" + tenant_name + "'"
    begin_time = request.POST.get('begintime', '')
    if begin_time != '':
        begin_time = '%s' % (dateutil.parser.parse(begin_time)
                             - abs(datetime.now() - datetime.utcnow()))
        search_str += " AND create_at>='" + begin_time + "'"

    end_time = request.POST.get('endtime', '')
    if end_time != '':
        end_time = '%s' % (dateutil.parser.parse(end_time).replace(hour=23, minute=59, second=59)
                           - abs(datetime.now() - datetime.utcnow()))
        search_str += " AND create_at<='" + end_time + "'"

    return search_str
