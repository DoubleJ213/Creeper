# coding: utf-8
# vim: tabstop=4 shiftwidth=4 softtabstop=4
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
__date__ = '2012-03-06'
__version__ = 'v2.0.1'

import md5
import logging
import dateutil.parser
from datetime import datetime
from functools import wraps

from django.conf import settings
from django.utils.timezone import utc
from django.utils.translation import ugettext
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirectBase
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django import shortcuts
from django.forms import BaseForm

from dashboard import exceptions
from dashboard.utils import jsonutils
from dashboard.utils.i18n import get_text
from dashboard.utils.logs_thread import CreateLogsThread
from dashboard.log_manage.models import LoggingAction
from dashboard.utils import db
from dashboard.authorize_manage.utils import get_user_role_id

if settings.DEBUG:
    __log__ = 'v2.0.1 create'

LOG = logging.getLogger(__name__)

NUMBERS_PER_PAGE = 10

# define response status here
# begin
UI_RESPONSE_DWZ_ERROR = 300
UI_RESPONSE_DWZ_SUCCESS = 200
UI_RESPONSE_ERROR = 500
UI_RESPONSE_NOTFOUND = 404
UI_RESPONSE_BADREQUEST = 400
UI_RESPONSE_OK = 200
UI_RESPONSE_DUPLICATE = 409
# define end


def run_json(status_code="300", message="Unknown",
             call_bacK_type="closeCurrent", forwardUrl='', object_name=''):
    return {"statusCode": status_code,
            "message": message,
            "navTabId": "",
            "rel": "",
            "callbackType": call_bacK_type,
            "forwardUrl": forwardUrl,
            "object_name": object_name,
    }


def ui_response(form=None, message="Unknown", status_code="300",
                object_name=""):
    if form:
        if form.errors:
            return run_json(message=form.errors.as_text())
        else:
            return run_json(status_code="200", message=get_text(message),
                            object_name=object_name)

    return run_json(status_code=status_code, message=get_text(message),
                    object_name=object_name)

#: Add by Xu Lei 2013-03-13
#: UIResponse for refreshing navTab
#: Update at 2013-03-15 for forwarding an URL with parameters
#: BEGIN #
def UIResponse(navTabId, forwardURL):
    def decorator(func):
        def _del_attributes(source, attributes):
            if attributes:
                for k in attributes:
                    if k in source:
                        del source[k]
            return source


        def _set_ui_element(source, args=None, url_rewrite=None):
            source['navTabId'] = ugettext(navTabId)
            if not url_rewrite:
                source['forwardUrl'] = reverse(forwardURL, args=args)
            else:
                source['forwardUrl'] = reverse(url_rewrite, args=args)

        @wraps(func)
        def _deco(*args, **kwargs):
            try:
                _response = func(*args, **kwargs)
            except Exception, e:
                LOG.error('invoke function error: %s' % (e))
                raise e

            if isinstance(_response, HttpResponseRedirectBase):
                LOG.debug('Proxy HTTP redirect response')
                return _response
            else:
                # parameter ref
                _args = None
                _url_rewrite = None
                _content = getattr(_response, '_container', None)
                if isinstance(_content, dict):
                    LOG.debug('Proxy UI response content.')
                    # forms.Form
                    if 'form' in _content:
                        _form = _content['form']
                        _new_content = ui_response(form=_form, message=get_text(
                            _content.get('message', 'Unknown')),
                                                   status_code=_content.get(
                                                       'statusCode', '300'))
                        _del_attributes(_content, ['form'])
                    else:
                        _new_content = run_json()
                        _new_content['message'] = get_text(
                            _content.get('message', 'Unknown'))
                        _new_content['statusCode'] = _content.get('statusCode',
                                                                  '300')

                    _args = _content.get('args', None)
                    _url_rewrite = _content.pop('url_rewrite', None)
                    # copy other elements to new dict
                    _del_attributes(_content, ['message', 'statusCode', 'args'])
                    for k, v in _content.items():
                        _new_content[k] = v

                elif isinstance(_content, BaseForm):
                    LOG.debug('Proxy form response content.')
                    _new_content = ui_response(form=_content)
                elif isinstance(_content, basestring):
                    try:
                        _new_content = jsonutils.load(_content)
                    except Exception, e:
                        return _response

                    LOG.debug('Proxy from application/json content')
                else:
                    LOG.debug('Proxy shortcuts render response.')
                    return _response

                _set_ui_element(_new_content, _args, _url_rewrite)
                json = jsonutils.dumps(_new_content)
                LOG.debug(
                    'Return application/json response, response body %s' % (
                        json))
                return HttpResponse(json)

        return _deco

    return decorator

    #: END #


