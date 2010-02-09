

import signal
import pyev

def sig_cb(watcher, events):
    print("got SIGINT")
    # optional - stop all watchers
    if watcher.data:
        print("stopping watchers: {0}".format(watcher.data))
        for w in watcher.data:
            w.stop()
    # unloop all nested loop
    print("stopping the loop: {0}".format(watcher.loop))
    watcher.loop.unloop()

def timer_cb(watcher, events):
    watcher.data += 1
    print("timer.data: {0}".format(watcher.data))
    print("timer.loop.count(): {0}".format(watcher.loop.count()))
    print("timer.loop.now(): {0}".format(watcher.loop.now()))

def main():
    # use the default event loop unless you have special needs
    # I disable signalfd here cause it seems to be borked on my kernel version
    loop = pyev.default_loop(pyev.EVFLAG_NOSIGFD)
    # initialise and start a repeating timer
    timer = pyev.Timer(0, 2, loop, timer_cb, 0)
    timer.start()
    # initialise and start a Signal watcher
    sig = pyev.Signal(signal.SIGINT, loop, sig_cb)
    sig.data = [timer, sig] # optional
    sig.start()
    # now wait for events to arrive
    loop.loop()

class Session( object ):
    pass

class Deamon( object ):
    
    def __init__( self, ):
        pass
    
    def create_socket( self, family, type ):
        self._s = socket.socket( family, type )
        
    def bind( self, address ):
        self._s.bind( address )
    
    def listen( self, port ):
        self._s.listen( port )
    
    def loop( self, ):
        
        loop = pyev.default_loop(pyev.EVFLAG_NOSIGFD)
        
        # "OkOO|O:__init__", kwlist,
        # &fd, &events,
        # &loop, &callback, &data))
        
        io = pyev.IO(self._s, pyev.EV_READ, loop, self.handle_accept, ())
        io.start()
        
        loop.loop()
        
        return
    
    def handle_accept( self ):
        
        channel = self._s.accept()
        
        io = pyev.IO(self._s, pyev.EV_READ, loop, self.readable, channel)
        
    def readable( self ):
        
        return
    
if __name__ == "__main__":
    main()