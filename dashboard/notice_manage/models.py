__author__ = 'zwd'

from django.db import models

class Notice(models.Model):
    uuid = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=50)
    operater_id = models.CharField(max_length=50)
    content = models.CharField(max_length=600)
    create_time = models.DateTimeField()
    update_time = models.DateTimeField()
    release = models.CharField(max_length=2, default='0')
    level = models.CharField(max_length=2, default='0')

    def get_values(self):
        """
        :return: dict value,which will be bounded with form
        """
        return {'uuid': self.uuid, 'title': self.title,
                'operater_id': self.operater_id, 'content': self.content,
                'release': self.release, 'level': self.level, }