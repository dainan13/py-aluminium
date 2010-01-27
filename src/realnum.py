import types

class Infinity(object):
    
    def __init__( self ):
        pass
    
    def F ( self, another ):
        return False
    
    def T ( self, another ) :
        return True
    
    __gt__ = T
    __ge__ = T
    
    __lt__ = F
    __le__ = F
    
    def __eq__ ( self, another ):
        return type(another) == Infinity
        
    def __ne__ ( self, another ):
        return type(another) != Infinity
        
    def __hash__( self ):
        return hash('3e656e07-36de-4e06-b79d-ec87dfc8f3fa')

Inf = Infinity()



class F(object):
    
    def __init__( self, factors ):
        
        self.factors = factors
        
    def __quadrature__( self ):
        
        return F( [ float(fa)/(i+1) for i, fa in enumerate(self.factors) ] )


class Line(object):
    
    def __init__( self, sttdict={None:None} ):
        
        if type(sttdict) != types.DictType :
            sttdict = dict(sttdict)
        
        self.point = sttdict.copy()
        
        if None not in self.point :
            self.point[None] = None
        
        self.nodes = self.point.keys()
        self.nodes.sort()
        
        return
        
    def delslice( self, start, stop ):
        
        if stop == None :
            stop = Inf
            
        ks = self.nodes
        
        seg = [ k for k in ks if k >= start and k < stop and k != None ]
        before = max( [ k for k in ks if k < start ] + [None,] )
        after = min( [ k for k in ks if k >= stop ] + [Inf,] )
        
        if after != stop or stop != Inf :
            v = self.point[seg[-1] if seg!=[] else before]
            if v != None :
                self.point[stop] = v
        
        for s in seg :
            del self.point[s]
        
        if self.point[before] != None :
            self.point[start] = None
        
        self.nodes = self.point.keys()
        self.nodes.sort()
        
        return
        
    def setslice( self, start, stop, value ):
        
        if stop == None :
            stop = Inf
        
        ks = self.nodes
        
        seg = [ k for k in ks if k >= start and k < stop and k != None ]
        before = max( [ k for k in ks if k < start ] + [None,] )
        after = min( [ k for k in ks if k >= stop ] + [Inf,] )
        
        if after != stop and stop != Inf :
            v = self.point[seg[-1] if seg!=[] else before]
            if v != value :
                self.point[stop] = v
        
        for s in seg :
            del self.point[s]
        
        if self.point[before] != value :
            self.point[start] = value
        
        self.nodes = self.point.keys()
        self.nodes.sort()
        
        return
    
    def getslice( self, start, stop ):
        
        if slice.stop == None :
            slice.stop = Inf
        
        ks = self.nodes
        
        seg = [ k for k in ks if k >= start and k < stop and k != None ]
        before = max( [ k for k in ks if k <= start ] + [None,] )
        after = min( [ k for k in ks if k >= stop ] + [Inf,] )
        
        r = [ ( s, self.point[s] ) for s in seg ]
        
        if ( seg == [] or seg[0] != start ) and before != None :
            r = [(start, self.point[before]),]+r
        
        if stop != Inf :
            r = r + [ (stop, None), ]
        
        return Line(dict(r))
    
    def __setitem__( self, key, value ):
        if type(key) != types.SliceType :
            raise ValueError, 'Line must using slice'
        
        return self.setslice( key.start, key.stop, value )
    
    def __delitem__( self, key ):
        if type(key) != types.SliceType :
            raise ValueError, 'Line must using slice'
        
        return self.delslice( key.start, key.stop )
    
    def __getitem__( self, key ):
        
        if type(key) == types.SliceType :
            return self.getslice( key.start, key.stop )
        
        before = max( [ k for k in self.nodes if k <= key ]+[None,] )
        
        return self.point[before]
        
    def __repr__( self ):
        
        z = [ (k, v) for k, v in self.point.items() if k != None or v != None ]
        z.sort(key = lambda x : x[0])
        
        return 'Line('+repr(z)+')'
        
    def __str__( self ):
        
        return self.__repr__()
        
    def __eq__( self ):
        return self.point == another.point
    
    def __ne__( self, another ):
        return self.point != another.point
    
    @staticmethod
    def _zip( a, b ):
        return (a,b) if None not in (a,b) else None
    
    def xzip( self, another ):
        return self.zip( another, 
                         lambda a,b : (a,b) if a != None or b!=None else None )
    
    def zip( self, another, f=None ):
        
        if f == None :
            f = self._zip
        
        start = min(self.nodes)
        stop = max(self.nodes)
        
        if self.point[stop] == None :
            stop = Inf
        
        # A    B       C                   D
        # |----|--|----|---|--------|------|
        #         M        N        O
        
        nodes = list(set(self.nodes + another.nodes))
        nodes.sort()
        
        nodes_s = [ max([ _p for _p in self.nodes if _p <= p ])
                    for p in nodes ]
        
        nodes_a = [ max([ _p for _p in another.nodes if _p <= p ])
                    for p in nodes ]
        
        value = [ ( n, f( self.point[ns], another.point[na] )
                  ) for n, ns, na in zip( nodes, nodes_s, nodes_a )]
        
        filter = set([ _v[0] for v, _v in zip( value, value[1:])
                       if v[1] == _v[1] ])
        
        value = [ (k, v) for k, v in value if k not in filter]
        
        return Line(value)
    
    def map( self, vf, kf=None ):
        
        if kf == None :
            kf = lambda x : x
        
        if vf == None :
            vf = lambda x : x
        
        r = [ ( kf(k), None if v == None else vf(v) )
              for k, v in self.point.items() ]
        
        return dict(r)
    
    @staticmethod
    def _add( a, b ):
        if a == None:
            return None
        if b == None :
            return a
        return a+b
    
    @staticmethod
    def _sub( a, b ):
        if a == None :
            return None
        if b == None :
            return a
        return a-b
    
    @staticmethod
    def _stripby( a, b ):
        return None if a == None or b == None else a
    
    @staticmethod
    def _update( a, b ):
        return b if b != None else a
    
    @staticmethod
    def _merge( a, b ):
        return b if a == None else a
    
    @staticmethod
    def _diff( a, b ):
        return a if a != b else None
    
    def __add__( self, another ):
        
        if type( another ) == Line :
            return self.zip( another, self._add )
        
        return self.map( None, lambda x: x+another )
        
    def __sub__( self, another ):
        
        if type( another ) == Line :
            return self.zip( another, self._sub )
        
        return self.map( None, lambda x: x-another )
        
    def update( self, another ):
        return self.zip( another, self._update )
        
    def stripby( self, another ):
        return self.zip( another, self._stripby )
    
    def merge( self, another ):
        return self.zip( another, self._merge )
    
    def diff( self, another ):
        return self.zip( another, self._diff )
        
    def __iter__( self ):
        
        for ns, ne in zip( self.nodes, self.nodes[1:]+[None,] ) :
            if self.point[ns] == None :
                continue
            yield ns, ne, self.point[ns]
            
    def iscontinuous( self ):
        
        return all( [ self.point[n] != None for n in self.nodes[:-1] ] )
        
    def iscomplete( self, start, stop ):
        
        stop = stop or Inf
        
        return all( [ self.point[n] != None for n in self.nodes
                      if n >= start and n < stop ] )
        
    def split( self ):
        
        return [ Line([(ns,x),(ne,None)])
                    if ne != None else
                 Line([(ns,x)])
                 for ns, ne, x in self if x != None ]
        
    def left( self, key=None ):
        
        if key == None :
        
            if self.point[None] != None:
                return None
            
            r = min(self.nodes)
            
            if r == None :
                raise ValueError, 'Empty Line can\'t get the boundary'
            
            return r
    
        return max( [ k for k in key if k <= start ] + [None,] )
        
    
    def right( self, key=Inf ):
        
        if key == Inf :
        
            if self.point[self.nodes[-1]] != None:
                return None
            
            r = max(self.nodes)
            
            if r == None :
                raise ValueError, 'Empty Line can\'t get the boundary'
            
            return r
        
        return min( [ k for k in key if k > stop ] + [Inf,] )
        
    def getslice( self, key ):
        return slice( self.left(key), self.right(key) )
        
    def before ( self, key ):
        return max( [ k for k in key if k <= start ] + [None,] )
        
    def after( self, key ):
        return min( [ k for k in key if k >= stop ] + [Inf,] )
    
    def __len__( self ):
        
        if self.point[None] != None or self.point[self.nodes[-1]] != None :
            return None
        
        return reduce( lambda x, y : x+y ,
                       [ ne - ns for ns, ne, x in self if x != None  ] )
    
    @staticmethod
    def _q( a, b, precision ):
        
        r = a
        while ( r < b ):
            yield r
            r += precision
    
    @staticmethod
    def _quadrature( v, a, b, precision=0.1 ):
        
        q = getattr( v, '__quadrature__', None )
        if q != None :
            return q(b) - q(a)
        
        if callable(v) :
            
            s = [ v(i)*precision for i in Line._q( a, b, precision ) ]
            
            return reduce( lambda x, y : x+y , s )
        
        return v*(b-a)
    
    def quadrature( self, precision=0.1 ):
        
        if self.point[None] != None or self.point[self.nodes[-1]] != None :
            return None
        
        return reduce( lambda x, y : x+y ,
                       [ self._quadrature( x, ns, ne, precision )
                         for ns, ne, x in self if x != None  ]
                     )
    
    def countsegment( self ):
        
        return len( [ n for n in self.nodes if self.point[n]!=None ] )
        
    def tolist( self ):
        
        z = [ (k, v) for k, v in self.point.items() if k != None or v != None ]
        z.sort(key = lambda x : x[0])
        
        return z
    
    def todict( self ):
        
        z = [ (k, v) for k, v in self.point.items() if k != None or v != None ]
        
        return dict(z)
        
    def isempty( self ):
        
        if len(self.nodes) == 1 and self.point[None] == None :
            return True
        
        return False





