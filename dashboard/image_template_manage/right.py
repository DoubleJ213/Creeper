__author__ = 'liuh'

#charactercontent:right_key,name,depends,mutex,description

right_information = [
    ['1200','View Image','','',''],
    ['1201', 'Create Image', {'depend_keys':['1200', '1600', '2000']},'',''],
    ['1202', 'Update Image', {'depend_keys':['1200']},'',''],
    ['1203', 'Delete Image', {'depend_keys':['1200']},'',''],
    ['1204', 'ActiveAndStart', {'depend_keys':['1100','1101','1102','1300','1201','2000','2100','3000','3300']}, '', '']
]