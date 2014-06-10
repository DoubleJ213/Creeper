"""
Threshold utils
"""
__author__ = 'xulei'
__date__ = '2013-04-07'
__version__ = 'v2.0.6'

import logging

from django.conf import settings
from functools import wraps

from dashboard.thresholds_manage.models import Thresholds

if settings.DEBUG:
    __log__ = 'v2.0.6 Views for thresholds operations'

LOG = logging.getLogger(__name__)

def threshold_cascade(host_id, host_name):
    """
    Update threshold information when node's name has been changed.
    :param host_id:
    :param host_name:
    :return:
    """
    try:
        Thresholds.objects.filter(host_id=host_id).update(host=host_name)
    except Exception, exp:
        LOG.error(
            ("Fail to cascade threshold host name , error info = %s") % (exp))


def _get_threshold_value(host_id, type_id):
    try:
        threshold = Thresholds.objects.get(host_id=host_id,
                                           type_id=type_id,
                                           deleted=False)
        return threshold.warning, threshold.critical
    except Thresholds.DoesNotExist:
        threshold = Thresholds.objects.get(host='default',
                                           default=True,
                                           type_id=type_id)
        return threshold.warning, threshold.critical