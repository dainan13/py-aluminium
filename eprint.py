
import types

class Node( object ):
    
    def __init__( self, *contains, **styles ):
        
        self.contains = contains
        self.styles = styles
        
        return
        
    def _print_console_( self ):
        
        r = [ n._print_console() if hasattr( n, '_print_console_' )
                                                else str(n) for n in contains ]
        
        return r
        
    def _print_html_( self, ):
        
        return


class EasyPrinter( object ):
    
    covert = {}
    
    def __init__( self, ):
        
        return
        
    def htmltable( self, ):
        
        return
        
    def eprint( self, ):
        
        return
        
    def _colssort( self, cols ):
        
        return
        
    def _parse_inner( self, data, rk=(), pth=(), strick=False, covert={} ):
        
        cvrt = covert.get( rk, lambda x : x )
        
        data = cvrt(data)
        
        cvrt = covert.get( type(data), None ) or \
                    self.covert.get( type(data), str )
        
        data = cvrt(data)
        
        if type(data) not in ( types.ListType, types.Tuple ):
            return [( rk, pth, a ),]
        
        a = [ self._parse_inner( v, tuple(list(rk)+[k]), tuple(list(pth)+[i]) )
              for i, _a in enumerate(a) for k, v in _a.items() ]
        
        return sum( a, [] )
        
    def _parse( self, data ):
        
        
        
        return
