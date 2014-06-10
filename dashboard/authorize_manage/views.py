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
__date__ = '2012-01-24'
__version__ = 'v2.0.1'

from django.conf import settings

if settings.DEBUG:
    __log__ = 'v2.0.1 create'

import datetime
import json
import subprocess
import threading
import logging
LOG = logging.getLogger(__name__)

#    code begin

from django import shortcuts
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.views import (login as django_login,
                                       logout_then_login as django_logout)
from django.contrib import messages
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.utils import translation
from django.utils.datastructures import SortedDict
from django.utils.functional import curry
from django.utils.translation import ugettext_lazy as _
from django.views.decorators import vary
from django.views.decorators.http import require_GET, require_POST

from openstack_auth.user import set_session_from_user

from dashboard import api
from dashboard.authorize_manage.utils import get_user_role_name
from dashboard.instance_manage.models import Distribution
from dashboard.instance_manage.utils import get_authorized_instances
from dashboard.instance_manage.views import instance_power_state
from dashboard.utils import start_thread
from dashboard.utils import Pagenation

from .forms import Login


_hardware_id = ''
has_permit = False
permit_lock = threading.Lock()


def get_hardware_id():
    global _hardware_id

    if not _hardware_id:
        f = subprocess.Popen([settings.SERIAL_BIN], stdout=subprocess.PIPE).stdout
        _hardware_id = f.read()
        f.close()

    return _hardware_id


def str2date(date_str):
    return datetime.date(*map(lambda x: int(x), date_str.split('-')))


def validate_quotas_json(quotas):
    try:
        str2date(quotas.get('ExpireTime'))
        int(quotas.get('NodeMaxNum'))
        int(quotas.get('ProjectMaxNum'))
        int(quotas.get('UserMaxNum'))
        int(quotas.get('InstanceMaxNum'))
        int(quotas.get('PerInstanceBakMaxNum'))
        int(quotas.get('Is_InstanceLiveMigrate'))
        int(quotas.get('Is_InstanceFlavorResize'))
        int(quotas.get('ImageMaxNum'))
        int(quotas.get('Is_CustomImage'))
        int(quotas.get('VolumeMaxNum'))
        int(quotas.get('VolumeSnapshotMaxNum'))
        int(quotas.get('SoftwareMaxNum'))
        int(quotas.get('VirtualNetworkMaxNum'))
        int(quotas.get('PerVirtualNetworkSubnetMaxNum'))
        int(quotas.get('RouterMaxNum'))
        int(quotas.get('PerRouterInterfaceMaxNum'))
        int(quotas.get('FloatingIPsMaxNum'))
#        int(quotas.get('ProjectQuotas').get('MetadataItems'))
#        int(quotas.get('ProjectQuotas').get('InjectedFiles'))
#        int(quotas.get('ProjectQuotas').get('InjectedFileBytes'))
        int(quotas.get('ProjectQuotas').get('VCPUs'))
        int(quotas.get('ProjectQuotas').get('Instances'))
        int(quotas.get('ProjectQuotas').get('DiskNum'))
        int(quotas.get('ProjectQuotas').get('DiskVolume'))
        int(quotas.get('ProjectQuotas').get('RAM'))
        int(quotas.get('ProjectQuotas').get('FloatingIPs'))
#        int(quotas.get('ProjectQuotas').get('FixedIPs'))
        int(quotas.get('ProjectQuotas').get('SecurityGroups'))
        int(quotas.get('ProjectQuotas').get('SecurityGroupRules'))
        int(quotas.get('FlavorQuotas').get('VCPUs'))
        int(quotas.get('FlavorQuotas').get('Memory'))
        int(quotas.get('FlavorQuotas').get('RootDisk'))
        int(quotas.get('FlavorQuotas').get('EphemeralDisk'))
        return True
    except:
        raise ValueError


# Use threading.Lock outer
def validate_permit(request, license_file=settings.LICENSE_FILE):
    global has_permit

    try:
        with open(settings.SERIAL_FILE, 'w') as f:
            f.write(get_hardware_id())

        f = subprocess.Popen([settings.DECRYPT_BIN,
                              settings.SERIAL_FILE,
                              license_file], stdout=subprocess.PIPE).stdout
        json_str = f.read()
        f.close()

        if 'Error' in json_str:
            return False
    except Exception, e:
        LOG.error(e)
        return False

    try:
        quotas = json.loads(json_str)
        if not validate_quotas_json(quotas):
            raise ValueError
    except ValueError:
        messages.error(request, _('License Not Valid!'))
        return False

    if not cache.set('CreeperQuotas', quotas):
        messages.error(request, _('License Load Error. Please try again later.'))
        return False

    has_permit = True
    return True


@start_thread
@vary.vary_on_cookie
@require_GET
def get_login_view(request):
    if not has_permit:
        with permit_lock:
            if not validate_permit(request):
                return shortcuts.redirect('get_permit_view')

    if request.user.is_authenticated():
        is_zh = True
        if request.LANGUAGE_CODE.lower().find('zh') == -1:
            is_zh = False
        return shortcuts.render(request, 'common/index.html',
                                {'username': request.user.username,
                                 'role': get_user_role_name(request),
                                 'is_admin': request.user.is_superuser,
                                 'language': is_zh})

    form = Login()
    request.session.clear()
    request.session.set_test_cookie()
    return shortcuts.render(request,
                            'authorize/splash.html',
                            {'form': form,
                             'next': request.GET.get('next', '')})


