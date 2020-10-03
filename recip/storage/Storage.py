from threading import Lock
from recip.util import Config
from recip.util import DataType
from recip.util import Log
import lmdb

class Storage:
    def __init__(self, database, subDatabase=None):
        self.database = database
        self.subDatabase = subDatabase
        self.db = None
        self.subDb = None
        self.lock = Lock()
    
    def open(self, subDatabase=None):
        self.lock.acquire()
        self.db = lmdb.open(self.database, max_dbs=Config.getIntValue('MAX_DATABASES'))
        subDatabaseBytes = DataType.serialize(self.subDatabase if subDatabase == None else subDatabase)
        self.subDb = self.db.open_db(subDatabaseBytes)
    
    def count(self, subDatabase=None):
        try:
            self.open(subDatabase)
            with self.db.begin() as db:
                return db.stat(db=self.subDb)['entries']
        except IOError:
            Log.error('Unable to count database entries')
        finally:
            self.close()
    
    def get(self, key, subDatabase=None):
        try:
            self.open(subDatabase)
            with self.db.begin(db=self.subDb) as db:
                return db.get(key)
        except IOError:
            Log.error('Unable to get record using key: %s' % key)
        finally:
            self.close()
        
    def set(self, key, value, subDatabase=None):
        try:
            self.open(subDatabase)
            with self.db.begin(write=True) as db:
                db.put(key, value, db=self.subDb)
        except IOError:
            Log.error('Unable to set record using key: %s value: %s' % (key, value))
        finally:
            self.close()
            
    def remove(self, key, subDatabase=None):
        try:
            self.open(subDatabase)
            with self.db.begin(write=True, db=self.subDb) as db:
                db.delete(key)
        except IOError:
            Log.error('Unable to remove record using key: %s' % key)
        finally:
            self.close()
    
    def close(self):
        try:
            if self.db != None:
                self.db.close()
                self.db = None
                self.subDb = None
        finally:
            self.lock.release()