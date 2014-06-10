"""
Prepared data
"""
import datetime
import md5

from django.conf import settings
from django.db.models.signals import post_syncdb
from django.utils.timezone import utc

from dashboard.node_manage import models as node_manage_models
from dashboard.node_manage.models import Node

# initialize
def add_host_control_in_database():
    """
    :return:
    """
    try:
        Node.objects.all().delete()
    except Exception, exp:
        print "flush node_manage data failed.please check error (%s)" % exp
        return None

    control_host_name = getattr(settings, 'CONTROLLER_HOST_NAME',
                                'controller')
    control_host_ip = getattr(settings, 'CONTROLLER_HOST_IP', '192.168.0.2')

    created_at = datetime.datetime.now(tz=utc)
    uuid = md5.new(str(created_at)).hexdigest()

    node = Node(uuid=uuid,
                name=control_host_name,
                ip=control_host_ip,
                type="control_node",
                created_at=created_at,
    )
    try:
        node.save()
        return node.id
    except Exception, exp:
        print "init control_manage data failed.please check error (%s)" % exp
        return None


def init_node_manage_data(sender, **kwargs):
    """
    :param sender:
    :param kwargs:
    :return:
    """
    if sender == node_manage_models:
        control_id = add_host_control_in_database()
        if control_id:
            print "create control node ......... ok"
        else:
            print "create control node ......... failed"
    return

post_syncdb.connect(init_node_manage_data, sender=node_manage_models)