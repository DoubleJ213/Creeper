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
__date__ = '2012-01-31'
__version__ = 'v2.0.2'

import datetime
import logging
import traceback

from django.conf import settings
from django import http
from django import shortcuts
from django.core.urlresolvers import reverse
from django.core.cache import cache
from django.contrib import messages
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.utils.encoding import iri_to_uri
from django.utils.translation import ugettext as _

from dashboard import exceptions
from dashboard.utils import save_log
from dashboard.utils.ui import run_json


LOG = logging.getLogger(__name__)

if settings.DEBUG:
    __log__ = '2012-01-24 v2.0.1 create'\
              'v2.0.2 add X_http_methodoverride_middleware'

class DashboardMiddleware(object):
    """ The main Dashboard middleware class. Required for use of Dashboard. """

    def process_request(self, request):
        """ Adds data necessary for Horizon to function to the request.

        Adds a :class:`~dashboard.users.User` object to ``request.user``.
        """
        # A quick and dirty way to log users out
        def user_logout(request):
            if hasattr(request, '_cached_user'):
                del request._cached_user
                # Use flush instead of clear, so we rotate session keys in
            # addition to clearing all the session data
            request.session.flush()

        request.__class__.user_logout = user_logout

    #        request.__class__.user = get_user(request)

    def process_exception(self, request, exception):
        """
        Catches internal Dashboard exception classes such as NotAuthorized,
        NotFound and Http302 and handles them gracefully.
        """
        LOG.error(traceback.format_exc())
        if isinstance(exception, exceptions.Unauthorized):
            auth_url = reverse("get_login_view")
            next_url = iri_to_uri(request.get_full_path())
            if next_url != auth_url:
                param = "?%s=%s" % (REDIRECT_FIELD_NAME, next_url)
                redirect_to = "".join((auth_url, param))
            else:
                redirect_to = auth_url

            if request.is_ajax():
                return http.HttpResponse(content=_(
                    'The token maybe expired, please try to login again.'),
                                         status=401)
            return shortcuts.redirect(redirect_to)

        if isinstance(exception, exceptions.LicenseForbidden):
            return http.HttpResponse(
                content=_('License Forbidden. '
                          'If you want to continue, please buy other License.'),
                status=500)

        if isinstance(exception, exceptions.PermissionDeniedException):
            return http.HttpResponse(content=_('Permission Denied.'),
                                     status=200)

        # If an internal "NotFound" error gets this far, return a real 404.
        if isinstance(exception, exceptions.NotFound):
            raise http.Http404(exception)

        if isinstance(exception, exceptions.Http302):
            if exception.message:
                messages.error(request, exception.message)
            return shortcuts.redirect(exception.location)

        # default exception
        if not settings.DEBUG:
            if request.is_ajax():
                return http.HttpResponse(content=_('unknown error'),
                                         status=500)

    user = None

    def process_response(self, request, response):
        """
        Convert HttpResponseRedirect to HttpResponse if request is via ajax
        to allow ajax request to redirect url
        """
        user = DashboardMiddleware.user
        save_log(request, response, user)
        if request.is_ajax():
            if type(response) == http.HttpResponseRedirect:
                redirect_response = http.HttpResponse()
                redirect_response['X-Horizon-Location'] = response['location']
                return redirect_response
        return response

    def process_view(self, request, callback, callback_args, callback_kwargs):
        func_name = getattr(callback, 'func_name', None)
        setattr(request, 'callback', func_name)
        DashboardMiddleware.user = request.user


class X_http_methodoverride_middleware(object):
    """
        Enable HTTP METHOD [PUT|DELETE][GET]
    """

    def process_request(self, request):
        """
        :param request:
        :return: None

        Get the 'HTTP_X_HTTP_METHODOVERRIDE'(default) attibute of request
        .META or request.POST
        if has value, it will change method of request to this value ,
        and change request.META['REQUEST_METHOD'] to the same
        then add the value of request with request.POST
        """
        add_in_string = getattr(settings, 'ADD_IN_METHOD_STRING',
                                'HTTP_X_HTTP_METHODOVERRIDE')
        if add_in_string in request.META or add_in_string in request.POST:
            newMethod = getattr(request.META, add_in_string, None)
            if not newMethod:
                newMethod = request.POST[add_in_string]
            if 'PUT' == newMethod.upper():
                request.method = 'PUT'
                request.META['REQUEST_METHOD'] = 'PUT'
                request.PUT = request.POST
            if 'GET' == newMethod.upper():
                request.method = 'GET'
                request.META['REQUEST_METHOD'] = 'GET'
                request.GET = request.POST
            if 'DELETE' == newMethod.upper() or 'DEL' == newMethod.upper():
                request.method = 'DELETE'
                request.META['REQUEST_METHOD'] = 'DELETE'
                request.DELETE = request.POST


class WantAuthorizedMiddleware(object):
    _pass_url = ['/',
                 '/authorize_manage/login/',
                 '/authorize_manage/loginclientindex/',
                 '/authorize_manage/loginclient/',
                 '/authorize_manage/permit/',
                 '/authorize_manage/tips/']

    def process_request(self, request):
        path = iri_to_uri(request.get_full_path())
        end_index = path.find('?')
        if -1 != end_index:
            path = path[:end_index]
        for pass_url in self._pass_url:
            if path == pass_url:
                return

        if request.user and not request.user.is_authenticated():
            auth_url = reverse("get_login_view")
            auth_client_url = reverse("get_login_client_view")
            next_url = iri_to_uri(request.get_full_path())
            if next_url != auth_url and next_url != auth_client_url:
                param = "?%s=%s" % (REDIRECT_FIELD_NAME, next_url)
                if next_url.find('clientinstances') > 0:
                    redirect_to = "".join((auth_client_url, param))
                else:
                    redirect_to = "".join((auth_url, param))
            elif next_url == auth_client_url:
                redirect_to = auth_client_url
            else:
                redirect_to = auth_url
            messages.error(request, _("Please log in to continue."))
            return shortcuts.redirect(redirect_to)


class ExpiredTimeMiddleware(object):
    _pass_url = ['/authorize_manage/permit/',
                 '/authorize_manage/tips/']

    def process_request(self, request):
        path = iri_to_uri(request.get_full_path())
        end_index = path.find('?')
        if -1 != end_index:
            path = path[:end_index]
        for pass_url in self._pass_url:
            if path == pass_url:
                return

        quotas = cache.get('CreeperQuotas')
        if quotas:
            today = datetime.date.today()
            expire_time_str = quotas.get('ExpireTime')
            expire_time = datetime.date(
                *map(lambda x: int(x), expire_time_str.split('-')))

            if today > expire_time:
                return shortcuts.render(request,
                                        'authorize/expire_permit.html',
                                        status=403)
