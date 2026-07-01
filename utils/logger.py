import logging
import os
from logging.handlers import RotatingFileHandler


def default_log_path(filename):
    """Resolve a log file path without hardcoding machine-specific directories.

    Uses ``$MINUTETRADER_LOG_DIR`` when set, otherwise a ``logs/`` directory at
    the project root (the parent of this module's package), so the bot writes
    logs correctly on any host or CI runner.
    """
    log_dir = os.environ.get('MINUTETRADER_LOG_DIR') or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs'
    )
    return os.path.join(log_dir, filename)


def setup_logger(name, log_file, level=logging.INFO):
    """Function to setup as many loggers as you want"""
    
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # File handler
    handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
    handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    logger.addHandler(console_handler)

    return logger
