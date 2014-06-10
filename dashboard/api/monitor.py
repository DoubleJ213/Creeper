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
__date__ = '2013-02-18'
__version__ = 'v2.0.1'

from django.conf import settings

if settings.DEBUG:
    __log__ = 'v2.0.1 create'

import logging

LOG = logging.getLogger(__name__)

#    code begin

import re
import subprocess
import json
#import memcache
from urllib2 import Request, HTTPError, URLError, urlopen

from dashboard.utils.i18n import get_text
from dashboard.thresholds_manage.utils import _get_threshold_value

from keystoneclient.exceptions import Unauthorized

FLAG_CPU = 'nrpe_check_cpu!'
FLAG_MEM = 'nrpe_check_mem!'
FLAG_NET = 'nrpe_check_net!'
FLAG_DISK = 'nrpe_check_disk!'
FLAG_IO = 'nrpe_check_diskstat!'
FLAG_SERVICE = 'nrpe_check_procs!'

HARD_STATUS = 1
SOFT_STATUS = 0

UP = 0
DOWN = 1
UNREACHABLE = 2

class APIResourceWrapper(object):
    """ Simple wrapper for api objects

        Define _attrs on the child class and pass in the
        api object as the only argument to the constructor
    """
    _attrs = []
    _item_split_char = ','

    def __init__(self, str):
        self._str = str
        if -1 == str.find('OK'):
            self._str = None

    def __getattr__(self, attr):
        if attr in self._attrs:
            # __getattr__ won't find properties
            return self.get_attr_from_str(attr)
        else:
            return None

    def get_attr_from_str(self, attr):
        if self._str:
            start_index = self._str.find(attr)
            if -1 != start_index:
                start_index = start_index + len(attr) + 1
                end_index = self._str.find(self._item_split_char, start_index)
                if -1 != end_index:
                    return self._str[start_index:end_index]
                else:
                    return self._str[start_index:]

        else:
            return None

    def to_JSON(self):
        json = {}
        if self._str:
            for attr in self._attrs:
                json[attr] = getattr(self, attr, None)
        return json


class CPU(APIResourceWrapper):
    _attrs = ['user', 'nice', 'sys', 'iowait', 'irq', 'softirq', 'idle',
              'cpu_usage']

    def __init__(self, str):
        super(CPU, self).__init__(str)


class MEM(APIResourceWrapper):
    _attrs = ['total', 'used', 'total_b', 'used_b', 'cache', 'buffer']

    def __init__(self, str):
        super(MEM, self).__init__(str)


class STATUS(object):
    def __init__(self, str):
        self._str = str
        if -1 == str.find('NRPE'):
            self.is_online = 'offline'
        else:
            self.is_online = 'online'

    @property
    def status(self):
        return self.is_online

    def to_JSON(self):
        return self.is_online


class NET(object):
    def __init__(self, str):
        self._str = str
        if -1 == str.find('NET'):
            self._str = None

        if self._str:
            self.nets = {}
            #list_all=re.findall('\s(\w+)=\(([\d\.]+B)\/([\d\.]+B)\)',self._str)
            list_all = re.findall(
                'NET \w+\s-\s(\w+):([0-9a-zA-Z\.]+)/([0-9a-zA-Z\.]+).*',
                self._str)
            for net in list_all:
                setattr(self, net[0], {'in': net[1], 'out': net[2]})
                self.nets[net[0]] = {'in': net[1], 'out': net[2]}

    def to_JSON(self):
        return self.nets


