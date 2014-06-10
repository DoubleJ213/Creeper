__author__ = 'sunyu'
import sys

reload(sys)
sys.setdefaultencoding('utf8')

logs_information = [
    ['create_role', 'Role Manage', 'add',
     'user %(user)s %(create_at)s create role', 'false'],
    ['delete_role', 'Role Manage', 'del',
     'user %(user)s %(create_at)s delete role', 'false'],
    ['resume_role', 'Role Manage', 'resuming',
     'user %(user)s %(create_at)s resume role', 'false'],
    ]