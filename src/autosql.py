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




def fetcher( datas, q, r={}, step = 50, threadnum = 1 ):
    
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
    
    except Exception as e :
        
        r['error'] = True
    
    finally :
        
        for i in range(threadnum) :
            q.put( None )
    
    return
    


def filler( dst, sql, q, xr={} ):
    
    conn = MySQLdb.connect( conv={}, **dst )
    
    try :
        
        while( True ):
            
            rs = q.get()
            
            if rs == None :
                break
                
            i = len(rs)
            
            conn.query( sql + ','.join( '(' + ','.join( '"'+MySQLdb.escape_string(str(v))+'"' if v != None else "NULL" for v in r ) + ')' for r in rs ) )
            
            conn.commit()
            
            xr['fillrows'] += i 
    
    except Exception as e :
        
        xr['error'] = True
        xr['traceback'].append(e)
    
    return



def dmprint( r ):
    print r

def datamove( src, dst, 
              src_cols = None, dst_cols = None, 
              convert = None, cond = None, 
              threadnum = 3, cb = None, t = 1 ):
    
    _src = src.copy()
    _dst = dst.copy()
    
    del _src['table']
    del _dst['table']
    
    cond = _src.pop( 'cond', cond )
    
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
    writesql = 'INSERT DELAYED IGNORE INTO `%s` (%s) VALUES ' % ( dst['table'], colssql(dst_cols) )
    
    if cond != None :
        readsql += (' WHERE ' + cond)

    r = {}
    q = Queue.Queue(200)

    cb( r )
    
    s = time.time()

    src_conn.query( readsql )
    
    e = time.time()
    
    r['querytime'] = e-s
    r['usedtime'] = 0
    
    s = e
    
    datas = src_conn.use_result()
    r['totalrows'] = datas.num_rows()
    #r['totalrows'] = src_conn.affected_rows()
    #r['info'] = src_conn.info()
    r['fill'] = [True]*threadnum
    r['fetch'] = True
    r['error'] = False
    r['traceback'] = []
    r['fillrows'] = 0
    r['fetchrows'] = 0
    r['interrupted'] = False
    
    cb( r )
    
    fe = threading.Thread( target = fetcher, 
                           args = ( datas, q, r ), 
                           kwargs = {'threadnum':threadnum} 
                         )
    fis = [ threading.Thread( target = filler, args=( _dst, writesql, q, r ) ) 
            for i in range(threadnum) ]
    
    fe.start()
    for fi in fis :
        fi.start()
    
    try :
        while( True ):
            
            r['fetch'] = fe.isAlive()
            r['fill'] = [ fi.isAlive() for fi in fis ]
            
            if cb :
                r['usedtime'] = time.time() - s
                cb( r )

            if r['fetch'] == False and not any(r['fill']) :
                break
                
            time.sleep(t)
    except Exception as e :
        r['interrupted'] = True
    finally :
        cb(r)
        
    fe.join()
    for fi in fis :
        fi.join()
        
    return
    