class SERVICE(object):
    _services = {'keystone-all': get_text('authorize service'),
                 'nova-compute': get_text('compute service'),
                 'nova-network': get_text('network service'),
                 'nova-scheduler': get_text('schedule service'),
                 'nova-volume': get_text('volume service'),
                 'mysqld': get_text('database service'),
                 'dnsmasq': get_text('dns service'),
                 'rabbitmq': get_text('rabbitmq service'),
    }

    def __init__(self, str):
        self._str = str
        if -1 == str.find('OK'):
            self._str = None

        if self._str:
            self.services = {}
            list_all = re.findall('PROCS\s(\w+):\s(\d+).*\'(\S+)\'', self._str)
            for service in list_all:
                setattr(self, service[2], {'status': service[0],
                                           'is_active': bool(int(service[1]))})
                if self._services.has_key(service[2]):
                    self.services[self._services[service[2]]] = {
                        'status': service[0],
                        'is_active': bool(int(service[1]))}

    def to_JSON(self):
        return self.services


class DISK(object):
    def __init__(self, str):
        self._str = str
        if -1 == str.find('DISK'):
            self._str = None

        if self._str:
            self.disks = {}
            list_all = re.findall(
                'DISK OK\s-\s(\w+)\s(\w+):(\w+),(\w+):(\d+),(\w+):(\d+),'
                '(\w+):(\d+)',
                self._str)
            for disk in list_all:
                setattr(self, disk[0],
                        {disk[1]: disk[2], disk[3]: disk[4], disk[5]: disk[6],
                         disk[7]: disk[8]})
                self.disks[disk[0]] = {disk[1]: disk[2], disk[3]: disk[4],
                                       disk[5]: disk[6], disk[7]: disk[8]}

    def to_JSON(self):
        return self.disks


class DISKSTAT(object):
    def __init__(self, str):
        self._str = str
        if -1 == str.find('DISKSTAT'):
            self._str = None

        if self._str:
            self.disks = {}
            list_all = re.findall(
                'DISKSTAT\s.*\s\-\s(\w+)\s\w*:(\d+).*\,.*:(\d+).*\,.*:(\d+).*',
                self._str)
            for disk in list_all:
                setattr(self, disk[0],
                        {'tps': disk[1], 'read': disk[2], 'write': disk[3]})
                self.disks[disk[0]] = {'tps': disk[1], 'read': disk[2],
                                       'write': disk[3]}

    def to_JSON(self):
        return self.disks


class Monitor(object):
    _nrpe_path = '/usr/local/nagios/libexec/check_nrpe'

    def __init__(self, *args, **kwargs):
        super(Monitor, self).__init__(*args, **kwargs)

    def run_command(self, filter, *args):
        data = None
        try:
            data = subprocess.Popen(args, stdout=subprocess.PIPE)
            return filter(data.stdout.read() or '')
        except Exception, e:
            print data.stderr if data else ""

    def check_status(self, host, command):
        _command = command
        if host:
            return self.run_command(STATUS, self._nrpe_path, '-H', str(host))
        else:
            return None

    def check_cpu(self, host, command):
        if host and command:
            return self.run_command(CPU, self._nrpe_path, '-H', str(host), '-c',
                                    str(command))
        else:
            return None

    def check_mem(self, host, command):
        if host and command:
            return self.run_command(MEM, self._nrpe_path, '-H', str(host), '-c',
                                    str(command))
        else:
            return None

    def check_net(self, host, command):
        if host and command:
            return self.run_command(NET, self._nrpe_path, '-H', str(host), '-c',
                                    str(command))
        else:
            return None

    def check_services(self, host, command, **kwargs):
        if host and command:
            return self.run_command(SERVICE, self._nrpe_path, '-H', str(host),
                                    '-c', str(command))
        else:
            return None

    def check_disk(self, host, command):
        if host and command:
            return self.run_command(DISK, self._nrpe_path, '-H', str(host),
                                    '-c', str(command))
        else:
            return None

    def check_diskstat(self, host, command):
        if host and command:
            return self.run_command(DISKSTAT, self._nrpe_path, '-H', str(host),
                                    '-c', str(command))
        else:
            return None