def Pagenation(template_name):
    def decorator(func):
        def get_template_name(kwargs):
            if kwargs.has_key('template_name'):
                return kwargs.get('template_name', None)
            else:
                return template_name

        @wraps(func)
        def _deco(request, *args, **kwargs):
            try:
                _response = func(request, *args, **kwargs)
            except Exception, e:
                LOG.error('invoke function error: %s' % (e))
                raise e
                #            if _response.has_key('redirect'):
            #                redirect = _response.get('redirect',None)
            #                _response.__delitem__('redirect')
            #                return shortcuts.redirect(redirect,_response)
            #
            #            if _response.has_key('msg'):
            #                msg = _response.get('msg',None)
            #                return HttpResponse(msg)

            list = _response.get('list', [])
            number_per_page = NUMBERS_PER_PAGE
            if _response.get('numPerPage', 0):
                number_per_page = _response.get('numPerPage')
            if request.GET.has_key("numPerPage"):
                number_per_page = request.GET['numPerPage']
            paginator = Paginator(list, number_per_page)
            page = request.GET.get('pageNum', 1)
            try:
                page_obj = paginator.page(page)  #page obj
            except PageNotAnInteger:
                # If page is not an integer, deliver first page.
                page_obj = paginator.page(1)
            except EmptyPage:
                # If page is out of range (e.g. 9999),
                # deliver last page of results.
                page_obj = paginator.page(paginator.num_pages)

            setattr(page_obj, 'sequence_number',
                    (page_obj.number - 1) * page_obj.paginator.per_page)

            if _response.has_key('list'):
                _response.__delitem__('list')
            _response['page_obj'] = page_obj

            Template_name = get_template_name(kwargs)

            return shortcuts.render(request, Template_name, _response)

        return _deco

    return decorator


def start_thread(func):
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        ret = func(request, *args, **kwargs)
        if CreateLogsThread.logThread == None:
            CreateLogsThread.logThread = CreateLogsThread()
            CreateLogsThread.logThread.start()
        return ret

    return wrapper


def save_log(request, response, user):
    try:
        method_name = getattr(request, 'callback', None)
        status = response.status_code
        if settings.LOG_INFORMATIONS.has_key(method_name):
            method_info = settings.LOG_INFORMATIONS.get(method_name)
            module = method_info[1]
            type = method_info[2]
            desc = get_text(method_info[3])
            is_primary = method_info[4]

            user_id = user.id if user.id else ''
            username = user.username if user.username else ''

            tenant_id = ''
            if hasattr(user, 'tenant_id'):
                if username != 'admin':
                    tenant_id = user.tenant_id

            tenant_name = ''
            if hasattr(user, 'tenant_name'):
                if 'admin' == username:
                    tenant_name = 'admin'
                else:
                    tenant_name = user.tenant_name

            if not username and not tenant_name:
                # for AnonymousUser
                return

            try:
                content = getattr(response, 'content', None)
                if "" != content and content:
                    _content = jsonutils.loads(content)
                    object_name = None
                    statuscode = None
                    #                    _content = eval(content)
                    if isinstance(_content, dict):
                        object_name = _content.get('object_name', None)
                        statuscode = _content.get('statusCode', None)
                    if object_name:
                        desc = '%(desc)s:%(object_name)s' % {'desc': desc,
                                                             'object_name':
                                                                 object_name}
                    if statuscode:
                        status = statuscode

                    if type == 'edit' and  'change_user_password_action' ==\
                       method_name:
                        username = object_name

            except Exception, e:
                LOG.error("get object_name error.")

            create_at = datetime.now(tz=utc).strftime('%Y-%m-%d %H:%M:%S')
            content_time = dateutil.parser.parse(create_at) + abs(
                datetime.now() - datetime.utcnow())
            desc = desc % {
                'create_at': content_time.strftime('%Y-%m-%d %H:%M:%S'),
                'user': username}

            log = LoggingAction(uuid=md5.new(str(datetime.now())).hexdigest(),
                                module=module, event=type,
                                create_at=create_at, content=desc,
                                username=username, userid=user_id,
                                tenant=tenant_name, tenantid=tenant_id,
                                is_primary=is_primary, status=status)

            CreateLogsThread.logsq.put(log, block=False)
    except Exception, e:
        LOG.error("save logs error. %s" % e)


###################################

def check_permission(*args, **kwargs):
    """
    Check permission of the current user. Raise a PermissionDeniedException
    when a user has no rights with current request. If no parameters are passed
    in, it will use the name of the function for the right and check.

    :param args: the right that want to be checked.
    :type: string or list
    :return: function proxy
    :rtype: function proxy
    :raise: PermissionDeniedException

    Example::

        @check_permission('instance_create')
        def do_something(*args, *kwargs):
            ......

        or

        @check_permission('instance_list', 'instance_delete')
        def do_something(*args, *kwargs):
            ......

        or

        @check_permission() # it will check the right which name is
        'do_something'
        def do_something(*args, *kwargs):
            ......

    """

    def decorator(func):
        if not args and not kwargs:
            rights = [func.__name__]
            opt = 'and'
        else:
            or_conditions = kwargs.get('_or', None)
            if or_conditions:
                rights = or_conditions
                opt = 'or'
            else:
                rights = args
                opt = 'and'


        def proxy(request, *args, **kwargs):
            if not rights:
                raise exceptions.PermissionDeniedException(
                    'Current user does not have any rights.')

            # check permission from request or db
            if opt == 'and':
                for right in rights:
                    if not db.has_right(get_user_role_id(request), right):
                        raise exceptions.PermissionDeniedException(
                            'Permission Denied.')
                return func(request, *args, **kwargs)

            else:
                for right in rights:
                    if db.has_right(get_user_role_id(request), right):
                        return func(request, *args, **kwargs)
                raise exceptions.PermissionDeniedException(
                    'Permission Denied.')

        return proxy

    return decorator