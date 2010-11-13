import MySQLdb


class sqlshell (object):
    
    def __init__( self, host, port, user, passwd, db ):

        self.conn = MySQLdb.Connection(
                        host=host, port=port, db=db,
                        user=user, passwd=passwd,
                    )
                    
    def query( self, sql ):
                    
        self.conn.query(sql)
        
        rst = self.conn.store_result()
        
        rst = rst.fetch_row(rst.num_rows())
        
        affect = self.conn.affected_rows()
        
        if rst != None :
            rst = [ [ str(i) for i in r ] for r in rst ]
            cols = [ max( len(i) for i in c ) for c in zip(*rst) ]
            rst = [ ' '.join( i.ljust(w) for i, w in zip( r, cols ) ) 
                    for r in rst ]
            for r in rst :
                print r
        
        print affect
        

import sys
import traceback
import getopt

if __name__ == '__main__' :
    
    opts, argv = getopt.getopt( sys.argv[1:] , 'h:P:p:u:e:' )
    opts = dict(opts)
    
    host = opts.get('-h', '127.0.0.1')
    port = int(opts.get('-P', 3306 ))
    user = opts['-u']
    passwd = opts['-p']
    e = opts.get('-e',None)
    
    db = argv[0] if argv else None
    
    ss = sqlshell( host, port, user, passwd, db )
    
    if e :
        ss.query(e)
    else :
        while True :
            e = raw_input('>>> ')
            try :
                ss.query(e)
            except Exception, _e:
                #traceback.print_exc()
                print _e
    