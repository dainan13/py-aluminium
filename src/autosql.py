import threading
import Queue
import time
import types

import MySQLdb




def simplequery( conn, sql ):
    
    conn.query( sql )
    
    rst = conn.store_result()
    rst = rst.fetch_row(rst.num_rows())
    
    return rst


def getcols( conn, table ):
    
    sql =  "DESCRIBE `%s`" % ( table )
    r = simplequery( conn, sql )
    
    return zip(*r)[0]

def colssql( cols ):
    return ','.join( ('`%s`' % (c) if c is not None else 'NULL') for c in cols )




def fetcher( datas, q, r={}, step = 50 ):
    
    try :
        
        while( True ):
            
            rs = datas.fetch_row( step )
            
            if len(rs) == 0 :
                break
            
            q.put( rs )
            
            r['fetchrows'] += len(rs)
            
        #for i in range( 0, r['totalrows'], step ):
        #    q.put( datas.fetch_row( step ) )
        #    datas['fetchrows'] = i
        #q.put( datas.fetch_row( r['totalrows'] - i ) )
        #r['fetchrows'] = r['totalrows']
        
    finally :
        
        r['error'] = True
        q.put( None )
    
    return
    


def filler( dst, sql, q, r={} ):
    
    conn = MySQLdb.connect( conv={}, **dst )
    
    try :
        
        while( True ):
            
            rs = q.get()
            
            if rs == None :
                break
                
            i = len(rs)
            
            conn.query( sql, [ [ '"'+MySQLdb.escape_string(str(v))+'"' if v != None else "NULL" for v in r ] for r in rs ] )
            
            conn.commit()
            
            r['fillrows'] += i 
    
    finally :
        r['error'] = True
    
    return



def dmprint( r ):
    print r

def datamove( src, dst, src_cols = None, dst_cols = None, convert = None, cb = None, t = 1 ):
    
    _src = src.copy()
    _dst = dst.copy()
    
    del _src['table']
    del _dst['table']
    
    src_conn = MySQLdb.connect( conv={}, **_src )
    dst_conn = MySQLdb.connect( conv={}, **_dst )
    
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

    readsql = 'SELECT SQL_BIG_RESULT SQL_BUFFER_RESULT SQL_NO_CACHE %s From `%s`' % ( colssql(src_cols), src['table'] )
    writesql = 'INSERT DELAYED IGNORE INTO `%s` (%s) VALUES ' % ( src['table'], colssql(src_cols) )

    r = {}
    q = Queue.Queue(200)

    cb( r )

    src_conn.query( readsql )
    
    datas = src_conn.use_result()
    r['totalrows'] = datas.num_rows()
    r['fill'] = True
    r['fetch'] = True
    r['error'] = False
    r['fillrows'] = 0
    r['fetchrows'] = 0
    
    cb( r )
    
    fe = threading.Thread( target = fetcher, args=( datas, q, r ) )
    fi = threading.Thread( target = filler, args=( _dst, writesql, q, r ) )
    
    fe.start()
    fi.start()
    
    while( True ):
        
        r['fetch'], r['fill'] = fe.isAlive(), fi.isAlive()
        
        if cb :
            cb( r )

        if r['fetch'] == False and r['fill'] == False :
            break
            
        time.sleep(t)
        
    fe.join()
    fi.join()
        
    return
    