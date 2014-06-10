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


__author__ = 'wangyihan'
__date__ = '2013-10-21'
__version__ = 'v3.1.3'


right_information = [
    ['3100', 'View Router', {'depend_keys':['2000']}, '', ''],
    ['3101', 'Add RouterProject', {'depend_keys':['3100']}, '',''],
    ['3102', 'Delete RouterProject', {'depend_keys':['3100']}, '', ''],
    ['3103', 'Set Gateway', {'depend_keys':['3100']}, '', ''],
    ['3104', 'Delete Gateway', {'depend_keys':['3100']}, '', ''],
    ['3105', 'Add Router Interface', {'depend_keys':['3000','3100']}, '', ''],
    ['3106', 'Delete Router Interface', {'depend_keys':['3100']}, '', ''],
]