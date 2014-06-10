"""
creeper log configuration
"""
import sys
reload(sys)

sys.setdefaultencoding('utf8')

logs_information = [
    ['create_node_action', 'Foundation Manage', 'add',
     'user %(user)s %(create_at)s create node', 'true'],
    ['delete_node', 'Foundation Manage', 'del',
     'user %(user)s %(create_at)s delete node', 'true'],
    ['update_node_action', 'Foundation Manage', 'edit',
     'user %(user)s %(create_at)s edit node', 'true'],
]