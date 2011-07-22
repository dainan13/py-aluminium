import easyprotocol as ezp
import pymysql
import struct

class EasyReplication:
    
    #dbargsort = ('host', 'port', 'user', 'passwd', 'db',)
    
    COM_BINLOG_DUMP = 18
    
    ebp = ezp.EasyBinaryProtocol()
    ebp.parsefile( 'replication.protocol' )
    
    def __init__( self, logname, pos, db ):
        
        #self.conn = pymysql.connect( *[ db[dba] for dba in self.dbargsort if dba in db ] )
        self.conn = pymysql.connect( **db )
        self.serverid = 1
        self.logname = logname
        self.pos = pos
        
    def readloop( self ):

        #arg = struct.pack('<LHLs',self.pos,0,self.serverid,self.logname)
        
        arg = struct.pack('<L',self.pos)
        arg = arg + struct.pack('<H',0)
        arg = arg + struct.pack('<L',self.serverid)
        arg = arg + self.logname
        
        self.conn._execute_command(self.COM_BINLOG_DUMP, arg)
        
        while(True):
            yield self.ebp.read('binlog',self.conn.socket.makefile(),extra_headers_length=0)

        return
        
        
if __name__ == '__main__':
    
    import pprint
    
    # mysql -h10.210.74.143 -urepl
    
    db = { 'host' : '10.210.74.143', 
           'port' : 3306, 
           'user' : 'repl',
         }
    
    #erep = EasyReplication( 'mysql-bin.000080', 556, db )
    #erep = EasyReplication( 'mysql-bin.000080', 0, db )
    erep = EasyReplication( 'mysql-bin.000080', 187, db )
    for i in erep.readloop():
        pprint.pprint(i)
        print
        