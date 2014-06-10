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


__author__ = 'zhaolei'
__date__ = '2013-06-13'
__version__ = 'v2.0.9'


import logging
import netaddr
import re

from django.forms import *
from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from dashboard import api
from dashboard.exceptions import Unauthorized

#    code begin
if settings.DEBUG:
    __log__ = 'v2.0.9 create'

LOG = logging.getLogger(__name__)

class CreateNetwork(forms.Form):
    """
        the form for create a network
    """
    name = forms.CharField(max_length = 10,
        min_length = 2,
        label = _("Name") ,
        required = False)
    tenant_id = forms.CharField(label = _("Project"))
    admin_state = forms.BooleanField(label = _("Admin State") ,
        initial = True , required = False)
    shared = forms.BooleanField(label = _("Shared"),
        initial = False , required = False)
    external = forms.BooleanField(label = _("External Network"),
        initial = False, required = False)

    def __init__(self , request,tenant_id , *args , **kwargs):
        super(CreateNetwork, self).__init__(*args, **kwargs)
        self.tenant_id = tenant_id
        self.request = request

    def clean(self):
        data = super(forms.Form, self).clean()
        network_name = data.get('name')
        #check name space
        if re.search(r'\s', network_name):
            raise ValidationError(_("no blank space allowed during network name"))

        try:
            networklist = api.quantum.network_list_for_tenant(self.request, self.tenant_id)
        except Unauthorized:
            raise
        except Exception as exe:
            LOG.error('Failed to network list,the error is %s' % exe.message)

        if networklist:
            for network in networklist:
                if network.name == network_name:
                    raise ValidationError(_("network name  has exist."))
        return data


class UpdateNetwork(forms.Form):
    """
        the form for update a network
    """
    name = forms.CharField(max_length = 10,
        min_length = 2,
        label = _("Name"),
        required = False)
    tenant_id = forms.CharField(label = _("Project"))

    network_id = forms.CharField(label = _("ID"),
        widget = forms.TextInput(
            attrs = {'readonly': 'readonly'}))
    admin_state = forms.BooleanField(label = _("Admin State"),
        initial = True, required = False)
    shared = forms.BooleanField(label = _("Shared"),
        initial = False, required = False)
    external = forms.BooleanField(label = _("External Network"),
        initial = False, required = False)

    def __init__(self, request , tenant_id , network_id ,*args, **kwargs):
        super(UpdateNetwork, self).__init__(*args, **kwargs)
        self.tenant_id = tenant_id
        self.network_id = network_id
        self.request = request

    def clean(self):

        data = super(forms.Form, self).clean()
        network_name = data.get('name')
        #check name space
        if re.search(r'\s', network_name):
            raise ValidationError(_("no blank space allowed during network name"))
        try:
            networklist = api.quantum.network_list_for_tenant(self.request, self.tenant_id)
        except Unauthorized:
            raise
        except Exception as exe:
            LOG.error('Failed to network list,the error is %s' % exe.message)

        if networklist:
            for network in networklist:
                if network.name == network_name and network.id != self.network_id :
                    raise ValidationError(_("network name  has exist."))
        return data

def check_subnet_data(cleaned_data, is_create=True):
    cidr = cleaned_data.get('cidr')
    ip_version = int(cleaned_data.get('ip_version'))
    gateway_ip = cleaned_data.get('gateway_ip')
    no_gateway = cleaned_data.get('no_gateway')
    if not cidr:
        msg = _("Specify 'Network Address'.")
        raise forms.ValidationError(msg)
    if cidr:
        try:
            subnet = netaddr.IPNetwork(cidr)
            ip_bits = subnet.ip.bits("")
            ip_bits_suffix = int(ip_bits[subnet.prefixlen:])
        except Exception, exe:
            LOG.error("Network address in CIDR format (e.g. 192.168.0.0/24),the error is %s " % exe.message )
            msg = _("")
            raise forms.ValidationError(_('Network address in CIDR format (e.g. 192.168.0.0/24)'))
        if subnet.version != ip_version:
            msg = _('Network Address and IP version are inconsistent.')
            raise forms.ValidationError(msg)
        if (ip_bits_suffix != 0):
            msg = _("The cidr's suffix part should all be 0. (e.g. *.*.*.*/24, the last 8 bits should be '00000000')")
            raise forms.ValidationError(msg)
        if (ip_version == 4 and subnet.prefixlen == 32) or\
           (ip_version == 6 and subnet.prefixlen == 128):
            msg = _("The subnet in the Network Address is too small.")
            raise forms.ValidationError(msg)

        cleaned_data['cidr']="%s/%d" % (subnet.ip, subnet.prefixlen)

    if not no_gateway and gateway_ip:
        try:
            if ip_version == 4:
                addr = '.'.join(['%d' % int(i) for i in gateway_ip.split('.')])
                gateway_ip_obj = netaddr.IPAddress(addr)
            else:
                gateway_ip_obj = netaddr.IPAddress(gateway_ip)
            if gateway_ip_obj.version is not ip_version:
                msg = _('Gateway IP and IP version are inconsistent.')
                raise forms.ValidationError(msg)
            if gateway_ip_obj <= subnet.ip or gateway_ip_obj > subnet.broadcast:
                msg = _('Gateway IP not in Subnet CIDR.')
                raise forms.ValidationError(msg)
        except Exception, exe:
            LOG.error("Gateway IP is error,the error is %s " % exe.message )
            raise forms.ValidationError(_('Gateway IP is error.'))

        cleaned_data['gateway_ip']="%s" % (gateway_ip_obj)

    if not is_create and not no_gateway and not gateway_ip:
        msg = _('Specify IP address of gateway or '
                       'check "Disable Gateway".')
        raise forms.ValidationError(msg)

