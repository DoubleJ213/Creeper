#!/usr/bin/env bash

# Author: Tom
# Date: 2013-3-1
# Description:

SERVICES="keystone nova-compute nova-network nova-schedule nova-volume mysql dnsmasq rabbitmq"
function simple_output_services_status(){
    output=""
    for service in $SERVICES; do
         temp=$(echo `/usr/local/nagios/libexec/check_procs -a $service` | awk '{print $2,$3}')
         output="${output},${service}:${temp}"
    done
    echo ${output:1:${#output}}
}


simple_output_services_status

