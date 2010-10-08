
import types
import unicodedata
import xml.sax.saxutils as saxutils

class Text( object ):
    
    def __init__( self, text ):
        
        self.texts = text.splitlines()
        
        return
        
    @staticmethod
    def _onelinelen( a ):
        
        if type(a) == types.StringType :
            return len(a)
        
        if type(a) == types.UnicodeType :
            return sum( [ 2 if unicodedata.east_asian_width(c).startswith('W') else 1 
                          for c in a ])
        
    def __len__( self ):
        
        return max( [ _onelinelen(l) for l in self.texts ] )
    

class Node( object ):
    
    def __init__( self, *contains, **styles ):
        
        self.contains = contains
        self.styles = styles
        
        return
        
    def _get_width_and_height( self ):
        
        return
        
    def _print_console_( self, width, height ):
        
        r = [ n._print_console() if hasattr( n, '_print_console_' )
                                    else str(n).splitlines() for n in contains ]
        
        return sum( r, [] )
        
    def _print_html_( self, ):
        
        r = [ n._print_console() if hasattr( n, '_print_console_' )
                          else '<br>'.join( [ saxutils.escape(ni) 
                                              for ni in str(n).splitlines() ] ) 
             for n in contains ]
        
        if r == [] :
            r = ['&nbsp;',]
        
        if len(r):
            
        return """<div style=>%s</div>""" % '\r\n'.join( [ ] )



class Bar( Node ):
    
    def __init__( self, number, text=None, **styles ):
        
        self.number = number
        self.contains = []
        self.styles = styles
        
    def _print_console_( self, width, height ):
        
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
                    self.covert.get( type(data), lambda x : x )
        
        data = cvrt(data)
        
        if type(data) not in ( types.ListType, types.Tuple ):
            return [( rk, pth, a ),]
        
        a = [ self._parse_inner( v, tuple(list(rk)+[k]), tuple(list(pth)+[i]) )
              for i, _a in enumerate(a) for k, v in _a.items() ]
        
        return sum( a, [] )
        
    def _parse( self, data ):
        
        
        
        return
