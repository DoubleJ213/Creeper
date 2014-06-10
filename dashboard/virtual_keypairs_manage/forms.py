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
__date__ = '2013-06-20'
__version__ = 'v2.0.9'

from django.conf import settings
if settings.DEBUG:
    __log__ = 'v2.0.9 create'

import logging
LOG = logging.getLogger(__name__)

#    code begin
from django.core import validators
from django.forms import *
from django import forms
from django.utils.translation import ugettext_lazy as _



class CreateKeypair(forms.Form):
    """
    the form for creating a keypiar
    """
    name = CharField(label = _("Name") , max_length = 20)

    def __init__(self, *args , **kwargs):
        super(CreateKeypair , self).__init__(*args , **kwargs)

    def clean(self):
        return super(forms.Form, self).clean()



class ImportKeypair(forms.Form):
    """
    the form for importing a Keypair
    """
    name = forms.CharField(max_length="20", label=_("Keypair Name"),
        validators=[validators.RegexValidator('\w+')])
    public_key = forms.CharField(label=_("Public Key"), widget=forms.Textarea)

    def __init__(self, *args , **kwargs):
        super(ImportKeypair , self).__init__(*args , **kwargs)

    def clean(self):
        return super(forms.Form , self).clean()

