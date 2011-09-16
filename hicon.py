import gevent
import socket
import weakref

from errno import EALREADY, EINPROGRESS, EWOULDBLOCK, ECONNRESET, EINVAL, \
     ENOTCONN, ESHUTDOWN, EINTR, EISCONN, EBADF, ECONNABORTED, errorcode
     
     

class BinlogClient( object ):
    
    def __init__( self ):
        pass
        
    def start( self ):
        pass
        
    def stop( self ):
        pass


class BaseChat(object):
    
    buffer_size = 1024
    terminal = '\n'
    
    def __init__( self, conn ):
        
        self.conn = conn
        
        self.event = gevent.core.event(
                        gevent.core.EV_READ,
                        self.conn.fileno(),
                        self.onreadable,
                    )
                    
        self.event.add()
        
        self.data = ''

    def onreadable( self, ent, ev ):
        
        try:
            data = self.conn.recv(self.buffer_size)
            if not data:
                # a closed connection is indicated by signaling
                # a read condition, and having recv() return 0.
                self.handle_close()
                return
            else:
                self.data += data
                self.findterminator()
                self.event.add()
                return
                
        except socket.error, why:
            # winsock sometimes throws ENOTCONN
            if why.args[0] in [ECONNRESET, ENOTCONN, ESHUTDOWN, ECONNABORTED]:
                self.handle_close()
                return
            else:
                raise
        
    def handle_close( self ):
        
        self.conn.close()
        
        return
        
    def findterminator( self ):
        
        while(True):
            
            x = self.data.split( self.terminal, 1 )
            
            if len(x) == 2 :
                self.data = x[1]
                try :
                    self.onwork( x[0] )
                except :
                    traceback.print_exc()
                return
            else :
                break
        
        return
        
    def work( self, data ):
        pass


class HiconChat(object):
    
    def __init__( self, conn, queue ):
        super( self, HiconChat ).__init__(conn)
        self.queue = weakref.ref(queue)
    
    def work( self, data ):
        self.queue.put( data )


class HiconServer(object)
    
    def __init__( self ):
        
        self.binlog = BinlogClient()
        
    def onconn( self, conn, *args, **kwargs ):
        
        self.binlog_event = gevent.core.event(
                        gevent.core.EV_READ,
                        self.rep.conn.socket.fileno(),
                        self.onbinlog,
                    )
        
        self.binlog_event.add()
        
    def loop( self, ):
        
        gevent.core.init()
        
        self.event = gevent.core.event(
                        gevent.core.EV_READ,
                        self.sock.fileno(),
                        self.onclientlink,
                    )
        
        self.event.add()
        
        self.ctrlc_event = gevent.core.event(
                        gevent.core.EV_SIGNAL,
                        signal.SIGINT,
                        self.onctrlc,
        )
        
        self.ctrlc_event.add()
        
        gevent.core.dispatch()
    
    def onclientlink( self, ent, ev ):
        
        try:
            conn, addr = self.sock.accept()
        except TypeError:
            return
        except socket.error as why:
            if why.args[0] in (EWOULDBLOCK, ECONNABORTED):
                return
            else:
                raise
        
        hc = HiconChat( conn )
        
        self.event.add()
        
        return
        
if __name__ == '__main__' :
    