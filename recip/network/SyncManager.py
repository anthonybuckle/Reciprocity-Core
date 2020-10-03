from threading import Thread, Timer
from recip.util import Config
from recip.util import Sync

class SyncManager(Thread):
    def __init__(self):
        Thread.__init__(self, name='SyncManager', daemon=True)
    
    def run(self):
        Sync.version()
        Sync.getaddr()
        Sync.getblocks() 
        Sync.mempool() 
        pingBroadcast = Timer(Config.getIntValue("PING_BROADCAST_SECONDS"), Sync.ping)  
        pingBroadcast.setName('PING_BROADCAST')
        pingBroadcast.start()