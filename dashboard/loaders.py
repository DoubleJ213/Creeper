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
__date__ = '2012-01-17'
__version__ = 'v2.0.1'

from django.conf import settings
if settings.DEBUG:
    __log__ = 'v2.0.1 create'

import logging
LOG = logging.getLogger(__name__)

#    code begin

import os
import sys

from django.core.exceptions import  ImproperlyConfigured
from django.template.base import TemplateDoesNotExist
from django.template.loader import BaseLoader
from django.utils._os import safe_join
from django.utils.importlib import import_module


# get the path of model 'dashboard'
fs_encoding = sys.getfilesystemencoding() or sys.getdefaultencoding()
app = 'dashboard'
try:
    mod = import_module(app)
except ImportError, e:
    raise ImproperlyConfigured('ImportError %s: %s' % (app, e.args[0]))

template_dir = os.path.dirname(mod.__file__)
template_dir = template_dir.decode(fs_encoding)
# list dashboard_app directories in this directories
dashboard_app_template_dirs = []
apps_name = os.listdir(template_dir)
for app_name in apps_name:
    app_path = safe_join(template_dir, app_name)
    if os.path.isdir(app_path) and app_name != 'api':
        dashboard_app_template_dirs.append(safe_join(app_path))


# It won't change, so convert it to a tuple to save memory.
dashboard_app_template_dirs = tuple(dashboard_app_template_dirs)

class TemplateLoader(BaseLoader):
    is_usable = True

    def get_template_sources(self, template_name, template_dirs=None):
        if not template_dirs:
            template_dirs = dashboard_app_template_dirs
        for template_dir in template_dirs:
            try:
                yield safe_join(template_dir, template_name)
            except UnicodeDecodeError:
                # The template dir name was a bytestring that wasn't valid UTF-8.
                raise
            except ValueError:
                # The joined path was located outside of template_dir.
                pass

    def load_template_source(self, template_name, template_dirs=None):
        for filepath in self.get_template_sources(template_name, template_dirs):
            try:
                file = open(filepath)
                try:
                    return (file.read().decode(settings.FILE_CHARSET), filepath)
                finally:
                    file.close()
            except IOError:
                pass
        raise TemplateDoesNotExist(template_name)


_loader = TemplateLoader()
