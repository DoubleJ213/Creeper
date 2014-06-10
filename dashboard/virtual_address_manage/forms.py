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


__author__ = 'lishiquan'
__date__ = '2013-06-8'
__version__ = 'v2.0.9'

from django.conf import settings
if settings.DEBUG:
    __log__ = 'v2.0.9 create'

import logging
LOG = logging.getLogger(__name__)

#    code begin

from django.forms import *
from django import forms
from django.utils.translation import ugettext_lazy as _
from dashboard.exceptions import Unauthorized
from dashboard import api



class AllocateIPForm(forms.Form):
    """
    the form for Allocate IP
    """
    pool = ChoiceField(label = _("Ip pool") , required = True)
    tenant_id = CharField(label = _("Tenant Id") , max_length = 50)

    def __init__(self , request , *args , **kwargs):
        self.request = request
        super(AllocateIPForm , self).__init__(*args , **kwargs)
        try:
            pools = api.network.floating_ip_pools_list(self.request)
            if pools:
                pool_list = [(pool.id , pool.name)
                             for pool in api.network.floating_ip_pools_list(self.request)]
            else:
                pool_list = [(None , _("No floating IP pools available."))]

            self.fields['pool'].choices = pool_list
        except Unauthorized:
            raise

    def clean(self):
        data = super(forms.Form , self).clean()
        pool = data.get("pool" , None)
        if pool == None or 'None' == pool :
            msg = _('No floating IP pools available.')
            raise ValidationError(msg)

        return data


class AssociateIPForm(forms.Form):
    """
    the form for Associate a IP
    """
    floating_ip_id = forms.CharField(widget = forms.HiddenInput())
    floating_ip = forms.CharField(label = _("Floating IP"),
        widget = forms.TextInput(
            attrs = {'readonly': 'readonly'}))
    instance_id = forms.ChoiceField(label = _("Instance ID"))

    def __init__(self , request , ip_id , *args , **kwargs):
        self.request = request
        self.ip_id = ip_id
        super(AssociateIPForm , self).__init__(*args , **kwargs)

        try:
            ip_obj = api.tenant_floating_ip_get(self.request , ip_id)
        except Unauthorized:
            raise
        except Exception , exe:
            LOG.error('Unable to associate floating IP.The error is %s ' % exe.message )

        self.fields['floating_ip_id'].initial = ip_id
        self.fields['floating_ip'].initial = ip_obj.ip

        try:
            servers = api.server_list(self.request)
        except Unauthorized:
            raise
        except Exception , exe:
            LOG.error('Unable to retrieve instance list.The error is %s ' % exe.message )

        instances = []
        for server in servers:
            # to be removed when nova can support unique names
            server_name = server.name
            if any(s.id != server.id and
                   s.name == server.name for s in servers):
                # duplicate instance name
                server_name = "%s [%s]" % (server.name , server.id)
            instances.append((server.id , server_name))

        # Sort instances for easy browsing
        instances = sorted(instances , key = lambda x: x[1])
        if instances:
            instances.insert(0 , ("" , _("Select an instance")))
        else:
            instances = (("" , _("No instances available")) , )
        self.fields['instance_id'].choices = instances

    def clean(self):
        data = super(forms.Form, self).clean()
        instance_id = data.get("instance_id" , None)
        if instance_id == None or "" == instance_id :
            msg = _('Please select an instance.')
            raise ValidationError(msg)

        return data