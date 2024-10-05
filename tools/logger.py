import os
import colorlog
from enum import Enum
from dotenv import find_dotenv, load_dotenv, dotenv_values

ENV = '.env'
LOGNAME = os.getenv('LOGNAME', 'app')
LOGLEVEL = os.getenv('LOGLEVEL', 'INFO').upper()


def _logger(name=None, level=LOGLEVEL):
    """Creates a colorized logger. (need to add file handler...)"""

    # use module name if no name is provided
    logformat = '%(log_color)s[%(levelname)s:%(module)s] %(message)s'
    if name:
        logformat = '%(log_color)s[%(levelname)s:%(name)s:] %(message)s'

    # use module filename and name
    if level == 'DEBUG':
        logformat = '%(log_color)s[%(levelname)s:%(name)s:%(module)s:%(filename)s:%(funcName)s] %(message)s'


    logger = colorlog.getLogger(name)
    if not logger.handlers:
        stream_handler = colorlog.StreamHandler()
        colored_formatter = colorlog.ColoredFormatter(logformat)
        stream_handler.setFormatter(colored_formatter)
        logger.addHandler(stream_handler)
        logger.setLevel(level)
        logger.propagate = False  # Prevent logger propagating messages to root logger
    return logger


### Create Default Logger
logger = _logger(name=LOGNAME, level=LOGLEVEL)

### Load Environment Variables
try:
    load_dotenv(find_dotenv(ENV, raise_error_if_not_found=True), override=True)
    print(f'Loaded {len(dotenv_values(ENV, verbose=True))} environment variables from {ENV}')

except Exception as e:
    logger.error(f'Error loading environment variables: {e}...')