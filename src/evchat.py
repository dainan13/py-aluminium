

import signal
import pyev
import socket

class ev_chat( object ):
    
    def __init__( self, channel, termin ):
        
        self._s = channel
        self.d = ''
        self.set_terminator(termin)
        
        return
    
    def set_terminator( self, terminator ):
        
        self.__terminator = terminator
        
        return
    
    def sendback( self, ):
        
        return
    
    def work( self, d ):
        
        print '>', self.d
        
        return
    
    def readable( self, watcher, events ):
        
        r = self._s.recv(1024)
        
        if r == '' :
            self._s.close()
            self.io.stop()
            
            return
        
        self.d += r
        
        d = self.d.split(self.__terminator,1)
        
        if len(d) == 2 :
            self.work(d[0])
            self.d = d[1]
        else :
            self.d = d[0]
        
        return

class dispatcher( object ):
    
    def __init__( self, addr = None ):
        
        if addr != None :
            self.create_socket( socket.AF_INET, socket.SOCK_STREAM )
            self.bind(addr)
            self.listen(5)
            
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
        
        self._listener = pyev.Io( self._s, pyev.EV_READ, self._loop, self.handle_accept, None )
        self._listener.start()
        
        self._loop.loop()
        
        return
    
    def handle_accept( self, watcher, events ):
        
        channel, addr = self._s.accept()
        
        s = ev_chat( channel, '\n' )
        
        io = pyev.Io( channel, pyev.EV_READ, self._loop, s.readable, self )
        
        s.io = io
        
        io.start()
        
    
if __name__ == "__main__":
    
    deamon = dispatcher( ('',7777) )
    
    deamon.loop()
    
    