# coding:utf8
"""
Prepared data.
"""
from django.db.models.signals import post_syncdb
from dashboard.control_manage import models as table
from dashboard.thresholds_manage.models import Thresholds, ThresholdsType

TYPE_SQL = (
    {"name": 'CPU', "description": 'Monitoring the target host CPU usage,unit%'},
    {"name": 'Memory', "description": 'Monitoring the target host memory usage,unit%'},
    {"name": 'Disk Space', "description": 'Monitoring the target host disk space usage,unit%'},
    {"name": 'Network', "description": 'Monitoring the target host NetWork bandwidth usage,unit%'},
    {"name": 'Disk TPS', "description": 'Monitoring the target host disk TPS usage,unit%'},
    )

VALUE_SQL = (
    {"name": "The default thresholds of CPU",
     "description": "The default thresholds of CPU",
     "host": "default",
     "type_id": 1,
     "warning": 85,
     "critical": 90,
     "default": True,
     "deleted": False},
    {"name": "The default thresholds of Memory",
     "description": "The default thresholds of Memory",
     "host": "default",
     "type_id": 2,
     "warning": 85,
     "critical": 90,
     "default": True,
     "deleted": False},
    {"name": "The default thresholds of disk space",
     "description": "The default thresholds of disk space",
     "host": "default",
     "type_id": 3,
     "warning": 85,
     "critical": 90,
     "default": True,
     "deleted": False},
    {"name": "The default thresholds of network",
     "description": "The default thresholds of network",
     "host": "default",
     "type_id": 4,
     "warning": 85,
     "critical": 90,
     "default": True,
     "deleted": False},
    {"name": "The default thresholds of disk IOWait",
     "description": "The default thresholds of disk IOWait",
     "host": "default",
     "type_id": 5,
     "warning": 500,
     "critical": 800,
     "default": True,
     "deleted": False},
    )

def check_value_data():
    """
    Check default data exists
    :return:
    """
    data = Thresholds.objects.filter(host='default', default=True).count()
    if data:
        return True
    else:
        return False


def check_type_data():
    """
    Check default data exists
    :return:
    """
    data = ThresholdsType.objects.count()
    if data:
        return True
    else:
        return False


def insert_type_data():
    """
    insert threshold type default data.
    :return:
    """
    for sql in TYPE_SQL:
        ThresholdsType(name=sql['name'], description=sql['description']).save()


def insert_value_data():
    """
    insert threshold default data.
    :return:
    """
    for sql in VALUE_SQL:
        Thresholds(name=sql['name'], description=sql['description'],
                   host=sql['host'], type_id=sql['type_id'],
                   warning=sql['warning'], critical=sql['critical'],
                   default=sql['default'], deleted=sql['deleted']).save()


def init_control_manage_data(sender, **kwargs):
    """
    Initial database.
    :param sender:
    :param kwargs:
    :return:
    """
    if sender == table:
        if not check_type_data():
            insert_type_data()
            print "Initicalize type data ok."

        if not check_value_data():
            insert_value_data()
            print "Initicalize value data ok."
    return

#post_syncdb.connect(init_control_manage_data, sender=table)