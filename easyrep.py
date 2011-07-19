import easyprotocol as ezp
import pymysql
import struct

class EasyReplication:
    
    #dbargsort = ('host', 'port', 'user', 'passwd', 'db',)
    
    COM_BINLOG_DUMP = 18
    
    ebp = ezp.EasyBinaryProtocol()
    ebp.parse( 'replication.protocol' )
    
    def __init__( self, logname, pos, db ):
        
        #self.conn = pymysql.connect( *[ db[dba] for dba in self.dbargsort if dba in db ] )
        self.conn = pymysql.connect( **db )
        self.serverid = 1
        self.logname = logname
        self.pos = pos
        
    def read( self ):

        arg = struct.pack('<LHLs',self.pos,0,self.serverid,self.logname)
        
        self.conn._execute_command(self.COM_BINLOG_DUMP, arg)
        
        return self.ebp.read('binlog',self.conn.socket.makefile(),extra_headers_length=0)
        
        
if __name__ == '__main__':
    
    db = { 'host' : '10.210.74.143', 
           'port' : 3306, 
           'user' : 'repl',
         }
    
    erep = EasyReplication( 'ker106-bin.000107', 658, db )
    print erep.read()
    