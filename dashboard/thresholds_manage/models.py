"""
Django orm classes
"""
from django.db import models

# Create your models here.

class Thresholds(models.Model):
    """
    threshold orm class
    """
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    delete_at = models.DateTimeField(null=True)
    deleted = models.NullBooleanField(null=True, default=False)
    name = models.CharField(max_length=50, null=True)
    description = models.CharField(max_length=255, null=True)
    host = models.CharField(max_length=255, default='default', null=True)
    type_id = models.IntegerField(null=True)
    warning = models.IntegerField(default=85, null=True)
    critical = models.IntegerField(default=90, null=True)
    default = models.NullBooleanField(default=False, null=True)
    isflag1 = models.NullBooleanField(null=True)
    isflag2 = models.NullBooleanField(null=True)
    host_id = models.CharField(max_length=50, null=True)

    class Meta:
        """
        Overwrite Django orm behaviors
        """
        db_table = 'thresholds'
        ordering = ['id', 'host']


class ThresholdsType(models.Model):
    """
    threshold type orm class
    """
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    delete_at = models.DateTimeField(null=True)
    deleted = models.NullBooleanField(null=True, default=False)
    name = models.CharField(max_length=50, null=True)
    description = models.CharField(max_length=255, null=True)
    isflag1 = models.NullBooleanField(null=True)
    isflag2 = models.NullBooleanField(null=True)

    class Meta:
        """
        Overwrite Django orm behaviors
        """
        db_table = 'thresholds_type'
