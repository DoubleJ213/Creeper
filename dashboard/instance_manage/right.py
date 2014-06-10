
__author__ = 'yangzhi'

#charactercontent:right_key,name,depends,mutex,description

right_information = [
    ['1100', 'View Own Instance', '', '', ''],
    ['1101', 'View All Instance', {'depend_keys': ['1100']}, '', ''],
    ['1102', 'Add Instance',
     {'depend_keys':['1100', '1101','1300','1200','2000','2100','3000','3300']},'',''],
    ['1103', 'Reboot Instance', {'depend_keys':['1100']},'',''],
    ['1104', 'Delete Instance', {'depend_keys':['1100']},'',''],
    ['1105', 'Remote Desktop', {'depend_keys':['1100']},'',''],
    ['1106', 'Distribution Instance', {'depend_keys':['1100','1101','2100']},'',''],
    ['1107', 'Instance Classify', {'depend_keys':['1100']},'',''],
    ['1108', 'Live Migrate', {'depend_keys':['1100','1101']},'',''],
    ['1109', 'Instance Flavor Resize', {'depend_keys':['1100','1300']},'',''],
    ['1110', 'Update Instance Info', {'depend_keys':['1100']},'',''],
    ['1111', 'Soft Reboot Instance', {'depend_keys':['1100']},'',''],
    ['1112', 'Suspend Instance', {'depend_keys':['1100']},'',''],
    ['1113', 'Pause Instance', {'depend_keys':['1100']},'',''],
    ['1114', 'Backup Instance', {'depend_keys':['1100']},'',''],
    ['1115', 'Restore Backups', {'depend_keys':['1100']},'',''],
    ['1116', 'Quickly Create Image Templates',
     {'depend_keys':['1100','1125','1201']},'',''],
    ['1117', 'Audio Stop', {'depend_keys':['1100']},'',''],
    ['1118', 'USB Stop', {'depend_keys':['1100']},'',''],
    ['1119', 'Resume Instance', {'depend_keys':['1100']},'',''],
    ['1120', 'Unpause Instance', {'depend_keys':['1100']},'',''],
    ['1121', 'Undistribution Instance', {'depend_keys':['1100','1101','2100']},'',''],
    ['1123', 'Audio Open', {'depend_keys':['1100']}, '', ''],
    ['1124', 'USB Open', {'depend_keys':['1100']}, '', ''],
    ['1125', 'Get Backup List', {'depend_keys': ['1100']}, '', ''],
]
