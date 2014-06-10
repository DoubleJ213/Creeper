__author__ = 'zwd'
__date__ = '2013-03-25'
__version__ = 'v2.0.5'

from django.conf import settings

if settings.DEBUG:
    __log__ = 'v2.0.5 create'

import logging

LOG = logging.getLogger(__name__)

#    code begin
from django.utils.translation import ugettext_lazy as _
from django.forms import *

class NoticeForm(forms.Form):
    uuid = CharField(label=_("uuid"), max_length=50, required=False)
    title = CharField(label=_("title"), min_length=2, max_length=10, required=True)
    content = CharField(label=_("content"), max_length=600, required=True)
    release = CharField(label=_("release"), max_length=2, required=False)
    level = CharField(label=_("level"), max_length=2, required=True)
    operater_id = CharField(label=_("operater_id"), max_length=50, required=False)

    def __init__(self, request, *args, **kwargs):
        super(NoticeForm, self).__init__(*args, **kwargs)