def convert_ip_address(ip, field_name):
    try:
        return netaddr.IPAddress(ip)
    except (netaddr.AddrFormatError, ValueError):
        msg = _('%(field_name)s: Invalid IP address '
                       '(value=%(ip)s)') % locals()
        raise forms.ValidationError(msg)

def convert_ip_network(network, field_name):
    try:
        return netaddr.IPNetwork(network)
    except (netaddr.AddrFormatError, ValueError):
        msg = _('%(field_name)s: Invalid IP address '
                       '(value=%(network)s)') % locals()
        raise forms.ValidationError(msg)

def check_allocation_pools(cleaned_data):
    try:
        allocation_pools = cleaned_data.get('allocation_pools')
        ip_version = int(cleaned_data.get('ip_version'))
        pools = ''
        for p in allocation_pools.split('\n'):
            p = p.strip()
            if not p:
                continue
            pool = p.split(',')
            if len(pool) != 2:
                msg = _('Start and end addresses must be specified')
                raise forms.ValidationError(msg)
            if ip_version == 4:
                startandend = []
                for ip in pool:
                    addr = '.'.join(['%d' % int(i) for i in ip.split('.')])
                    ipaddr = convert_ip_address(addr, _("Allocation Pools"))
                    startandend.append(ipaddr)
                start, end = startandend
            else:
                start, end = [convert_ip_address(ip, _("Allocation Pools"))
                              for ip in pool]
            if start > end:
                msg = _('Start address is larger than end address')
                raise forms.ValidationError(msg)
            pools = pools +"%s,%s" % (start, end) +'\n'
        cleaned_data['allocation_pools'] = pools
    except Exception,exe:
        LOG.error("allocation_pools is error,the error is %s " % exe.message )
        raise forms.ValidationError(_('allocation pools is error.'))

def check_dns_nameservers(cleaned_data):
    try:
        dns_nameservers = cleaned_data.get('dns_nameservers')
        ip_version = int(cleaned_data.get('ip_version'))
        dnsservers = ''
        for ns in dns_nameservers.split('\n'):
            ns = ns.strip()
            if not ns:
                continue
            if ip_version == 4:
                addr = '.'.join(['%d' % int(i) for i in ns.split('.')])
                dns_nameserve = convert_ip_address(addr, _("Host Routes"))
            else:
                dns_nameserve = convert_ip_address(ns, _("DNS Name Servers"))
            dnsservers = dnsservers +'%s' % dns_nameserve +'\n'
        cleaned_data['dns_nameservers'] = dnsservers
    except Exception,exe:
        LOG.error("dns is error,the error is %s " % exe.message )
        raise forms.ValidationError(_('DNS is error.'))

def check_host_routes(cleaned_data):
    try:
        host_routes = cleaned_data.get('host_routes')
        ip_version = int(cleaned_data.get('ip_version'))
        routes=''
        for r in host_routes.split('\n'):
            r = r.strip()
            if not r:
                continue
            route = r.split(',')
            if len(route) != 2:
                msg = _('Host Routes format error: '
                               'Destination CIDR and nexthop must be specified '
                               '(value=%s)') % r
                raise forms.ValidationError(msg)
            routecidr = convert_ip_network(route[0], _("Host Routes"))
            routecidrstr = "%s/%d" % (routecidr.ip, routecidr.prefixlen)
            if ip_version == 4:
                addr = '.'.join(['%d' % int(i) for i in route[1].split('.')])
                routenexthop = convert_ip_address(addr, _("Host Routes"))
            else:
                routenexthop = convert_ip_address(route[1], _("Host Routes"))
            routes = routes +"%s,%s" % (routecidrstr , routenexthop) + '\n'
        cleaned_data['host_routes'] = routes
    except Exception,exe:
        LOG.error("dns is error,the error is %s " % exe.message )
        raise forms.ValidationError(_('routes is error.'))



