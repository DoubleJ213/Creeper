__author__ = 'zwd'
__date__ = '2013-03-25'
__version__ = 'v2.0.5'

import datetime, md5
import logging

from django import shortcuts
from django.conf import settings
from django.http import HttpResponse
from django.utils.timezone import utc
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from dashboard import api
from dashboard.authorize_manage import ROLE_ADMIN
from dashboard.authorize_manage.utils import get_user_role_name
from dashboard.exceptions import Unauthorized
from dashboard.utils import jsonutils, UIResponse, Pagenation, check_permission
from dashboard.utils import ui_response, UI_RESPONSE_DWZ_ERROR, UI_RESPONSE_ERROR,\
    UI_RESPONSE_OK

from .models import Notice
from .forms import NoticeForm
from .utils import user_list

LOG = logging.getLogger(__name__)

if settings.DEBUG:
    __log__ = """v2.0.5 create [2013-03-25]
     v2.0.5 add check if fold exist or not when create and delete binary package of notice
    """


@check_permission('View Notice')
@require_GET
@Pagenation('notice_manage/index.html')
def index_notice(request):
    """
    :param request: request Object
    :return:
    """
    args = {}
    notices = []
    users = []
    try:
#        if get_user_role_name(request) == ROLE_ADMIN:
         notices = Notice.objects.order_by('-level', '-create_time')
#        else:
#            notices = Notice.objects.filter(operater_id=request.user.id).order_by('-level',
#                                                                                  '-create_time')
    except Exception, e:
        LOG.error('Can not get list of notices,error is %s' % e.message)

    try:
        users = user_list(request)
    except Unauthorized:
        raise
    except Exception, e:
        msg = 'Unable to retrieve user list,error is %s' % e.message
        LOG.error(msg)

    args['list'] = notices
    args['users'] = users
    return args


@check_permission('Create Notice')
@require_GET
def create_notice(request):
    """
    :param request:
    :return:
    """
    form = NoticeForm(request)
    return shortcuts.render(request, 'notice_manage/create.html',
        {'form': form})


@check_permission('Create Notice')
@require_POST
@UIResponse('Notice Manage', 'get_notice_list')
def create_notice_action(request):
    """
    :param request:request Object
    :return:
    """
    notice_form = NoticeForm(request, request.POST)
    if notice_form.is_valid():
        data = notice_form.cleaned_data
        title = data['title']
        content = data['content']
        level = data['level']
        release = data['release']
        create_time = datetime.datetime.now(tz=utc)
        update_time = create_time
        uuid = md5.new(str(create_time)).hexdigest()
        operater_id = request.user.id
        try:
            # add origin status
            notice = Notice(
                uuid=uuid,
                title=title,
                operater_id=operater_id,
                content=content,
                create_time=create_time,
                update_time=update_time,
                level=level,
                release=release
            )
            notice.save()
        except Exception, e:
            LOG.error("Create notice failed, error is %s !" % e)
            return HttpResponse(
            {"form": notice_form, "message": "", "statusCode": UI_RESPONSE_DWZ_ERROR}, status=UI_RESPONSE_ERROR)
    else:
        return HttpResponse(
            {"form": notice_form, "message": "", "statusCode": UI_RESPONSE_DWZ_ERROR}, status=UI_RESPONSE_ERROR)
    return HttpResponse({"message": "Create notice Success", "statusCode": UI_RESPONSE_OK},
        status=UI_RESPONSE_OK)


@check_permission('Update Notice')
@require_GET
def update_notice(request, notice_uuid):
    """
    :param request: request Object
    :param notice_uuid: the uuid of notice which will show in table
    :return:
    """
    try:
        notice = Notice.objects.get(uuid=notice_uuid)
    except Notice.DoesNotExist:
        LOG.error('Can not get notice (uuid=%s) information' % notice_uuid)
        return shortcuts.redirect('get_notice_list')
    return shortcuts.render(request, 'notice_manage/update.html',
        {'notice': notice})


@check_permission('Update Notice')
@require_POST
@UIResponse('Notice Manage', 'get_notice_list')
def update_notice_action(request):
    """
    :param request: request Object
    :return:
    """
    notice_form = NoticeForm(request, request.POST)
    if notice_form.is_valid():
        data = notice_form.cleaned_data
# maybe unused add by yangzhi 2013.11.13
#        user_id = request.user.id
#        operater_id = data['operater_id']
#        if user_id != operater_id and get_user_role_name(request) != ROLE_ADMIN:
#            msg = "Sorry , you do not have this permissions"
#            return HttpResponse(jsonutils.dumps(ui_response(message=msg)))
        title = data['title']
        notice_uuid = data['uuid']
        try:
            notice = Notice.objects.get(uuid=notice_uuid)
            notice.title = title
            notice.content = data['content']
            notice.level = data['level']
            notice.release = data['release']
            notice.update_time = datetime.datetime.now(tz=utc)
            notice.save()
        except Notice.DoesNotExist:
            msg = 'Can not get notice (uuid=%s) information' % notice_uuid
            return HttpResponse(jsonutils.dumps(ui_response(message=msg)))
        except Exception, e:
            LOG.error('Can not update notice uuid=%s,error is %s' % (
                notice_uuid, e.message))
            msg = 'update notice uuid=%s failed, please retry later.' % notice_uuid
            return HttpResponse(jsonutils.dumps(ui_response(message=msg)))
        return HttpResponse(
            {"message": "Update notice Success", "statusCode": UI_RESPONSE_OK,
             "object_name": title}, status=UI_RESPONSE_OK)
    else:
        return HttpResponse(jsonutils.dumps(ui_response(notice_form)))


