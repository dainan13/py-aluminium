
import socket

class Memcache( object ):
    
    def __init__( self, host, port ):
        
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        self.conn((host, port))
        
        self.buffer = ''
        
        return
        
    
    def _send( self, s ):
        
        return self.conn.send( s )
    
    def _readline( self ):
        
        buf = self.buffer
        recv = self.conn.recv
        
        while True:
            
            index = buf.find('\r\n')
            if index >= 0:
                break
            data = recv(4096)
            if not data:
                self.buffer = ''
                return None
            buf += data
            
            
        self.buffer = buf[index+2:]
        
        return buf[:index]
        
    def _read( self, rlen ):
        
        self_socket_recv = self.conn.recv
        buf = self.buffer
        
        while len(buf) < rlen:
            foo = self_socket_recv(max(rlen - len(buf), 4096))
            buf += foo
            if not foo:
                raise _Error( 'Read %d bytes, expecting %d, '
                        'read returned 0 length bytes' % ( len(buf), rlen ))
        
        self.buffer = buf[rlen:]
        
        return buf[:rlen]
    
    def _store( self, cmd, key, flags, exptime, contain ):
        '''
        <command name> <key> <flags> <exptime> <bytes>\r\n
        <data block>\r\n
        
        - "STORED\r\n"
        - "NOT_STORED\r\n"
        
        
        <command name> : set add replace
        '''
        
        bytes = len(contain)
        
        self._send( '%s %s %d %d %d\r\n' %
                    (cmd, key, flags, exptime, bytes)
                  )
        
        self._send( contain + '\r\n')
        
        r = self._readline()
        
        if r == "STORED" :
            return
        else :
            raise Exception(r)
        
    def _set( key, flags, exptime, contain ):
        return self._store( 'set', key, flags, exptime, contain )
        
    def _add( key, flags, exptime, contain ):
        return self._store( 'add', key, flags, exptime, contain )

    def _replace( key, flags, exptime, contain ):
        return self._store( 'replace', key, flags, exptime, contain )

    def _read( self, keys ):
        '''
        get <key>*\r\n
        
        VALUE <key> <flags> <bytes>\r\n
        <data block>\r\n
        "END\r\n"
        '''
        
        keylist = ' '.join(keys)
        
        self._send( 'get %s\r\n' % ( keylist, ) )
        
        r = []
        for k in keys :
            v, ke, flags, le = self._readline().split(' ')
            data = self._read(le)
            self._readline()
            r.append( ( flags, data ) )
        
        ed = self._readline()
        
        return r

    def _delete( self, key, time ):
        '''
        delete <key> <time>\r\n
        
        - "DELETED\r\n"
        - "NOT_FOUND\r\n"
        '''
        
        self._send( 'delete %s %s\r\n' % ( key, time ) )
        
        r = self._readline()
        
        if r == 'DELETED' :
            return
        
        raise Exception(r)
        
    def _inc( self, key, value ):
        '''
        <key> <value>\r\n
        
        - "NOT_FOUND\r\n"
        - <value>\r\n
        '''

    def _dec( self, key, value ):
        '''
        <key> <value>\r\n
        
        - "NOT_FOUND\r\n"
        - <value>\r\n
        '''
        
    def _stat( self, args=None ):
        '''
        stats\r\n
        stats <args>\r\n
        
        STAT <name> <value>\r\n
        END\r\n
        '''
        
        if args == None :
            self._send('stats\r\n')
        else :
            self._send('stats %s\r\n' % (args,))
        
        r = {}
        x = self._readline()
        while( x != 'END' ):
            if x.startswith('STAT '):
                x = x[5:]
                k, v = x.split(' ',1)
                r[k] = v
            else :
                raise Exception(x)
        
            
        raise Exception(r)
        
    def _flush_all( self ):
        '''
        flush_all
        
        OK\r\n
        '''
    
    def _version( self ):
        '''
        version\r\n
        
        "VERSION <version>\r\n"
        '''
        
        self._send('version\r\n')
        
        r = self._readline()
        
        if r.startswith('VERSION ') :
            return r[8:]
            
        raise Exception(r)