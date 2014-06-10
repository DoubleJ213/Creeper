__author__ = 'zhaolei'
import sys
reload(sys)
sys.setdefaultencoding('utf8')

logs_information = [
    ['allocate_ip_action','Virtual Address Manage','edit','user %(user)s %(create_at)s allocate floating ip','false'],
    ['release_ip_action','Virtual Address Manage','edit','user %(user)s %(create_at)s release floating ip','false'],
    ['associate_ip_action','Virtual Address Manage','edit','user %(user)s %(create_at)s associate floating ip','false'],
    ['disassociate_ip_action','Virtual Address Manage','edit','user %(user)s %(create_at)s disassociate floating ip','false'],
    ['release_fips','Virtual Address Manage','edit','user %(user)s %(create_at)s batch release floating ip','false'],
]