
import types





def getcols( data, level = 2 ):
    
    cols = {}
    
    # breadth-first traversal
    
    s = [ ( data, 0, cols ), ]
    
    while( len(s)!=0 ):
        
        v, lv, r = s.pop(0)
        
        if lv > level :
            continue
        
        if type(v) not in ( types.ListType, types.TupleType ) :
            v = [v,]
            
        for vi in v :
            
            if type(vi) != types.DictType :
                continue
            
            for k in vi.keys():
                r.setdefault( k, {} )
                s.append( ( vi[k], lv+1, r[k] ) )
    
    return cols


def _xzip( matrix ):
    
    maxlen = max( [ len(r) for r in matrix ] )
    m2 = [ r + ['',]*(maxlen-len(r)) for r in matrix ]
    
    return zip(m2)

def _format( v, cols ):
    
    if cols == {} :
        return str(v).splitlines()
        
    if type(data) not in ( types.ListType, types.TupleType ) :
        v = [v,]
        
    r = []
    
    for vi in v :
        
        if type(vi) != types.DictType :
            r.append( _format( vi, {} ) )
            
        r.append( _format( vi, cols[k] ) for k in cols.keys() )
    
    return _xzip(r)

def easyprint( data, cols = None ):
    
    # get the cols if not fixed
    if cols == None :
        cols = getcols( data )
    elif type(cols) == types.IntType :
        cols = getcols( data, cols )
        
    if data not in ( types.ListType, types.TupleType ):
        data = [data,]
        
    for r in data :
        r = [ r.get( k, '' ) for k in cols.keys() ]
        
    return

if __name__ == '__main__' :
    
    a = [ { 'colA' : ['A','B','C','D'], 'colB' : ['A','B','C'] },
          { 'colA' : ['A','B'] , 'colB' : 'A\r\nB\r\nC\r\nD' },
          { 'colA' : ['A\r\nB','C\r\nD'] , 'colB' : 'A\r\nB\r\nC\r\nD' },
        ]
    
    b = [ { 'col A' : 'A.1', 'col B': 'B.1' },
          { 'col A' : 'A.2', 'col B': {'subcol A': 'B.A.2', 'subcol B': 'B.A.2'} },
        ]
    
    print getcols(a)
    print getcols(b)