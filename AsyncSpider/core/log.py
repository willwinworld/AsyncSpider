import logging.config
import sys

__all__ = ['logger']

logger = logging.getLogger('AsyncSpider')

logging.config.dictConfig(dict(
    version=1,
    loggers={
        'AsyncSpider': {
            'level': logging.INFO,
            'handlers': ['console']
        }
    },
    handlers={
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'std',
            'level': logging.INFO,
            'stream': sys.__stdout__
        }
    },
    formatters={
        'std': {
            'format': '%(asctime)s [%(filename)s] [line:%(lineno)d] %(levelname)s: %(message)s',
            'datefmt': '%Y:%m:%d %H:%M:%S',
        }
    }
))