@vary.vary_on_cookie
@require_GET
def get_permit_view(request):
    expire_time = None
    can_use = False

    quotas = cache.get('CreeperQuotas')
    if quotas:
        today = datetime.date.today()
        expire_time = str2date(quotas.get('ExpireTime'))
        if today <= expire_time:
            can_use = True

    return shortcuts.render(request, 'authorize/permit.html',
                            {'hardware_id': get_hardware_id(),
                             'expire_time': expire_time,
                             'can_use': can_use})


@vary.vary_on_cookie
@require_GET
def show_permit_tips(request):
    return shortcuts.render(request, 'authorize/expire_permit.html')


@vary.vary_on_cookie
@require_POST
def authorize_permit(request):
    license_data = request.POST.get('license', '')
    if license_data:
        with permit_lock:
            with open(settings.LICENSE_TMP_FILE, 'w') as f:
                f.write(license_data)

            if not validate_permit(request, settings.LICENSE_TMP_FILE):
                return shortcuts.redirect('get_permit_view')

            with open(settings.LICENSE_FILE, 'w') as f:
                f.write(license_data)

    return shortcuts.redirect('get_login_view')


@vary.vary_on_cookie
@require_POST
def authorize_login(request):
    initial = {}
    login_url = 'get_login_view'

    if request.method == "POST":
        form = curry(Login, request)
    else:
        form = curry(Login, initial=initial)

    extra_context = {'redirect_field_name': REDIRECT_FIELD_NAME}

    if request.is_ajax():
        template_name = 'auth/_login.html'
        extra_context['hide'] = True
    else:
        template_name = login_url

    django_login(request,
                template_name=login_url,
                authentication_form=form,
                extra_context=extra_context)

    if request.user.is_authenticated():
        set_session_from_user(request, request.user)

    redirect = request.POST.get('next', None) or login_url
    return shortcuts.redirect(redirect)


@require_GET
def authorize_logout(request):
    django_logout(request)
    request.user_logout()

    # FIXME(gabriel): we don't ship a view named splash
    return shortcuts.redirect('get_login_view')


@start_thread
@vary.vary_on_cookie
@require_GET
def get_login_client_view(request):
    form = Login()
    request.session.clear()
    translation.activate('zh')
    request.LANGUAGE_CODE = 'zh'
    request.session.set_test_cookie()
    return shortcuts.render(request,
                            'authorize/client_splash.html',
                            {'form': form,
                             'next': request.GET.get('next', '')})


@require_GET
@Pagenation('common/client_index.html')
def get_client_instances(request):
    translation.activate('zh')
    request.LANGUAGE_CODE = 'zh'
    args = {}
    authorized_tenants = request.user.authorized_tenants
    instances = []

    if authorized_tenants:
        for tenant in authorized_tenants:
            if not tenant.enabled:
                continue
            instances.extend(get_authorized_instances(request, tenant.id) or [])

        try:
            flavors = api.nova.flavor_list(request)
        except Exception, e:
            flavors = []
            LOG.error('Unable to retrieve instance size information. %s' % e)

        full_flavors = SortedDict([(f.id, f) for f in flavors])

        _relationship = []
        filter_instances = []
        try:
            _relationship = Distribution.objects.filter(user_id=request.user.id)
        except Exception, e:
            LOG.error('Error: %s' % e)

        for relationship in _relationship:
            for inst in instances:
                if inst.id == relationship.instance_id:
                    filter_instances.append(inst)
                    break

        tenant_dict = SortedDict([(t.id, t) for t in authorized_tenants])
        num = 0

        for inst in filter_instances:
            tenant = tenant_dict.get(inst.tenant_id, None)
            inst.tenant_name = getattr(tenant, "name", None)
            inst.full_flavor = full_flavors.get(inst.flavor["id"], None)
            setattr(inst, 'task', getattr(inst,'OS-EXT-STS:task_state', 'None'))
            setattr(inst, 'host', getattr(inst,'OS-EXT-SRV-ATTR:host', 'None'))

            instance_power_state(inst)

            setattr(inst, "status_link", reverse('get_client_instance_status', args=[inst.tenant_id, inst.id]))
            setattr(inst, "task_link", reverse('get_client_instance_task', args=[inst.tenant_id, inst.id]))
            setattr(inst, "power_link", reverse('get_client_instance_power', args=[inst.tenant_id, inst.id]))
            setattr(inst, "rebooturl", reverse('reboot_instance_client', args=[inst.tenant_id, inst.id]))
            setattr(inst, "stopurl", reverse('stop_instance_client', args=[inst.tenant_id, inst.id]))
            setattr(inst, "unstopurl", reverse('unstop_instance_client', args=[inst.tenant_id, inst.id]))
            setattr(inst, "gtkurl", reverse('get_instance_gtk_client', args=[inst.tenant_id, inst.id]))
            num += 1
            setattr(inst, "num", num)
            setattr(inst, "numtype", num%2)

        args['list'] = []
        args['instances'] = filter_instances
        args["username"] = request.user.username
        args["is_admin"] = request.user.is_superuser
        return args
    else:
        args['list'] = []
        return args


@vary.vary_on_cookie
@require_POST
def authorize_client_login(request):
    login_url = 'get_login_client_view'
    translation.activate('zh')
    request.LANGUAGE_CODE = 'zh'
    form = curry(Login, request)
    extra_context = {'redirect_field_name': REDIRECT_FIELD_NAME}

    django_login(request,
                template_name=login_url,
                authentication_form=form,
                extra_context=extra_context)

    if request.user.is_authenticated():
        set_session_from_user(request, request.user)
        return shortcuts.redirect('get_client_instances')
    else:
        return shortcuts.redirect(login_url)


@require_GET
def authorize_client_logout(request):
    request.user_logout()
    return shortcuts.redirect('get_login_client_view')
