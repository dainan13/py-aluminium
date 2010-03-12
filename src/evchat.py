

import signal
import pyev
import socket
import sys
import inspect


import traceback


def safe( old ):
    
    def new( *args, **kwargs ):
        try:
            return old(*args, **kwargs)
        except :
            traceback.print_exc()
            
    return new

class ev_chat( object ):
    
    def __init__( self, channel, termin ):
        
        self._s = channel
        self.d = ''
        self.set_terminator(termin)
        
        return
    
    def set_terminator( self, terminator ):
        
        self.__terminator = terminator
        
        return
    
    def sendback( self, data ):
        
        self._s.sendall(data)
        
        return
    
    def work( self, d ):
        
        print '>', self.d
        
        return

    def stop( self ):
	pass
    
    @safe
    def readable( self, watcher, events ):

        try :
            r = self._s.recv(1024)

        except :
            self._s.close()
            self._io = None
            self.stop()
            
            return


	if '' == r or None is r:
	    self._s.close()
            self._io = None
            self.stop()

	    return
        
        self.d += r
        
        while True:
            d = self.d.split(self.__terminator,1)
            
            if len(d) == 2 :
                self.work(d[0])
                self.d = d[1]
            else :
                self.d = d[0]
                break
        
        return

class dispatcher( object ):
    
    def __init__( self, addr, work=ev_chat, terminator='\r\n' ):
        
        self.chat = work if inspect.isclass(work) else ev_chat
        self.bindwork = work if self.chat!=work else None
        
        self.create_socket( socket.AF_INET, socket.SOCK_STREAM )
        self.bind(addr)
        self.listen(5)
        
        self.terminator = terminator
            
        return
    
    def create_socket( self, family, type ):
        self._s = socket.socket( family, type )
        
    def bind( self, address ):
        self._s.bind( address )
    
    def listen( self, backlog ):
        self._s.listen( backlog )
    
    def loop( self ):
        
        self._loop = pyev.default_loop(pyev.EVFLAG_NOSIGFD)
        
        # "OkOO|O:__init__", kwlist,
        # &fd, &events,
        # &loop, &callback, &data))
        
        self._listener = pyev.Io( self._s, pyev.EV_READ, self._loop, self.handle_accept )
        self._listener.start()
        
        self._signal = pyev.Signal( signal.SIGINT, self._loop, self.signal )
        self._signal.start()
        
        self._loop.loop()
        
        return
    
    @safe
    def handle_accept( self, watcher, events ):
        
        channel, addr = self._s.accept()
        
        s = self.chat( channel, self.terminator )
        
        io = pyev.Io( channel, pyev.EV_READ, self._loop, s.readable )
        
        s._io = io
        
        if self.bindwork != None:
            self.work = self.bindwork
        
        io.start()
        
    def signal( self, watcher, events ):
        
        watcher.loop.unloop()
    
    
    
if __name__ == "__main__":
    
    deamon = dispatcher( ('',7777) )
    
    deamon.loop()
    
    print
    