class VoyageClient(object):
    def __init__(self):
        self.base_url = settings.VOYAGE_BASE_URL
        self.all_hosts_url = settings.VOYAGE_OBJECTS_URL
        self.host_url = settings.VOYAGE_OBJECT_URL
        self.all_status_url = settings.VOYAGE_SERVICES_STATUS_URL
        self.status_url = settings.VOYAGE_SERVICE_STATUS_URL
        self.all_strategy_url = settings.VOYAGE_OS_STRATEGY_URL
        self.update_strategy_url = settings.VOYAGE_OS_STRATEGY_UPDATE_URL
        self.headers = {"accept": "application/json",
                        "content-type": "application/json"}

    def _do_request(self, action, header, body=None):
        if header:
            self.headers.update(header)
        try:
            request = Request(url=action, headers=self.headers, data=body)
            resp = urlopen(request)
            return json.loads(resp.read())
        except Exception, e:
            if getattr(e, 'code', '') == 401:
                raise Unauthorized('Unauthorized')
            LOG.error(
                "Failed to send request to voyage server, reason: %s" % (e))
            raise e

    def get_all_hosts(self, tenant_id, token):
        url = self.all_hosts_url % {'tenant_id': tenant_id,
                                    'base_url': self.base_url}
        body = self._do_request(url, {'X-Auth-Token': token})
        if not body:
            raise VoyageClientException()
        else:
            return body

    def get_host_by_id(self, tenant_id, token, host_id):
        url = self.host_url % {'tenant_id': tenant_id,
                               'host_id': host_id,
                               'base_url': self.base_url}
        body = self._do_request(url, {'X-Auth-Token': token})
        if not body:
            raise VoyageClientException()
        else:
            return body

    def get_all_status(self, tenant_id, token):
        url = self.all_status_url % {'tenant_id': tenant_id,
                                     'base_url': self.base_url}
        body = self._do_request(url, {'X-Auth-Token': token})
        if not body:
            raise VoyageClientException()
        else:
            return body

    def get_status_by_host_id(self, tenant_id, token, host_id):
        url = self.status_url % {'tenant_id': tenant_id,
                                 'host_id': host_id,
                                 'base_url': self.base_url}
        body = self._do_request(url, {'X-Auth-Token': token})
        if not body:
            raise VoyageClientException()
        else:
            return body

    def get_all_os_strategy(self, tenant_id, token):
        url = self.all_strategy_url % {'tenant_id': tenant_id,
                                       'base_url': self.base_url}
        body = self._do_request(url, {'X-Auth-Token': token})
        if not body:
            raise VoyageClientException()
        else:
            return body

    def update_os_strategy(self, tenant_id, token, data):
        strategy_id = data.pop('old_id')
        url = self.update_strategy_url % {'tenant_id': tenant_id,
                                          'base_url': self.base_url,
                                          'strategy_id': strategy_id}
        try:
            self._do_request(url, {'X-Auth-Token': token},
                             body=json.dumps(data))
        except Exception, e:
            raise e


class VoyageClientException(Exception):
    """
    Voyage Client Exception when voyage server did not reply any data.
    """
    pass


