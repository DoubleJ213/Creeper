__author__ = 'liuh'

#charactercontent:right_key,name,depends,mutex,description

right_information = [
    ['4100','View Own Logs','','',''],
    ['4101', 'View All Logs', {'depend_keys': ['4100']}, '', ''],
    ['4102', 'Export Log List', {'depend_keys':['4100']},'',''],
    ['4103', 'Delete Log', {'depend_keys':['4100']},'',''],
]