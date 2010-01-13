
import types

from pprint import pprint



def _coltree( Name, d ):
    return ( Name, {}, tuple( _coltree(k, v) for k, v in d.items() ) )

def _coldata( t ):
    
    if t[2] == ():
        return t[0]
    
    return [ t[0], dict([ (v[0], _coldata(v)) for v in t[2] ]) ]

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
    
    return _coltree( '', cols )


def _xzip( matrix ):
    
    maxlen = max( [ len(r) for r in matrix ] )
    m2 = [ r + ['',]*(maxlen-len(r)) for r in matrix ]
    
    return zip(*m2)


def _format( v, cols ):
    
    if cols == None or cols[2] == () :
        return str(v).splitlines()
        
    if type(v) not in ( types.ListType, types.TupleType ) :
        v = [v,]
        
    r = []
    
    for vi in v :
        
        if type(vi) == types.DictType :
            ri = [ _format( vi[subc[0]], subc ) if subc[0] in vi else ''
                   for subc in cols[2] ]
            r.append( _xzip(ri) )
        else :
            r.append( _format( vi, None ) )
    
    return sum(r,[])



def _width( v, cols ):
    
    if type(v) == types.TupleType :
        r = sum( [ _width( vi, cols[2][i] ) for i, vi in enumerate(v) ] )
        r += len(v)-1
    else :
        r = len(v)
    
    cols[1]['__width__'] = max( cols[1].get('__width__',len(cols[0])), r )
    
    return cols[1]['__width__']
    
def width( v, cols ):
    
    for vi in v :
        _width( vi, cols )
    
    return

def _print( v, cols ):
    
    if type(v) == types.TupleType :
        return ' '.join([ _print(vi, cols[2][i]) for i, vi in enumerate(v) ])
    else :
        return v.ljust(cols[1]['__width__'])

def eprint( v, cols ):
    
    for vi in v :
        print _print( vi, cols )

def easyprint( data, cols = None ):
    
    # get the cols if not fixed
    if cols == None :
        cols = getcols( data )
    elif type(cols) == types.IntType :
        cols = getcols( data, cols )
    
    #print cols
    
    fdata = _format( data, cols )
    width( fdata, cols )
    
    cdata = _coldata( cols )
    cdata = _format( cdata, cols )
    
    eprint( cdata, cols )
    print '-'*cols[1]['__width__']
    eprint( fdata, cols )
    
    return







if __name__ == '__main__' :
    
    a = [ { 'colA' : ['A','B','C','D'], 'colB' : ['A','B','C'] },
          { 'colA' : ['A','B'] , 'colB' : 'A\r\nB\r\nC\r\nD' },
          { 'colA' : ['A\r\nB','C\r\nD'] , 'colB' : 'A\r\nB\r\nC\r\nD' },
        ]
    
    b = [ { 'col A' : 'A.1', 'col B': 'B.1' },
          { 'col A' : 'A.2', 'col B': {'subcol A': 'B.A.2', 'subcol B': 'B.B.2'} },
        ]
    
    c = [ { 'col A' : 'A.1', 'col B': 'B.1' },
          { 'col A' : 'A.2', 'col B': 'B.2' },
        ]
    
    d = [ { 'colA' : 'A.1.alpha\r\nA.1.beta' ,
            'colB' : 'B.1.alpha\r\nB.1.beta\r\nB.1.gamma\r\nB.1.delta' },
          { 'colA' : 'A.2.alpha\r\nA.2.beta' ,
            'colB' : 'B.2.alpha' }
        ]
    
    #easyprint(a)
    easyprint(b)
    print
    easyprint(c)
    print
    easyprint(d)