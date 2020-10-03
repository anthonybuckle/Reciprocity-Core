from recip.util import DataType
import json
import os

class Config:
    with open('recip/config/config.json', 'r') as configFile:
        config = json.load(configFile)

def setKeyValue(key, value):
    Config.config[key] = value

def getIntValue(key, base=10):
    return DataType.asInt(Config.config[key], base)

def getBoolValue(key):
    return DataType.asBool(Config.config[key])

def getDecimalValue(key):
    return DataType.asDecimal(Config.config[key])

def getBytesValue(key, hexStr=True):
    if hexStr:
        return DataType.fromHex(Config.config[key])
    else:
        return DataType.serialize(Config.config[key])

def getFilePath(directoryKey, fileKey):
    directory = getValue(directoryKey)
    file = getValue(fileKey)
    if not os.path.exists(directory):
        os.makedirs(directory)
    return os.path.join(directory, file)

def getValues(key):
    values = getValue(key)
    return values.split(',')

def getValue(key):
    return Config.config[key]
