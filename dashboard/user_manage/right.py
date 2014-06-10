
__author__ = 'yangzhi'

#charactercontent:right_key,name,depends,mutex,description

right_information = [
    ['2100', 'View User', '', '', ''],
    ['2101', 'Create User', {'depend_keys':['2100']},'',''],
    ['2102', 'Update User', {'depend_keys':['2100']},'',''],
    ['2103', 'Update Password', {'depend_keys':['2100']},'',''],
    ['2104', 'Delete User', {'depend_keys':['2100']},'',''],
]