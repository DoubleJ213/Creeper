# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 Nebula, Inc.
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

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _
import re
from django.core import validators
import unicodedata

horizon_config = getattr(settings, "HORIZON_CONFIG", {})
password_config = horizon_config.get("password_validator", {})

ipv4_cidr_re = re.compile(r'^(25[0-5]|2[0-4]\d|[0-1]?\d?\d)'   # 0-255
                          '(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}'  # 3x .0-255
                          '/(3[0-2]|[1-2]?\d)$')  # /0-32


validate_ipv4_cidr = validators.RegexValidator(ipv4_cidr_re)

def validate_port_range(port):
    if port not in range(-1, 65536):
        raise ValidationError("Not a valid port number")


def password_validator():
    return password_config.get("regex", ".*")


def password_validator_msg():
    return password_config.get("help_text", _("Password is not accepted"))

def has_hz(text):
    hz_yes = True
    for ch in text:
        if isinstance(ch,unicode):
            if unicodedata.east_asian_width(ch) != 'Na':
                hz_yes = False
                break
        else:
            continue
    return hz_yes