class CreateSubnet(forms.Form):
    """
        the form for create a subnet
    """
    subnet_name = forms.CharField(max_length = 10,
        min_length = 2,
        label = _("Subnet Name"),
        help_text = _("Subnet Name"),
        required = True)

    cidr = fields.CharField(label = _("Network Address"),
        required = False,
        initial = "",
#        help_text = _("Network address in CIDR format "
#                    "(e.g. 192.168.0.0/24)"))
        help_text = _("Network address in CIDR format (e.g. 192.168.0.0/24),"
                      "and the cidr suffix part should all be 0. "
                      "(e.g. *.*.*.*/24, the last 8 bits should be '*.*.*.00000000')"))

    ip_version = forms.ChoiceField(choices = [(4, 'IPv4'), (6, 'IPv6')],
        label = _("IP Version"))

    gateway_ip = fields.CharField(
        label = _("Gateway IP"),
        required = False,
        initial = "",
        help_text = _("IP address of Gateway (e.g. 192.168.0.254) "
                    "The default value is the first IP of the "
                    "network address (e.g. 192.168.0.1 for "
                    "192.168.0.0/24). "
                    "If you use the default, leave blank. "
                    "If you want to use no gateway, "
                    "check 'Disable Gateway' below."))

    no_gateway = forms.BooleanField(label = _("Disable Gateway"),
        initial = False, required = False)

    enable_dhcp = forms.BooleanField(label = _("Enable DHCP"),
        initial = True, required = False)

    allocation_pools = forms.CharField(
        widget = forms.Textarea(),
        label = _("Allocation Pools"),
        help_text = _("IP address allocation pools. Each entry is "
                      "<start_ip_address>,<end_ip_address> "
                      "(e.g., 192.168.1.100,192.168.1.120) "
                      "and one entry per line."),
        required = False)

    dns_nameservers = forms.CharField(
        widget = forms.widgets.Textarea(),
        label = _("DNS Name Servers"),
        help_text = _("IP address list of DNS name servers for this subnet. "
                    "One entry per line."),
        required = False)

    host_routes = forms.CharField(
        widget = forms.widgets.Textarea(),
        label = _("Host Routes"),
        help_text = _("Additional routes announced to the hosts. "
                      "Each entry is <destination_cidr>,<nexthop> "
                      "(e.g., 192.168.200.0/24,10.56.1.254)"
                      "and one entry per line."),
        required = False)

    def __init__(self, request , network_id , *args, **kwargs):
        super(CreateSubnet, self).__init__(*args, **kwargs)
        self.network_id = network_id
        self.request = request

    def clean(self):
        cleaned_data = super(CreateSubnet, self).clean()
        check_subnet_data(cleaned_data)
        check_allocation_pools(cleaned_data)
        check_host_routes(cleaned_data)
        check_dns_nameservers(cleaned_data)
        subnet_name = cleaned_data.get('subnet_name')
        #check name space
        if subnet_name and re.search(r'\s', subnet_name):
            raise ValidationError(_("no blank space allowed during subnet name"))
        try:
            subnets = api.quantum.subnet_list(self.request,
                network_id = self.network_id)
        except Unauthorized:
            raise
        except Exception as exe:
            LOG.error('Failed to subnet list,the error is %s' % exe.message)

        if subnets:
            for subnet in subnets:
                if subnet_name and subnet.name == subnet_name:
                    raise ValidationError(_("subnet name  has exist."))
        return cleaned_data



