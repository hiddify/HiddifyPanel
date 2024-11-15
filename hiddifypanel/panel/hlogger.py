import sys
from loguru import logger

def logger_dynamic_formatter(record) -> str:
    fmt = '<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>'
    if record['extra']:
        fmt += ' | <level>{extra}</level>'
    return fmt + '\n'

def init_app(app):
    init_logger(app,False)

def init_cli(app):
    init_logger(app,True)


def init_logger(app, cli):
    # configure logger
    
    logger.remove()
    logger.add(sys.stderr if cli else sys.stdout, format=logger_dynamic_formatter, level=app.config['STDOUT_LOG_LEVEL'],
               colorize=True, catch=True, enqueue=True, diagnose=False, backtrace=True)
    logger.trace('Logger initiated :)')

    with app.app_context():
        from hiddifypanel.models.config import hconfig,ConfigEnum
        set_level(app,hconfig(ConfigEnum.log_level))


def set_level(app, level):
    logger.add(app.config['HIDDIFY_CONFIG_PATH'] + "/log/system/panel.log", format=logger_dynamic_formatter, level=level,
                   colorize=True, catch=True, enqueue=True, diagnose=False, backtrace=True)