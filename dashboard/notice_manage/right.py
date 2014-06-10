__author__ = 'liuh'

#charactercontent:right_key,name,depends,mutex,description

right_information = [
    ['4000','View Notice','','',''],
    ['4001', 'Create Notice', {'depend_keys':['4000']},'',''],
    ['4002', 'Update Notice', {'depend_keys':['4000']},'',''],
    ['4003', 'Delete Notice', {'depend_keys':['4000']},'',''],
]