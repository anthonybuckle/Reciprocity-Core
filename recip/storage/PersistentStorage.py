from recip.storage.Storage import Storage
from recip.util import Config
from recip.util import RLP
from recip.util import Log

class PersistentStorage:
    db = Config.getFilePath("CHAIN_DIRECTORY", "PERSISTENT_DB")
    subDb = Config.getValue("STORAGE_SUB_DB")
    persistent = Storage(db, subDb)
    
    storage = {}

def dump():
    try:
        PersistentStorage.persistent.open()
        with PersistentStorage.persistent.db.begin() as storage:
            for keyBytes, valueBytes in storage.cursor(db=PersistentStorage.persistent.subDb):
                print('key', keyBytes, 'value', valueBytes)
    except IOError:
        Log.error('Unable to read persistent storage')
    finally:
        PersistentStorage.persistent.close()

def commit(key):
    deleteKeys = []
    for _key in PersistentStorage.storage:
        if _key.startswith(key):
            add(_key, PersistentStorage.storage[_key], False)
            deleteKeys.append(_key)
    for _key in deleteKeys:
        remove(_key, True)

def rollback(key):
    deleteKeys = []
    for _key in PersistentStorage.storage:
        if _key.startswith(key):
            deleteKeys.append(_key)
    for _key in deleteKeys:
        remove(_key, True)

def get(key, readOnly):
    if readOnly:
        if key in PersistentStorage.storage:
            return PersistentStorage.storage[key]
        value = PersistentStorage.persistent.get(RLP.encode(key))
        if value != None:
            value = RLP.decode(value)
            PersistentStorage.storage[key] = value
            return value
    else:
        value = PersistentStorage.persistent.get(RLP.encode(key))
        if value != None:
            return RLP.decode(value)
    return None

def add(key, value, readOnly):
    if readOnly:
        PersistentStorage.storage[key] = value
    else:
        PersistentStorage.persistent.set(RLP.encode(key), RLP.encode(value))
    
def remove(key, readOnly):
    if readOnly:
        if key in PersistentStorage.storage:
            PersistentStorage.storage.pop(key)
    else:
        PersistentStorage.persistent.remove(RLP.encode(key))