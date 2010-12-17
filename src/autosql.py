

import threading
import queue

import MySQLdb

import time



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
    return ','.join( '`%s`' % (c) for c in cols )


def fetcher( conn, sql, q, t, step = 50 ):
    
    conn.query( sql )
    
    r = conn.use_result()
    
    for i in range( 0, rst.num_rows(), step )
        q.put( r.fetch_row( step ) )
    
    q.put( None )
    
    return
    
def putter( conn, sql, q, t ):
    
    while( True ):
        
        rs = q.get()
        
        if rs == None :
            break
        
        conn.query( sql, [ [ '"'+MySQLdb.escape_string(str(v))+'"' if v != None else "NULL" for v in r ] for r in rs ] )
    
    return

def datamove( src, dst, src_cols = None, dst_cols = None, convert = None, p = False ):
    
    src_conn = mysqldb.connect( **src, conv={} )
    dst_conn = mysqldb.connect( **dst, conv={} )
    
    if ( dst_cols == None or src_cols == None ) and convert != None :
        raise Exception, 'convert error'
    
    if dst_cols == None :
        dst_cols = getcols( dst_conn, dst['table'] )
        
    if src_cols == None :
        src_cols = getcols( src_conn, src['table'] )

    if convert == None :
        dst_cols = src_cols = set(dst_cols) & set(src_cols)

    readsql = 'SELECT SQL_BIG_RESULT SQL_BUFFER_RESULT SQL_NO_CACHE %s From `%s`' % ( colsql(src_cols), src['table'] )
    writesql = 'INSERT DELAYED IGNORE INTO `%s` (%s) VALUES ' % ( src['table'], colsql(src_cols) )
    
    q = queue.Queue(200)
    
    f = threading.Tread( target = fetcher, args=( conn, readsql, q ) )
    
    return
    