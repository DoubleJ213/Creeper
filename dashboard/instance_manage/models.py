__author__ = 'xulei'
__date__ = '2013-03-11'
__version__ = 'v2.0.1'

import logging
#: CODE BEGIN
from django.conf import settings
from django.db import models

if settings.DEBUG:
    __log__ = 'v2.0.1 New models for relationship between instance and user.'

LOG = logging.getLogger(__name__)

class Distribution(models.Model):
    ins_name = models.CharField(max_length=50)
    instance_id = models.CharField(max_length=50)
    user_id = models.CharField(max_length=50)
    create_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'instance_user_mapping'

class Classify(models.Model):
    instance_id = models.CharField(max_length=50)
    classify_id = models.CharField(max_length=50)
    user_id = models.CharField(max_length=50)

    class Meta:
        db_table = 'instance_classify'


class UserClassify(models.Model):
    classify_id = models.CharField(max_length=50,primary_key=True)
    user_id = models.CharField(max_length=50)
    classify_name = models.CharField(max_length=100)

    class Meta:
        db_table = "instance_user_classify"

class ConsoleToken(models.Model):
    host = models.CharField(max_length=255, unique=True)
    token = models.CharField(max_length=255)
    create_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "console_tokens"