import sys
import logging
import logging.config
from dockwrkr.monads import *

class StdoutFilter(logging.Filter):
  def __init__(self, level):
    self._level = level
    logging.Filter.__init__(self)
  def filter(self, rec):
    return rec.levelno < self._level

class LevelLogFormatter(logging.Formatter):
  def format(self, record):
    if record.levelno == logging.DEBUG:
      record.msg = '[%s] %s' % (record.levelname, record.msg)
    return super(LevelLogFormatter , self).format(record)

LOG_SETTINGS = {
  'version': 1,
  'disable_existing_loggers': False, 
  'root': {
    'level': 'NOTSET',
  },
  'loggers': {
    'dockwrkr': {
      'level': 'NOTSET',
      'qualname': 'dockwrkr',
      'handlers': ['stdout', 'stderr'],
      'propagate': False
    }
  },
  'handlers': {
    'console': {
      'level': 'NOTSET',
      'formatter': 'levelformatter',
      'class': 'logging.StreamHandler',
      'stream': 'ext://sys.stdout',
    },
    'stdout': {
      'level': 'INFO',
      'formatter': 'levelformatter',
      'class': 'logging.StreamHandler',
      'stream': 'ext://sys.stdout',
      'filters': ['StdoutFilter'],
    },
    'stderr': {
      'level': 'WARNING',
      'formatter': 'levelformatter',
      'class': 'logging.StreamHandler',
      'stream': 'ext://sys.stderr'
    }
  },
  'filters': {
    'StdoutFilter': {
      '()': StdoutFilter,
      'level': logging.WARNING
    }
  },
  'formatters': {
    'levelformatter': { 
      '()': LevelLogFormatter, 'format': '%(message)s' },
    'stdout': { 'format': '%(message)s' },
    'stderr': { 'format': '%(message)s' }
  }
}

logging.config.dictConfig(LOG_SETTINGS)

logger = logging.getLogger("dockwrkr")


def ddebug(msg, *args, **kwargs):
  return dlog(logging.DEBUG, msg, *args, **kwargs)

def dinfo(msg, *args, **kwargs):
  return dlog(logging.INFO, msg, *args, **kwargs)

def dwarning(msg, *args, **kwargs):
  return dlog(logging.WARNING, msg, *args, **kwargs)

def dcritical(msg, *args, **kwargs):
  return dlog(logging.CRITICAL, msg, *args, **kwargs)

def dexception(msg, *args, **kwargs):
  return dlog(logging.EXCEPTION, msg, *args, **kwargs)

def dlog(level, msg, *args, **kwargs):
  if args:
    msg = msg % args
  def deferredLog(data=None, *args, **kwargs):
    logger.log(level, msg)
    return OK(data)
  return deferredLog

