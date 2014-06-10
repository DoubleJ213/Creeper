
__author__ = 'yangzhi'

#charactercontent:right_key,name,depends,mutex,description

right_information = [
    ['2000', 'View Project', '', '', ''],
    ['2001', 'View Project Users', {'depend_keys':['2000','2100']},'',''],
    ['2002', 'Create Project', {'depend_keys':['2000']}, '', ''],
    ['2003', 'Create Project User', {'depend_keys':['2000', '2100']}, '', ''],
    ['2004', 'Update Project', {'depend_keys':['2000']}, '', ''],
    ['2005', 'Update Project Quotas', {'depend_keys':['2000']}, '', ''],
    ['2006', 'Delete Project', {'depend_keys':['2000']}, '', ''],
    ['2007', 'Update Project User', {'depend_keys':['2000', '2100']}, '', ''],
    ['2008', 'Delete Project User', {'depend_keys':['2000', '2100']}, '', ''],
]