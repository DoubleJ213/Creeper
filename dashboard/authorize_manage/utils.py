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
__date__ = '2013-03-02'
__version__ = 'v2.0.1'

from django.conf import settings

if settings.DEBUG:
    __log__ = 'v2.0.1 create'

import logging
LOG = logging.getLogger(__name__)

#    code begin
import hashlib

from django.utils.translation import ugettext_lazy as _

from openstack_auth.user import set_session_from_user, create_user_from_token

from dashboard import api
from dashboard.authorize_manage import ROLE_ADMIN
from dashboard.exceptions import Unauthorized


def get_user_role_id(request):
    role_id = ''

    for role in request.user.roles:
        if role['name'] != ROLE_ADMIN:
            role_id = role['id']
            break
        else:
            role_id = role['id']

    return role_id


def get_user_role_name(request):
    role_name = ''

    for role in request.user.roles:
        if role['name'] != ROLE_ADMIN:
            role_name = role['name']
            break
        else:
            role_name = role['name']

    return role_name


def creeper_role_from_roles(roles):
    role_name = ''

    for role in roles:
        if role.name != ROLE_ADMIN:
            role_name = role.name
            break
        else:
            role_name = role.name

    return role_name


def switch_tenants(request, tenant_id):
    """
    Swaps a user from one tenant to another using the unscoped token from
    Keystone to exchange scoped tokens for the new tenant.
    """
    if request.user.tenant_id == tenant_id:
        return True

    endpoint = request.user.endpoint
    unscoped_token = request.session.get('unscoped_token', None)

    if unscoped_token:
        try:
            token = api.token_create_scoped(request,
                                            tenant_id,
                                            unscoped_token)
            user = create_user_from_token(request, token, endpoint)
            request.user = user
            set_session_from_user(request, user)
            return request.user
        except Unauthorized:
            raise
        except Exception, e:
            LOG.error('User(%s) can not authorize project %s. Error: %s'
                      % (request.user.id, tenant_id, e))
        return None

    return None


def create_token(request, username, password):
    """
    Creates a token using the username and password provided.
    """
    from keystoneclient.v2_0 import client as keystone_client
    from keystoneclient import exceptions as keystone_exceptions
    from keystoneclient.v2_0.tokens import Token, TokenManager
    from openstack_auth.exceptions import KeystoneAuthException
    from openstack_auth.utils import is_ans1_token

    insecure = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
    endpoint = request.user.endpoint
    try:
        client = keystone_client.Client(username=username,
                                        password=password,
                                        tenant_id='',
                                        auth_url=endpoint,
                                        insecure=insecure)

        unscoped_token_data = {"token": client.service_catalog.get_token()}
        unscoped_token = Token(TokenManager(None),
                                unscoped_token_data,
                                loaded=True)
    except (keystone_exceptions.Unauthorized,
            keystone_exceptions.Forbidden,
            keystone_exceptions.NotFound) as exc:
        msg = _('Invalid user name or password.')
        LOG.debug(exc.message)
        raise KeystoneAuthException(msg)
    except (keystone_exceptions.ClientException,
            keystone_exceptions.AuthorizationFailure) as exc:
        msg = _("An error occurred authenticating. "
                "Please try again later.")
        LOG.debug(exc.message)
        raise KeystoneAuthException(msg)

    # FIXME: Log in to default tenant when the Keystone API returns it...
    # For now we list all the user's tenants and iterate through.
    try:
        tenants = client.tenants.list()
    except (keystone_exceptions.ClientException,
            keystone_exceptions.AuthorizationFailure):
        msg = _('Unable to retrieve authorized projects.')
        raise KeystoneAuthException(msg)

    # Abort if there are no tenants for this user
    if not tenants:
        msg = _('You are not authorized for any projects.')
        raise KeystoneAuthException(msg)

    while tenants:
        tenant = tenants.pop()
        try:
            token = api.token_create_scoped(request,
                                            tenant.id,
                                            unscoped_token.id)
            break
        except (keystone_exceptions.ClientException,
                keystone_exceptions.AuthorizationFailure):
            token = None

    if token is None:
        msg = _("Unable to authenticate to any available projects.")
        raise KeystoneAuthException(msg)

    # If we made it here we succeeded. Create our User!
    user = create_user_from_token(request,
                                token,
                                endpoint)

    if request is not None:
        if is_ans1_token(unscoped_token.id):
            hashed_token = hashlib.md5(unscoped_token.id).hexdigest()
            unscoped_token._info['token']['id'] = hashed_token
        request.session['unscoped_token'] = unscoped_token.id
        request.user = user
        set_session_from_user(request, request.user)

    return unscoped_token


def set_user_admin_token(request):
    """
    Via admin account login again when admin token is expired.
    """
    from keystoneclient.v2_0 import client as keystone_client
    from keystoneclient import exceptions as keystone_exceptions
    from keystoneclient.v2_0.tokens import Token, TokenManager
    from openstack_auth.exceptions import KeystoneAuthException
    from openstack_auth.utils import is_ans1_token

    insecure = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
    endpoint = request.user.endpoint
    try:
        password = getattr(settings, 'OPENSTACK_ADMIN_TOKEN', 'admin')
        client = keystone_client.Client(username=u'admin',
                                        password=password,
                                        tenant_id='',
                                        auth_url=endpoint,
                                        insecure=insecure)

        unscoped_token_data = {"token": client.service_catalog.get_token()}
        unscoped_token = Token(TokenManager(None),
                                unscoped_token_data,
                                loaded=True)
    except (keystone_exceptions.Unauthorized,
            keystone_exceptions.Forbidden,
            keystone_exceptions.NotFound) as exc:
        msg = _('Invalid user name or password.')
        LOG.debug(exc.message)
        raise KeystoneAuthException(msg)
    except (keystone_exceptions.ClientException,
            keystone_exceptions.AuthorizationFailure) as exc:
        msg = _("An error occurred authenticating. "
                "Please try again later.")
        LOG.debug(exc.message)
        raise KeystoneAuthException(msg)

    # FIXME: Log in to default tenant when the Keystone API returns it...
    # For now we list all the user's tenants and iterate through.
    try:
        tenants = client.tenants.list()
    except (keystone_exceptions.ClientException,
            keystone_exceptions.AuthorizationFailure):
        msg = _('Unable to retrieve authorized projects.')
        raise KeystoneAuthException(msg)

    # Abort if there are no tenants for this user
    if not tenants:
        msg = _('You are not authorized for any projects.')
        raise KeystoneAuthException(msg)

    while tenants:
        tenant = tenants.pop()
        try:
            token = api.token_create_scoped(request,
                                            tenant.id,
                                            unscoped_token.id)
            break
        except (keystone_exceptions.ClientException,
                keystone_exceptions.AuthorizationFailure):
            token = None

    if token is None:
        msg = _("Unable to authenticate to any available projects.")
        raise KeystoneAuthException(msg)

    # If we made it here we succeeded. Create our User!
    user = create_user_from_token(request,
                                token,
                                endpoint)

    if request is not None:
        if is_ans1_token(unscoped_token.id):
            hashed_token = hashlib.md5(unscoped_token.id).hexdigest()
            unscoped_token._info['token']['id'] = hashed_token
        request.session['unscoped_token'] = unscoped_token.id
        request.user = user
        set_session_from_user(request, request.user)

    return user
