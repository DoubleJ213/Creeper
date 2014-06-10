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


__author__ = 'zhao lei'
__date__ = '2013-03-14'
__version__ = 'v2.0.1'

import logging
import re

from django.conf import settings
from django.forms import *
from django import forms
from django.utils.translation import ugettext_lazy as _

from dashboard import api
from dashboard.authorize_manage.utils import switch_tenants
from dashboard.utils.validators import validate_port_range, validate_ipv4_cidr
from dashboard.exceptions import Unauthorized

if settings.DEBUG:
    __log__ = 'v2.0.1 create'

LOG = logging.getLogger(__name__)

#    code begin
ICMP_MIN = -1
ICMP_MAX = 256

NOT_ICMP_MIN = 1
NOT_ICMP_MAX = 65536

class CreateSecurityGroupForm(forms.Form):
    """
    the form for creating a SecurityGroup
    """
    name = CharField(label=_("Security Group Name"), max_length=10, min_length=2)
    description = CharField(label=_("Description"), max_length=50, min_length=6)
    tenant_id = CharField(label=_("Tenant Id"), max_length=50)

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super(CreateSecurityGroupForm, self).__init__(*args, **kwargs)

    def clean(self):
        data = super(forms.Form, self).clean()
        try:
            switch_tenants(self.request, data['tenant_id'])
            securitygroups = api.security_group_list(self.request)
        except Unauthorized:
            raise
        except Exception, ex:
            LOG.error(ex)

        if 'name' in data:
            if re.search(r'\s', data['name']):
                raise ValidationError(_("no blank space allowed during security group name"))
            for index in range(len(securitygroups)):
                if data['name'] == getattr(securitygroups[index], 'name',
                    'unknown'):
                    msg = 'Security Group Name has exist.'
                    raise ValidationError(_(msg))
                if re.search(r'\s', data['name']):
                    raise ValidationError(_("no blank space allowed during security group name"))
        return data


class CreateSecurityGroupRuleForm(forms.Form):
    """
    the form for creating a SecurityGroup
    """
    ip_protocol = forms.ChoiceField(label=_('IP Protocol'),
        choices=[('tcp', 'TCP'),
                 ('udp', 'UDP'),
                 ('icmp', 'ICMP')],
        widget=forms.Select(attrs={'class':
                                       'switchable'}))

    port_or_range = forms.ChoiceField(label=_('Open'),
        choices=[('port', _('Port')),
                 ('range', _('Port Range'))],
        widget=forms.Select(attrs={
            'class': 'switchable'}))

    from_port = forms.IntegerField(label=_("From Port"),
        required=False,
        help_text=_("TCP/UDP: Enter integer value "
                           "between 1 and 65535. ICMP: "
                           "enter a value for ICMP type "
                           "in the range (-1: 255)"),
        widget=forms.TextInput(
            attrs={'data': _('From Port'),
                   'data-icmp': _('Type')}),
        validators=[validate_port_range])
    to_port = forms.IntegerField(label=_("To Port"),
        help_text=_("TCP/UDP: Enter integer value "
                           "between 1 and 65535. ICMP: "
                           "enter a value for ICMP code "
                           "in the range (-1: 255)"),
        widget=forms.TextInput(
            attrs={'data': _('To Port'),
                   'data-icmp': _('Code')}),
        validators=[validate_port_range])

    source_group = forms.ChoiceField(label=_('Source Group'), required=False)
    cidr = forms.CharField(label=_("CIDR"),
        required=False,
        initial="0.0.0.0/0",
        help_text=_("Classless Inter-Domain Routing "
                           "(e.g. 192.168.0.0/24)"),
        validators=[validate_ipv4_cidr])

    security_group_id = forms.CharField(widget=forms.HiddenInput())

    source = forms.ChoiceField(label=_('Source'),
        choices=[('cidr', _('CIDR')),
                 ('sg', _('Security Group'))],
        help_text=_('To specify an allowed IP '
                    'range, select "CIDR". To '
                    'allow access from all '
                    'members of another security '
                    'group select "Security '
                    'Group".'),
        widget=forms.Select(attrs={
            'class': 'switchable'}))

    def __init__(self, request, *args, **kwargs):
        super(CreateSecurityGroupRuleForm, self).__init__(*args, **kwargs)
        initials = kwargs.get("initial", {})
        current_group_id = initials.get('security_group_id', 0)
        security_groups = initials.get('security_group_list', [])
        group_choices = [s for s in security_groups
                         if str(s[0]) != current_group_id]
        self.fields['source_group'].choices = group_choices

    def clean(self):
        data = super(forms.Form, self).clean()
        from_port = data.get("from_port", None)
        to_port = data.get("to_port", None)
        cidr = data.get("cidr", None)
        ip_proto = data.get("ip_protocol", None)
        source_group = data.get("source_group", None)
        port_or_range = data.get("port_or_range", None)
        source = data.get("source", None)

        if ip_proto == 'icmp':
            if from_port == None:
                msg = _('The ICMP type is invalid.')
                raise ValidationError(msg)
            if to_port == None:
                msg = _('The ICMP code is invalid.')
                raise ValidationError(msg)
            if from_port < ICMP_MIN and from_port > ICMP_MAX:
                msg = _('The ICMP type not in range (-1, 255)')
                raise ValidationError(msg)
            if to_port < ICMP_MIN and to_port > ICMP_MAX:
                msg = _('The ICMP code not in range (-1, 255)')
                raise ValidationError(msg)
        else:
            if port_or_range == "port":
                data['from_port'] = to_port
                from_port = to_port
                if to_port == None:
                    msg = _('The specified port is invalid.')
                    raise ValidationError(msg)
                if to_port < NOT_ICMP_MIN and to_port > NOT_ICMP_MAX:
                    msg = _('The port number not in range (1, 65535)')
                    raise ValidationError(msg)

            if from_port == None:
                msg = _('The from port number is invalid.')
                raise ValidationError(msg)
            if to_port == None:
                msg = _('The to port number is invalid.')
                raise ValidationError(msg)
            if from_port < NOT_ICMP_MIN and from_port > NOT_ICMP_MAX:
                msg = _('The from port number not in range (1, 65535)')
                raise ValidationError(msg)
            if to_port < NOT_ICMP_MIN and to_port > NOT_ICMP_MAX:
                msg = _('The to port number not in range (1, 65535)')
                raise ValidationError(msg)
            if to_port < from_port:
                msg = _(
                    'The to port number must be greater than or equal to the "from" port number.')
                raise ValidationError(msg)

        if source == "cidr":
            data['source_group'] = None
        else:
            data['cidr'] = None

        return data


