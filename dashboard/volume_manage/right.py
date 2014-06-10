__author__ = 'lsq'


right_information = [
    ['1500','View Volume','','',''],
    ['1501', 'Create Volume', {'depend_keys':['1500']},'',''],
    ['1502', 'Delete Volume', {'depend_keys':['1500']},'',''],
    ['1503', 'Attach Volume', {'depend_keys':['1100', '1101', '1500']},'',''],
    ['1504', 'Create Volume Snapshot', {'depend_keys':['1500']},'',''],
    ['1505', 'Delete Snapshot', {'depend_keys':['1500']},'',''],
    ['1506', 'Detach Volume', {'depend_keys':['1500']},'','']
]

