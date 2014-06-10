"""
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
"""

__author__ = 'tangjun'
__date__ = '2012-02-17'
__version__ = 'v2.0.1'

import logging
import re

from django.conf import settings
from django.forms import *
from django.utils.translation import ugettext_lazy as _

from dashboard.api.monitor import VoyageClient
from dashboard.node_manage.models import Node

if settings.DEBUG:
    __log__ = 'v2.0.1 create'

LOG = logging.getLogger(__name__)

class NodeForm(forms.Form):
    """
    node's form , with node Models
    uuid = models.CharField(max_length=50)
    name = models.CharField(max_length=30)
    ip = models.IPAddressField()
    password = models.CharField()
    type = models.CharField()
    created_at = models.DateTimeField()
    It will be changed into 'ModelForm' later.
    """
    host_name = ChoiceField(label=_("Name"), required=True)
    host_ip = IPAddressField(label=_("IP"), required=True)
    type = ChoiceField(label=_("Type"), required=True)
    real_ip = IPAddressField(required=False)
    #created_at = DateTimeField(label=_("created at"),required=True)

    def __init__(self, request, uuid, *args, **kwargs):
        super(NodeForm, self).__init__(*args, **kwargs)

        #add type choice
        action_type_choices = [('compute_node', _('compute_node')),
                               ('control_node', _('control_node'))
            , ('storage_node', _('storage_node'))]
        self.fields['type'].choices = action_type_choices
        self.uuid = uuid
        namechoices = []
        ipchoices = []
        nagios_hosts = VoyageClient().get_all_hosts(
            tenant_id=request.user.tenant_id,
            token=request.user.token.id)
        for host in nagios_hosts.get('hosts', []):
            if namechoices.count(
                (host['host']['name'], host['host']['name'])) < 1:
                namechoices.append((host['host']['name'], host['host']['name']))
                ipchoices.append((host['host']['name'], host['host']['address']))
        self.fields['host_name'].choices = namechoices
        self.fields['real_ip'].choices = ipchoices

    def clean(self):
        """
            Assure that the ip will be uniquely in the database
        """
        data = super(forms.Form, self).clean()
        host_ip = data['host_ip']
        host_name = data['host_name']
        if re.search(r'\s', host_name):
            raise ValidationError(_("no blank space allowed during node name"))

        try:
            namenode = Node.objects.get(name=host_name)
            if namenode.uuid != self.uuid:
                raise ValidationError(_("compute name has exist!"))
        except Node.DoesNotExist:
            LOG.info("compute name has not exist!")

        if host_ip:
            ip_pat = r'^(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|['\
                     r'0-1]?\d?\d)){3}'
            if re.match(ip_pat, host_ip):
                ip_list = re.split(r'\.', re.match(ip_pat, host_ip).group())
                ip_filter = []
                for ip in ip_list:
                    ip_filter.append(str(int(ip)))
                ip_filter = '.'.join(ip_filter)
                data['host_ip'] = ip_filter.decode()
            else:
                raise ValidationError(_("Please input correct IP Address!"))

        try:
            node = Node.objects.get(ip=host_ip)
            if node.uuid == self.uuid:
                return data
            else:
                raise ValidationError(_("IP has exist!"))

        except Node.DoesNotExist:
            return data









