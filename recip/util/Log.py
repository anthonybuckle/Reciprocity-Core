from recip.util import Config
import logging

def getLogger(name, logLevel, logPath):
    logger = logging.getLogger(name)
    logger.setLevel(logLevel)
    logger.addHandler(getLogHandler(logPath))
    return logger

def getLogHandler(logPath):
    logHandler = logging.FileHandler(logPath)
    logFormat = logging.Formatter(Config.getValue('LOG_FORMAT'))
    logHandler.setFormatter(logFormat)
    return logHandler

class Log:
    debugLogger = getLogger(
        'DEBUG', 
        logging.DEBUG,
        Config.getFilePath('LOG_DIRECTORY', 'DEBUG_LOG_FILE')
    )
    
    errorLogger = getLogger(
        'ERROR', 
        logging.ERROR,
        Config.getFilePath('LOG_DIRECTORY', 'ERROR_LOG_FILE')
    )

def debug(message):
    if Config.getBoolValue('DEBUG_LOG_ENABLED'):
        Log.debugLogger.debug(message)
    
def error(message):
    Log.errorLogger.error(message)