class VoyageMonitor(object):
    def __init__(self):
        self.voyage_client = VoyageClient()
        #self.memcached_client = memcache.Client([settings.VOYAGE_CACHE],
        # debug=0)

    def get_host_list(self, tenant_id, token):
        json = self.voyage_client.get_all_hosts(tenant_id, token) or None
        if json:
            data = {}
            hosts = json['hosts']
            for host in hosts:
                host = host['host']
                data[host['address']] = {'id': host['id'],
                                         'service': host['service']}
            return data
        else:
            return {}


    def get_host_dict(self, tenant_id, token):
        json = self.voyage_client.get_all_hosts(tenant_id, token) or None
        if json:
            data = {}
            hosts = json['hosts']
            for host in hosts:
                host = host['host']
                data[host['name']] = host['id']
            return data
        else:
            return {}


    def get_host_status(self, tenant_id, token):
        all_status = self.voyage_client.get_all_status(tenant_id, token)
        if all_status:
            json = {}
            hosts = all_status['hoststatus']
            for host in hosts:
                state_type = host['state_type']
                current_state = host['current_state']
                host_id = host['host_object_id']
                # TODO compare with cache and make sure the host status has
                # been changed.
                if state_type == HARD_STATUS and current_state == DOWN:
                    json[host_id] = 'offline'
                else:
                    json[host_id] = 'online'
                    # TODO cache host status and notify the subscriber.
            return json
        else:
            return {}

    def check_load(self, tenant_id, token, host_id, node_uuid):
        host_all_service_status = self.voyage_client.get_status_by_host_id(
            tenant_id, token, host_id)
        if host_all_service_status:
            services = host_all_service_status['service']
            json = self._parse_services(services, node_uuid)

            state_type = host_all_service_status['state_type']
            current_state = host_all_service_status['current_state']
            if state_type == HARD_STATUS and current_state == DOWN:
                json['HOST'] = 'offline'
            else:
                json['HOST'] = 'online'

            return json
        else:
            return {}

    def _parse_services(self, services, node_uuid):
        # TODO cache service perform load and check the attempt
        json = {}
        openstack_service = {}
        for service in services:
            type = service['check_command']
            if FLAG_CPU in type:
                perf = CPU(service['output']).to_JSON()
                warning, critical = self.get_thresholds(node_uuid, 1)
                percentage = int(perf['cpu_usage'])
                if percentage < warning:
                    perf['status'] = 'OK'
                elif warning <= percentage < critical:
                    perf['status'] = 'WARNING'
                else:
                    perf['status'] = 'CRITICAL'
                json['CPU'] = perf

            elif FLAG_MEM in type:
                perf = MEM(service['output']).to_JSON()
                warning, critical = self.get_thresholds(node_uuid, 2)
                percentage = (
                    int(perf['used'][0:perf['used'].find(' ')]) * 100 / int(
                        perf['total'][0:perf['total'].find(' ')]))
                if percentage < warning:
                    perf['status'] = 'OK'
                elif warning <= percentage < critical:
                    perf['status'] = 'WARNING'
                else:
                    perf['status'] = 'CRITICAL'
                json['MEM'] = perf

            elif FLAG_NET in type:
                perf = NET(service['output']).to_JSON()
                read = 0
                write = 0
                for disk, state in perf.items():
                    read += float(state['in'][0:state['in'].find('Kb')])
                    write += float(state['out'][0:state['out'].find('Kb')])
                    # BUG 196
                read /= 12800.0
                write /= 12800.0

                warning, critical = self.get_thresholds(node_uuid, 4)

                if read < warning and write < warning:
                    perf['status'] = 'OK'
                elif read > critical or warning > critical:
                    perf['status'] = 'CRITICAL'
                else:
                    perf['status'] = 'WARNING'

                json['NET'] = perf

            elif FLAG_DISK in type:
                perf = DISK(service['output']).to_JSON()
                warning, critical = self.get_thresholds(node_uuid, 3)
                for disk, usage in perf.items():
                    percentage = int(usage['usage'])
                    if percentage < warning:
                        perf['status'] = 'OK'
                    elif warning <= percentage < critical:
                        perf['status'] = 'WARNING'
                        break
                    else:
                        perf['status'] = 'CRITICAL'
                        break

                json['DISK'] = perf

            elif FLAG_IO in type:
                perf = DISKSTAT(service['output']).to_JSON()
                percentage = 0
                for disk, state in perf.items():
                    percentage += int(state['tps'])

                warning, critical = self.get_thresholds(node_uuid, 5)

                if percentage < warning:
                    perf['status'] = 'OK'
                elif warning <= percentage < critical:
                    perf['status'] = 'WARNING'
                else:
                    perf['status'] = 'CRITICAL'
                json['IO'] = perf

            elif FLAG_SERVICE in type:
                for key, value in SERVICE(service['output']).to_JSON().items():
                    openstack_service[key] = value

            else:
                pass
        json['SERVICE'] = openstack_service
        return json

    def get_thresholds(self, node_uuid, threshold_type):
        return _get_threshold_value(node_uuid, threshold_type)

