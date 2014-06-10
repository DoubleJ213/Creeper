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

from django.forms import *
from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from dashboard import api
from dashboard.exceptions import Unauthorized

#    code begin

if settings.DEBUG:
    __log__ = 'v2.0.1 create'

LOG = logging.getLogger(__name__)

class CreateRoutersDetailForm(forms.Form):

    subnet_id = forms.ChoiceField(label = _("Subnet"), required = False)
    router_name = forms.CharField(max_length=10, min_length=2, label = _("Router Name"),
                                            widget = forms.TextInput(
                                            attrs = {'readonly': 'readonly'}))
    router_id = forms.CharField(label = _("Router ID"),
                                widget = forms.TextInput(
                                attrs = {'readonly': 'readonly'}))

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super(CreateRoutersDetailForm, self).__init__(*args, **kwargs)

        initials = kwargs.get("initial", {})
        self.fields['router_id'].initial = initials.get('router_id', 0)

        self.fields['router_name'].initial  = initials.get('router_name', 0)

        c = self.populate_subnet_id_choices(request)
        self.fields['subnet_id'].choices = c

    def populate_subnet_id_choices(self, request):
        tenant_id = self.request.user.tenant_id
        try:
            networks = api.quantum.network_list_for_tenant(request, tenant_id)

        except Unauthorized:
            raise
        except Exception , exc:
            msg = 'Failed to get network list %s' % exc.message
            LOG.error(msg)
            return

        choices = []
        for n in networks:
            net_name = n.name + ': ' if n.name else ''
            choices += [(subnet.id,
                         '%s%s (%s)' % (net_name, subnet.cidr,
                                        subnet.name or subnet.id))
                        for subnet in n['subnets']]
        if choices:
            choices.insert(0, ("", "Select Subnet"))
        else:
            choices.insert(0, ("", "No subnets available"))
        return choices

    def clean(self):
        data = super(forms.Form, self).clean()

        return data

class CreateGateWayForm(forms.Form):
    extNetwork = forms.ChoiceField(label = _("External Network"),
                                                    required = False)
    router_name = forms.CharField(label = _("Router Name"),
                                max_length = 10,
                                min_length = 2,
                                widget = forms.TextInput(
                                attrs = {'readonly': 'readonly'}))
    router_id = forms.CharField(label = _("Router ID"),
                                widget = forms.TextInput(
                                attrs = {'readonly': 'readonly'}))


    def __init__(self, request, *args, **kwargs):
        self.request = request
        super(CreateGateWayForm, self).__init__(*args, **kwargs)

        initials = kwargs.get("initial", {})
        self.fields['router_id'].initial = initials.get('router_id', 0)

        self.fields['router_name'].initial  = initials.get('router_name', 0)
        c = self.list_external_networks(request)

        self.fields['extNetwork'].choices = c

    def list_external_networks(self, request):
        ext_net_name = []
        try:
            search_opts = {'router:external': True}
            ext_nets = api.quantum.network_list(request, **search_opts)
            for ext_net in ext_nets:
                ext_net.set_id_as_name_if_empty()
                ext_net_name += [(ext_net._apidict["id"],
                                  ext_net._apidict["name"])]

            if ext_net_name:
                ext_net_name.insert(0, ("", "Select network"))
            else:
                ext_net_name.insert(0, ("", "No network available"))
        except Unauthorized:
            raise
        except Exception , exc:
            msg = 'Unable to retrieve a list of external networks "%s".' % exc.message
            LOG.error(msg)
        return ext_net_name

    def clean(self):
        data = super(forms.Form, self).clean()

        return data


class CreateRouterForm(forms.Form):
    name = forms.CharField(label = _("Router Name"),
        max_length = 10,
        min_length = 2
    )

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super(CreateRouterForm, self).__init__(*args, **kwargs)

    def clean(self):
        data = super(forms.Form, self).clean()
        if re.search(r'\s', data['name']):
            raise ValidationError(_("no blank space allowed during router name"))
        return data