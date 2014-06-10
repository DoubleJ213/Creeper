__author__ = 'wangqing'

import logging
LOG = logging.getLogger(__name__)

import datetime

from django.core.files.uploadhandler import FileUploadHandler
from django.core.files.uploadedfile import TemporaryUploadedFile
from django.utils.timezone import utc

from dashboard.software_manage import SOFTWARE_STATE_UPLOADING
from dashboard.software_manage.models import Software


class SoftwareFileUploadHandler(FileUploadHandler):
    """
    Upload handler that streams data into a temporary file.
    """
    def __init__(self, *args, **kwargs):
        super(SoftwareFileUploadHandler, self).__init__(*args, **kwargs)
        #if 'software_formhash' in self.request.GET:
            #self.software_formhash = self.request.POST['software_formhash']
            #cache.set(self.software_formhash, { 'progress_percentage': 0 })
        #self.activated = True
        #else:
        #    self.activated = False

    def new_file(self, file_name, *args, **kwargs):
        """
        Create the file object to append to as data is coming in.
        """
        super(SoftwareFileUploadHandler, self).new_file(file_name, *args, **kwargs)

        if 'software_uuid' not in self.request.GET:
            self.activated = False
        else:
            try:
                software = Software.objects.filter(uuid=self.request.GET['software_uuid'])
                if software:
                    self.activated = False
                else:
                    try:
                        content_length = int(self.request.META.get('CONTENT_LENGTH', 0))
                    except Exception, e:
                        content_length = 0
                        LOG.error('Request META CONTENT_LENGTH format error. %s' % e)

                    created_at = datetime.datetime.now(tz=utc)
                    software = Software(uuid=self.request.GET['software_uuid'],
                                        status=SOFTWARE_STATE_UPLOADING,
                                        created_at=created_at,
                                        content_name=self.file_name,
                                        content_type=self.content_type,
                                        content_total=content_length,
                                        classify='unknown')
                    software.save()
                    self.activated = True
            except Exception, e:
                LOG.error('software upload error. %s', e)
                self.activated = False

        if self.activated:
            self.file = TemporaryUploadedFile(self.file_name, self.content_type, 0, self.charset)

    def receive_data_chunk(self, raw_data, start):
        if self.activated:
            self.file.write(raw_data)

    def file_complete(self, file_size):
        if self.activated:
            self.file.seek(0)
            self.file.size = file_size
            return self.file
