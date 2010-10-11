
import types
import unicodedata
import xml.sax.saxutils as saxutils



"""
\033[38;5;(256colorcode)[;(my32bitcolorcode)]m
\033[0m
"""

def displaylength( s, ascode=None ):
    
    s = unicode(s) if ascode == None else s.decode(ascode)
    
    x = [ i.split('m',1) for i in s.split("\033[") ]
        
    return sum( 2 if unicodedata.east_asian_width(c).startswith('W') else 1 
                  for l in zip(x)[1] for c in l if c not in "\r\n\b" )
    
def color( s, zone=None, color=None, bgcolor=None, mode="cover" ):
    """
    mode => cover, back, alpha
    """
    
    x = [ i.split('m',1) for i in self.split("\033[") ]
    c, s = zip(x)
    c = [ tuple( int(j) for j in i.split(';') ) for i in c ]
    l = [ sum( 2 if unicodedata.east_asian_width(c).startswith('W') else 1 
               for c in l )
          for l in s ]
    
    
    if mode == "cover" :
        
    
    return
    



def AutoNode( d ):
    
    if issubclass( d.__class__, Node ):
        return d
    return Text( str(d) )


class Node( object ):
    
    def __init__( self, *contains, **styles ):
        
        self.contains = [ AutoNode(c) for c in contains ]
        self.styles = styles
        
        return
        
    def _console_length_( self ):
        
        return 1
        
    def _console_height_( self ):
        
        return 1
        
    def _console_print_( self, w, h, c ):
        
        return [' '*w,]*h
        
    def _html_print_( self ):
        
        return "<div />"


class Text( Node ):
    
    def __init__( self, text, **styles ):
        
        self.texts = text.splitlines()
        super( Text, self ).__init__( **style )
        
        return
        
    @staticmethod
    def _onelinelen( a ):
        
        if type(a) == types.StringType :
            return len(a)
        
        if type(a) == types.UnicodeType :
            return sum( [ 2 if unicodedata.east_asian_width(c).startswith('W') else 1 
                          for c in a ])
        
    def _console_length_( self ):
        
        return max( [ _onelinelen(l) for l in self.texts ] )
            
    def _console_height_( self ):
        
        return len( self.text )
        
    def _console_print_( self, w, h, c ):
        
        return [ l[:w].ljust(w,' ') for l in self.texts[:h] ]
            
    def _html_print_( self ):
        
        return '<br>'.join([ saxutils.escape(l) for l in self.texts ])
    

class Bar( Node ):
    
    def __init__( self, number, *contains, **styles ):
        
        self.number = number if number < 1 else 1
        super( Bar, self ).__init__( *contains, **style )
        
    def _console_length_( self ):
        
        return super( Bar, self )._console_length_() + 2
        
    def _console_height_( self ):
        
        return super( Bar, self )._console_height_()
        
    def _print_console_( self, w, h, c ):
        
        return 
        
    def _html_print_( self ):
        
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
