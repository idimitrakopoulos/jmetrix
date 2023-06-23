import logging
log = logging.getLogger('root')
import functools, inspect

def debug(func):
    """ Debug a method and return it back"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return_value = func(*args, **kwargs)
        log.debug(f'Function  : {func.__name__}')
        log.debug(f'Arguments : {args, kwargs}')
        log.debug(f'Returns   : {return_value}')

        return return_value

    return wrapper