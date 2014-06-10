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

right_information = [
    # see dashboard/monitor_manage/views.py#?
    ['1000', 'View Global Monitor', {'depend_keys': ['1400', '1100']}, '', 'Right that user can get all monitor informations.'],
    # see dashboard/monitor_manage/views.py#358
    ['1001', 'Update Threshold Strategy', {'depend_keys':['1000']},'','Right that user can change nagios monitor strategy.'],
]