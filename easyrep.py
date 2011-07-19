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

        #arg = struct.pack('<LHLs',self.pos,0,self.serverid,self.logname)
        
        arg = struct.pack('<L',self.pos)
        arg = arg + struct.pack('<H',0)
        arg = arg + struct.pack('<L',self.serverid)
        arg = arg + self.logname
        
        self.conn._execute_command(self.COM_BINLOG_DUMP, arg)
        
        return self.ebp.read('binlog',self.conn.socket.makefile(),extra_headers_length=0)
        #return self.conn.socket.makefile().read(68)
        
        
if __name__ == '__main__':
    
    import pprint
    
    db = { 'host' : '10.210.74.143', 
           'port' : 3306, 
           'user' : 'repl',
         }
    
    #erep = EasyReplication( 'ker106-bin.000121', 801523535, db )
    erep = EasyReplication( 'mysql-relay-bin-m.000002', 658, db )
    pprint.pprint(erep.read())
    
    #'D\x00\x00\x01\xff\xd4\x04#HY000Could not find first log file name in binary log index '
    # ---len---  r1  r2 -errno-