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
__date__ = '2012-01-31'
__version__ = 'v2.0.1'

import datetime
import dateutil.parser

from django.conf import settings

if settings.DEBUG:
    __log__ = 'v2.0.1 create'

import logging
LOG = logging.getLogger(__name__)

#    code begin
from django.template.base import (Node, Library,TemplateSyntaxError)
from django.utils.safestring import mark_safe
register = Library()

class AddInMethodNode(Node):
    """
        AddInMethodNode with render will generate string like
             "<div style='display:none'><input type='hidden' name='%s' value=%s /></div>"
    """
    def __init__(self, http_method):
        self.http_method = http_method

    def render(self, context):
        add_in_string = getattr(settings,'ADD_IN_METHOD_STRING','HTTP_X_HTTP_METHODOVERRIDE')
        if add_in_method:
            return mark_safe(u"<div style='display:none'><input type='hidden' name='%s' value=%s /></div>" % (add_in_string,self.http_method))


@register.tag
def add_in_method(parser, token):
    """
    :param parser: the tag parser
    :param token: the token which contain content
    :return: AddInMethodNode Obeject

    """
    bits = token.split_contents()
    if len(bits) != 2:
        raise TemplateSyntaxError("'%s' takes at one argument"
                                  " (HTTP METHOD)" % bits[0])
    return AddInMethodNode(bits[1])


@register.inclusion_tag('common/progress_bar.html')
def creeper_progress_bar(current_val, max_val):
    """ Renders a progress bar based on parameters passed to the tag. The first
    parameter is the current value and the second is the max value.

    Example: ``{% progress_bar 25 50 %}``

    This will generate a half-full progress bar.

    The rendered progress bar will fill the area of its container. To constrain
    the rendered size of the bar provide a container with appropriate width and
    height styles.

    """
    return {'current_val': current_val,
            'max_val': max_val}


@register.filter(is_safe=False)
def datetime_from_utctime(value):
    """Get datetime now form utc datetime."""
    time_diff = abs(datetime.datetime.now() - datetime.datetime.utcnow())
    if not isinstance(value, datetime.datetime):
        value = dateutil.parser.parse(value)
    return (value + time_diff).strftime("%Y-%m-%d %H:%M:%S")
