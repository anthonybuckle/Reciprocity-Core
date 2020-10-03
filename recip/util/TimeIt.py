from recip.util import Config
from recip.util import DataType
from recip.util import Log

class TimeIt:
    timings = {}

def start(key):
    TimeIt.timings[key] = DataType.asTime()
    
def stop(key):
    startTime = TimeIt.timings[key]
    TimeIt.timings[key] = DataType.asTime() - startTime
    
def view(key):
    if Config.getBoolValue('TIME_IT_ENABLED'):
        message = "{0} => {1}s".format(key, TimeIt.timings[key])
        if Config.getBoolValue('TIME_IT_CONSOLE'):
            print(message)
        if Config.getBoolValue('TIME_IT_FILE'):
            Log.debug(message)