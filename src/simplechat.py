
try :
    
    import select
    import epoll

    for attr in [ 'poll', 'error', 'POLLIN', 'POLLPRI',
                  'POLLOUT', 'POLLERR', 'POLLHUP', 'POLLNVAL']:
        setattr(select, attr, getattr(epoll, attr))
        
except ImportError:
    
    pass





import asyncore, asynchat
import socket

import types



import easydecorator


class SimpleChatChannel( asynchat.async_chat ):
    """
    telnet serv
    terminator is "\r\n" as default
    """
    
    def __init__( self, socket, work, terminator='\r\n' ):
        
        asynchat.async_chat.__init__( self, sock = socket )
        
        self.set_terminator(terminator)
        self.dowork = work
        self.data = ''
    
    def found_terminator( self ):
        """
        when the terminator is found , be called.
        and it will call do work here .
        """
        
        self.push( self.dowork( self.data ) or '' )
        self.data = ''
        
    def collect_incoming_data( self, data ):
        """
        when has data coming , be called .
        collect data from socket
        """
        
        self.data += data




class SimpleChatDeamon( asyncore.dispatcher ):
    
    """ simple telnet serv's daemon
    telnet serv's dispatcher
    when a user linked in, it will create a simplechatchannel object,
    and dispatch the link to it.
    """
    
    def __init__( self, work, addr, terminator='\r\n' ):
        """
        init the deamon , it will listen the port .
        """
        
        asyncore.dispatcher.__init__( self )
        
        self.create_socket( socket.AF_INET, socket.SOCK_STREAM )
        self.bind( addr )
        self.listen(5)
        
        self.dowork = work
        self.terminator = terminator

    def handle_accept(self):
        """
        when client is linked , be called .
        and a channel will be created by the channel_creator .
        """
        conn, addr = self.accept()
        
        SimpleChatChannel( conn, self.dowork, self.terminator )
        


def simplechat( work, addr, terminator='\r\n' ):
    
    SimpleChatDeamon( work, addr, terminator )
    asyncore.loop()


@easydecorator.decorator_builder(2)
def simplechatwith( _old, addr, terminator ):
    
    SimpleChatDeamon( _old, addr, terminator )
    asyncore.loop()
    
    return


if __name__ == '__main__':
    
    def foo( data ):
        return data.encode('hex')+'\r\n'
    
    simplechat( foo, ('', 2323) )