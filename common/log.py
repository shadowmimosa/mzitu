import logging
from loguru import logger
from config import DEBUG, SYSTEM


def init_log():

    if SYSTEM == 'Windows':
        rotation = None
    elif SYSTEM == 'Linux':
        rotation = '1 day'
    else:
        rotation = None

    _format = '{time:YY-MM-DD HH:mm:ss.SSS} - {process.name} - {thread.name} - {function} - {line} - {level} - {message}'
    logger.remove()
    handlers = [
        {
            # 'sink': 'log/error-{time:YYMMDD}.log',
            'sink': 'log/error.log',
            # 'sink': write,
            'format': _format,
            'level': 'ERROR',
            'rotation': rotation,
            'enqueue': True,
            'encoding': 'utf-8',
            'backtrace': True
        },
        {
            'sink': 'log/log.log',
            'format': _format,
            'level': 'INFO',
            'rotation': rotation,
            'enqueue': True,
            'encoding': 'utf-8',
            'backtrace': True
        }
    ]

    if DEBUG:
        handlers.append({
            'sink': 'log/debug.log',
            'format': _format,
            'level': 'DEBUG',
            'rotation': rotation,
            'enqueue': True,
            'encoding': 'utf-8',
            'backtrace': True
        })

    handlers.append({
        'sink': logging.StreamHandler(),
        'format': _format,
        'level': 'DEBUG',
        'enqueue': True,
        'backtrace': True
    })

    logger.configure(handlers=handlers)

    return logger
