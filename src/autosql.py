import threading
import queue
import time
import types

import MySQLdb




def simplequery( conn, sql ):
    
    conn.query( sql )
    
    rst = conn.store_result()
    rst = rst.fetch_row(rst.num_rows())
    
    return rst


def getcols( conn, table ):
    
    sql =  "DESCRIBE %s" % (src['table'])
    r = simplequery( conn, sql )
    
    return zip(*r)[0]

def colssql( cols ):
    return ','.join( ('`%s`' % (c) if c is not None else 'NULL') for c in cols )


def fetcher( conn, sql, q, s={}, step = 50 ):
    
    conn.query( sql )
    
    r = conn.use_result()
    s['total'] = r.num_rows()
    
    for i in range( 0, s['total'], step ):
        q.put( r.fetch_row( step ) )
        s['fetch'] = i
    
    q.put( None )
    
    return
    
def putter( conn, sql, q, s={} ):
    
    while( True ):
        
        rs = q.get()
        
        i = len(rs)
        
        if rs == None :
            break
        
        conn.query( sql, [ [ '"'+MySQLdb.escape_string(str(v))+'"' if v != None else "NULL" for v in r ] for r in rs ] )
            
        s['fill'] += i 
    
    return

def datamove( src, dst, src_cols = None, dst_cols = None, convert = None, cb = False, t = 1 ):
    
    src_conn = mysqldb.connect( conv={}, **src )
    dst_conn = mysqldb.connect( conv={}, **dst )
    
    if cb is not None and not callable(cb) :
        raise Exception, 'cb must callable.'
    
    if ( dst_cols == None or src_cols == None ) and convert != None :
        raise Exception, 'convert error'
    
    if dst_cols == None :
        dst_cols = getcols( dst_conn, dst['table'] )
        
    if src_cols == None :
        src_cols = getcols( src_conn, src['table'] )

    if convert == None :
        #dst_cols = src_cols = set(dst_cols) & set(src_cols)
        src_cols = [ ( c if c in src_cols else None ) for c in dst_cols ]
    elif type( convert ) == types.DictType :
        src_cols = [ c if c in src_cols else convert.get(c,None) for c in dst_cols ]
        convert = None

    readsql = 'SELECT SQL_BIG_RESULT SQL_BUFFER_RESULT SQL_NO_CACHE %s From `%s`' % ( colsql(src_cols), src['table'] )
    writesql = 'INSERT DELAYED IGNORE INTO `%s` (%s) VALUES ' % ( src['table'], colsql(src_cols) )
    
    q = queue.Queue(200)
    
    r = {}
    
    f = threading.Tread( target = fetcher, args=( conn, readsql, q, r ) )
    p = threading.Tread( target = putter, args=( conn, readsql, q, r ) )
    
    f.run()
    p.run()
    
    while( True ):
        
        fa, pa = f.isAlive(), p.isAlive()
        
        if cb :
            cb( fa, pa, r )

        if not ( fa or pa ) :
            break
            
        time.sleep(t)
        
    return
    