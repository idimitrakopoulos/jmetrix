import logging

def setup_custom_logger(name):
    formatter = logging.Formatter(fmt='%(asctime)s [%(levelname)s] (%(filename)s:%(module)s:%(lineno)d): %(message)s')

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    return logger