class UpdateSubnet(forms.Form):
    """
        the form for create a subnet
    """
    subnet_name = forms.CharField(max_length = 10,
        min_length = 2,
        label = _("Subnet Name"),
        help_text = _("Subnet Name"),
        required = True)

    cidr = fields.CharField(label = _("Network Address"),
        required = False,
        initial = "",
        help_text = _("Network address in CIDR format "
                             "(e.g. 192.168.0.0/24)"))

    ip_version = forms.ChoiceField(choices = [(4, 'IPv4'), (6, 'IPv6')],
        label = _("IP Version"))

    gateway_ip = fields.CharField(
        label = _("Gateway IP"),
        required = False,
        initial = "",
        help_text = _("IP address of Gateway (e.g. 192.168.0.254) "
                             "The default value is the first IP of the "
                             "network address (e.g. 192.168.0.1 for "
                             "192.168.0.0/24). "
                             "If you use the default, leave blank. "
                             "If you want to use no gateway, "
                             "check 'Disable Gateway' below."))

    no_gateway = forms.BooleanField(label = _("Disable Gateway"),
        initial = False, required = False)

    enable_dhcp = forms.BooleanField(label = _("Enable DHCP"),
        initial = True, required = False)

    allocation_pools = forms.CharField(
        widget = forms.Textarea(),
        label = _("Allocation Pools"),
        help_text = _("IP address allocation pools. Each entry is "
                      "<start_ip_address>,<end_ip_address> "
                      "(e.g., 192.168.1.100,192.168.1.120) "
                      "and one entry per line."),
        required = False)

    dns_nameservers = forms.CharField(
        widget = forms.widgets.Textarea(),
        label = _("DNS Name Servers"),
        help_text = _("IP address list of DNS name servers for this subnet. "
                             "One entry per line."),
        required = False)

    host_routes = forms.CharField(
        widget = forms.widgets.Textarea(),
        label = _("Host Routes"),
        help_text = _("Additional routes announced to the hosts. "
                      "Each entry is <destination_cidr>,<nexthop> "
                      "(e.g., 192.168.200.0/24,10.56.1.254)"
                      "and one entry per line."),
        required = False)

    def __init__(self, request, subnet_id , *args, **kwargs):
        super(UpdateSubnet, self).__init__(*args, **kwargs)
        self.subnet_id = subnet_id
        self.request = request

    def clean(self):
        cleaned_data = super(UpdateSubnet, self).clean()
        check_subnet_data(cleaned_data)
        check_allocation_pools(cleaned_data)
        check_host_routes(cleaned_data)
        check_dns_nameservers(cleaned_data)
        subnet_name = cleaned_data.get('subnet_name')
        #check name space
        if subnet_name and re.search(r'\s', subnet_name):
            raise ValidationError(_("no blank space allowed during network name"))

        try:
            subnet = api.quantum.subnet_get(self.request, self.subnet_id)
            subnets = api.quantum.subnet_list(self.request,
                network_id = subnet.network_id)
        except Unauthorized:
            raise
        except Exception as exe:
            LOG.error('Failed to get subnet list,the error is %s' % exe.message)

        if subnets:
            for subnet in subnets:
                if subnet_name and subnet.name == subnet_name and subnet.id != self.subnet_id :
                    raise ValidationError(_("subnet name  has exist."))

        return cleaned_data


class CreatePort(forms.Form):
    """
        the form for create a port
    """
    network_name = forms.CharField(label = _("Network Name"),
        widget = forms.TextInput(
            attrs = {'readonly': 'readonly'}))
    network_id = forms.CharField(label = _("Network ID"),
        widget = forms.TextInput(
            attrs = {'readonly': 'readonly'}))
    name = forms.CharField(max_length = 10,
        min_length = 2,
        label = _("Name"),
        required = False)
    admin_state = forms.BooleanField(label = _("Admin State"),
        initial = True, required = False)
    device_id = forms.CharField(max_length = 100, label = _("Device ID"),
        help_text = _('Device ID attached to the port'),
        required = False)
    device_owner = forms.CharField(max_length = 100, label = _("Device Owner"),
        help_text = _('Device owner attached to the port'),
        required = False)

    def __init__(self, *args, **kwargs):
        super(CreatePort, self).__init__(*args, **kwargs)

    def clean(self):
        return super(forms.Form, self).clean()

class UpdatePort(forms.Form):
    """
        the form for update a port
    """
    name = forms.CharField(max_length = 10,
        min_length = 2,
        label = _("Name"),
        required = False)
    admin_state = forms.BooleanField(label = _("Admin State"),
        initial = True, required = False)
    device_id = forms.CharField(max_length = 100, label = _("Device ID"),
        help_text = _('Device ID attached to the port'),
        required = False)
    device_owner = forms.CharField(max_length = 100, label = _("Device Owner"),
        help_text = _('Device owner attached to the port'),
        required = False)

    def __init__(self, *args, **kwargs):
        super(UpdatePort, self).__init__(*args, **kwargs)

    def clean(self):
        return super(forms.Form, self).clean()