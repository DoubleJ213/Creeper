
import logging
LOG = logging.getLogger(__name__)

import threading

from Queue import Queue

class CreateLogsThread(threading.Thread):
    logsq =Queue()
    logThread = None
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        try:
            while True:
                try:
                    if CreateLogsThread.logsq._qsize() > 0:
                        log = CreateLogsThread.logsq.get(block=False)
                        log.save()
                except Exception, e:
                    LOG.error("save logs error. %s" % e)
        except Exception, e:
            LOG.error("save logs error. %s" % e)