class AllocateIPForm(forms.Form):
    """
    the form for creating a SecurityGroup
    """
    pool = ChoiceField(label=_("Ip pool"), required=True)
    tenant_id = CharField(label=_("Tenant Id"), max_length=50)

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super(AllocateIPForm, self).__init__(*args, **kwargs)
        try:
            pools = api.network.floating_ip_pools_list(self.request)

            if pools:
                pool_list = [(pool.id, pool.name)
                             for pool in
                             api.network.floating_ip_pools_list(self.request)]
            else:
                pool_list = [
                    (None, _("No floating IP pools available."))]
        except Unauthorized:
            raise
        except Exception, ex:
            LOG.error(ex)

        self.fields['pool'].choices = pool_list

    def clean(self):
        data = super(forms.Form, self).clean()
        pool = data.get("pool", None)
        if pool == None or 'None' == pool:
            msg = _('No floating IP pools available.')
            raise ValidationError(msg)

        return data


class AssociateIPForm(forms.Form):
    """
    the form for creating a SecurityGroup
    """
    floating_ip_id = forms.CharField(widget=forms.HiddenInput())
    floating_ip = forms.CharField(label=_("Floating IP"),
        widget=forms.TextInput(
            attrs={'readonly': 'readonly'}))
    instance_id = forms.ChoiceField(label=_("Instance ID"))

    def __init__(self, request, ip_id, *args, **kwargs):
        self.request = request
        self.ip_id = ip_id
        super(AssociateIPForm, self).__init__(*args, **kwargs)

        #        ip_id = int(ip_id)
        try:
            ip_obj = api.tenant_floating_ip_get(self.request, ip_id)
        except Exception, ex:
            msg = 'Unable to associate floating IP. The error is %s' % ex
            LOG.error(msg)

        self.fields['floating_ip_id'].initial = ip_id
        self.fields['floating_ip'].initial = ip_obj.ip

        try:
            servers = api.server_list(self.request)
        except Unauthorized:
            raise
        except Exception, ex:
            msg = 'Unable to retrieve instance list. The error is %s' % ex
            LOG.error(msg)
        instances = []
        for server in servers:
            # to be removed when nova can support unique names
            server_name = server.name
            if any(s.id != server.id and
                   s.name == server.name for s in servers):
                # duplicate instance name
                server_name = "%s [%s]" % (server.name, server.id)
            instances.append((server.id, server_name))

        # Sort instances for easy browsing
        instances = sorted(instances, key=lambda x: x[1])
        if instances:
            instances.insert(0, ("", _("Select an instance")))
        else:
            instances = (("", _("No instances available")),)
        self.fields['instance_id'].choices = instances

    def clean(self):
        data = super(forms.Form, self).clean()
        instance_id = data.get("instance_id", None)
        if instance_id == None or "" == instance_id:
            msg = _('Please select an instance.')
            raise ValidationError(msg)

        return data