@check_permission('Delete Notice')
@require_GET
def delete_notice(request, notice_uuid):
    return shortcuts.render(request, 'notice_manage/delete.html',
        {'notice_uuid': notice_uuid})


@check_permission('Delete Notice')
@require_http_methods(['DELETE'])
@UIResponse('Notice Manage', 'get_notice_list')
def delete_notice_action(request, notice_uuid):
    try:
        notice = Notice.objects.get(uuid=notice_uuid)
#    try:
#        notice = Notice.objects.get(id=notice_uuid)
#        if notice.operater_id != request.user.id \
#                and get_user_role_name(request) != ROLE_ADMIN:
#            msg = "Sorry , you do not have this permissions"
#            return HttpResponse(jsonutils.dumps(ui_response(message=msg)))
        notice.delete()
    except Exception, e:
        LOG.error('Can not delete notice uuid=%s,error is %s' % (
            notice_uuid, e.message))
        return HttpResponse({"message": 'Can not delete notice',
                             "statusCode": UI_RESPONSE_DWZ_ERROR},
                            status=UI_RESPONSE_ERROR)
    return HttpResponse({"message": "Delete notice Success",
                         "statusCode": UI_RESPONSE_OK,
                         "object_name": notice.title},
                        status=UI_RESPONSE_OK)


@check_permission('Delete Notice')
@require_http_methods(['DELETE'])
@UIResponse('Notice Manage', 'get_notice_list')
def delete_notices(request):
    try:
        notice_ids = request.POST.getlist('notice_check')
        for id in notice_ids:
            notice = Notice.objects.get(uuid=id)
#            if notice.operater_id != request.user.id \
#                    and get_user_role_name(request) != ROLE_ADMIN:
#                msg = "Sorry , you do not have this permissions"
#                return HttpResponse(jsonutils.dumps(ui_response(message=msg)))
            notice.delete()
    except Exception, e:
        LOG.error(e)
        return HttpResponse({"message": 'Can not delete notice',
                             "statusCode": UI_RESPONSE_DWZ_ERROR},
                            status=UI_RESPONSE_ERROR)
    return HttpResponse({"message": "Delete notice Success",
                         "statusCode": UI_RESPONSE_OK},
                        status=UI_RESPONSE_OK)


@require_GET
def detail_notice(request, notice_uuid):
    """
    :param request: request Object
    :param notice_uuid: the uuid of notice which will show in table
    :return:
    """
    notice = None
    try:
        notice = Notice.objects.get(uuid=notice_uuid)
        operater_id = notice.operater_id
        operater_name = api.keystone.user_get(request, operater_id).name
        setattr(notice, 'operater_name', operater_name)
    except Unauthorized:
        raise
    except Notice.DoesNotExist:
        LOG.error('Can not get notice (uuid=%s) information' % notice_uuid)
        return shortcuts.redirect('get_notice_list')
    except Exception, e:
        LOG.error('Can not get notice,error is %s.' % e.message)
    return shortcuts.render(request, 'notice_manage/detail.html',
        {'notice': notice})


@require_GET
@Pagenation('notice_manage/notice_list.html')
def get_notice_list_for_head(request):
    notices = []
    try:
        notices = Notice.objects.filter(release='1').order_by('-level',
            '-create_time')
    except Unauthorized:
        raise
    except Exception, e:
        LOG.error('Can not get list of notices,error is %s' % e.message)

    args = {}
    args['list'] = notices

    return args


@require_GET
def detail_notice_for_head(request, notice_uuid):
    """
    :param request: request Object
    :param notice_uuid: the uuid of notice which will show in table
    :return:
    """
    notice = None
    try:
        notice = Notice.objects.get(uuid=notice_uuid)
        operater_id = notice.operater_id
        try:
            operater_name = api.keystone.user_get(request, operater_id).name
        except Unauthorized:
            raise
        except Exception, e:
            LOG.error("Unable to get user,error is %s." % e.message)
            operater_name = "admin"
        setattr(notice, 'operater_name', operater_name)
    except Notice.DoesNotExist:
        LOG.error('Can not get notice (uuid=%s) information' % notice_uuid)
        return shortcuts.redirect('get_notice_list')
    except Exception, e:
        LOG.error("Unable to get notice,error is %s." % e.message)
    return shortcuts.render(request, 'notice_manage/notice_detail.html',
        {'notice': notice})


@require_GET
def get_notices(request):
    """
    :param request: request Object
    :return:
    """
    notices = None
    notice_objs = []
    try:
        notices = Notice.objects.filter(release='1').order_by('-level',
            '-create_time')
        i = 0
        for notice in notices:
            i = i + 1
            if i < 6:
                uuid = notice.uuid
                title = notice.title
                noticeObj = {'uuid': uuid,'title': title}
                notice_objs.append(noticeObj)
            else:
                break
    except Exception, e:
        LOG.error('Can not get list of notices,error is %s' % e)
    try:
        return HttpResponse(jsonutils.dumps(notice_objs))
    except Exception, e:
        LOG.error('Can not get notices,error is %s' % e)
        return HttpResponse('Not Found')


@require_GET
def notice_action(request, notice_uuid, type='detail'):
    if type == 'detail':
        return detail_notice(request, notice_uuid)
    elif type == 'edit':
        return update_notice(request, notice_uuid)
    elif type == 'delete':
        return delete_notice(request, notice_uuid)