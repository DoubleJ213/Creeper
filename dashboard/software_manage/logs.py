__author__ = 'zhaolei'
import sys
reload(sys)
sys.setdefaultencoding('utf8')

logs_information = [
    ['create_software_action', 'Software Manage', 'add',
     'user %(user)s %(create_at)s create software', 'false'],
    ['delete_software_action', 'Software Manage', 'del',
     'user %(user)s %(create_at)s delete software', 'false'],
    ['delete_softwares', 'Software Manage', 'del',
     'user %(user)s %(create_at)s batch delete software', 'false'],
]