if __name__ == '__main__' :
    
    print 'create a Line '\
          '[0,20) = \'A\', [20,25) = \'B\', [25,Infinty) = \'C\' '
    l = Line( {0:'A',20:'B',25:'C'} )
    
    print '''
    A...................B....C......................
    |---------|---------|----|----|---------------->
    0        10        20   25   30
    '''
    
    print 'l :', l
    
    
    print 'l[-1] :', l[-1]
    print 'l[1] :', l[1]
    print 'l[22] :', l[22]
    
    print
    print
    
    print 'subsegmentset '
    print '''
    A...................B....C......................
    |---------|---------|----|----|---------------->
    0        10        20   25   30
           |<---- sub --->|
           A............B.|
    |------|--|---------|-|--|----|---------------->
    0        10        20   25   30
    '''
    print 'l[7:22] :', l[7:22]
    
    print
    print
    
    
    print 'delete segment form 15 to 27, [15,27)\'s value as None'
    del l[15:27]
    
    print '''
                   |<-Removed->|
    A..............|           C....................
    |---------|----|----|----|-|--|---------------->
    0        10   15   20   25   30
    '''
    
    print 'l :', l
    
    print
    print
    
    print 'operate of Line'
    print '''
    ........ Line A 
    """""""" Line B
       |
    20 |              """"""""""
    15 |         ..........     """""""""""""""""""""""
    10 |    """"""""""     ............................
     5 |.........
       |----:----|----:----|----:----|---------------->
       0    5   10   15   20   25   30
    
    
    +++++ A + B, ----- A - B
       |
    35 |              +++++
    30 |                   +++++
    25 |         +++++          +++++++++++++++++++++++
    20 |              
    15 |    +++++
    10 |         
     5 |+-+-     -----
     0 |
    -5 |    -----     -----     -----------------------
    -10|                   -----
       |----:----|----:----|----:----|---------------->
       0    5   10   15   20   25   30
    '''
    
    A = Line( {0:5,10:15,20:10} )
    B = Line( {5:10,15:20,25:15} )
    
    print 'A+B :', A+B
    print 'A-B :', A-B
    
    print 'A.countsegment() :', A.countsegment()
    print 'A.stripby(B) :', A.stripby(B)
    print 'A.diff(A+B) :', A.diff(A+B)
    print 'B.merge(A) :', B.merge(A)
    print 'A[0:25].quadrature() :', A[0:25].quadrature()
    
    