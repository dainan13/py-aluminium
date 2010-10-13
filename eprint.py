
import types
import unicodedata
import xml.sax.saxutils as saxutils
from Al import realnum


"""
foreground
\033[38;5;(256colorcode)[;(my32bitcolorcode)]m
background
\033[48;5;(256colorcode)[;(my32bitcolorcode)]m
\033[0m
"""

class STREND(object):
    pass

class ColorString(object) :
    
    def __init__( self, s='', ascode=None, fg=None, bg=None ):
        
        self.s = unicode(s) if ascode == None else s.decode(ascode)
        self.displaylen = ColorString.displaylength(self.s)
        self.foreground = realnum.Line()
        self.background = realnum.Line()
        
        if fg.__class__ == realnum.Line :
            self.foreground = fg
        elif fg != None :
            self.fgcolor(fg)
        
        if bg.__class__ == realnum.Line :
            self.background = bg
        elif bg != None :
            self.bgcolor(bg)
        
    def fgcolor( self, color, s=0, e=STREND, mode='cover' ):
        
        e = self.displaylen if e == STREND else e
        
        if mode == 'cover' :
            self.foreground[s:e] = color
        elif mode == 'back' :
            self.foreground.merge(Line([(s,color),(e,None)]))
        else :
            raise ValueError, 'ColorString:foreground not supported the mode'
        
    def bgcolor( self, color, s=0, e=STREND, mode='cover' ):
        
        e = self.displaylen if e == STREND else e
        
        if mode == 'cover' :
            self.background[s:e] = color
        elif mode == 'back' :
            self.background.merge(Line([(s,color),(e,None)]))
        else :
            raise ValueError, 'ColorString:foreground not supported the mode'

    @staticmethod
    def displaylength( s ):
        return sum( 2 if unicodedata.east_asian_width(c).startswith('W') else 1 
                    for c in s if c not in "\r\n\b" )
    
    @staticmethod
    def colorsign( f, b ):
        if f == None and b == None:
            return '\033[0m'
        if f == None :
            return '\033[0m\033[48;5;%dm' % (b,)
        if b == None :
            return '\033[0m\033[38;5;%dm' % (f,)
        return '\033[38;5;%dm\033[48;5;%dm' % (f,b)
        
    def __str__( self ):
        
        P = self.foreground.zip( self.background, f = lambda x, y : ( x, y ) )
        
        #print self.foreground, self.background, P
        
        return ''.join( self.colorsign(f,b) + self.s[s:e].encode('utf-8') 
                        for s, e, (f, b) in P )
        
        #return self.s.encode('utf-8')
        
    def join( self, iterstr ):
        
        iterstr = [ ColorString(a) if a.__class__ != ColorString else a 
                    for a in iterstr ]
        
        s = self.s.join( a.s for a in iterstr )
        lentable = reduce( lambda x, y: x+[x[-1]+y,x[-1]+y+self.displaylen], 
                           (a.displaylen for a in iterstr), [0] )[:-1]
        
        xiterstr = [ aa for a in iterstr for aa in [a,self] ][:-1]
        
        fg = [ realnum.Line( [ ( k+lt if k !=None else None, v ) 
                               for k, v in a.foreground.tolist() ] ) 
               for lt, a in zip( lentable, xiterstr ) ]
        fg = reduce( lambda x, y: x.merge(y), fg, realnum.Line() )
        
        bg = [ realnum.Line( [ ( k+lt if k !=None else None, v ) 
                               for k, v in a.background.tolist() ] ) 
               for lt, a in zip( lentable, xiterstr ) ]
        bg = reduce( lambda x, y: x.merge(y), bg, realnum.Line() )
        
        #print fg, bg
        return ColorString( s, fg=fg, bg=bg )
        
    def __add__( self, another ):
        
        another = ColorString(another) \
                            if another.__class__ != ColorString else another
        
        s = self.s + another.s
        
        fg = self.foreground.merge( 
                realnum.Line( [ ( k+self.displaylen if k !=None else None, v ) 
                                for k, v in another.foreground.tolist() ] ) 
             )
             
        bg = self.background.merge( 
                realnum.Line( [ ( k+self.displaylen if k !=None else None, v ) 
                                for k, v in another.background.tolist() ] ) 
             )
        
        return ColorString( s, fg=fg, bg=bg )



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
        
    def _console_print_( self, w, h ):
        
        #fg = styles.get('color', None)
        bg = styles.get('background-color', None)
        
        return [ ColorString(' '*w, bg=bg ) for i in range(h) ]
        
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
            return sum( [ 2 if unicodedata.east_asian_width(c).startswith('W') \
                            else 1 
                          for c in a ])
        
    def _console_length_( self ):
        
        return max( [ _onelinelen(l) for l in self.texts ] )
            
    def _console_height_( self ):
        
        return len( self.text )
        
    def _console_print_( self, w, h, styles ):
        
        styles = styles.copy()
        styles.update(self.styles)
        
        v_alias = styles.get('vertical-align','top')
        if v_alias = 'top' :
            r = self.texts[:h] + ['']*max( h - len(self.texts), 0 )
        elif v_alias = 'bottom' :
            r = ['']*max( h - len(self.texts), 0 ) + self.texts[:h]
        elif v_alias = 'middle' :
            bt = ['']*max( (h - len(self.texts))/2, 0 )
            bb = ['']*max( h - bt - len(self.texts), 0 )
            r = bt + self.texts[:h]
            
        align = styles.get('align','left')
        if alias = 'left' :
            align = lambda s : ljust( s, w, ' ' )
        elif alias = 'right' :
            align = lambda s : rjust( s, w, ' ' )
        elif alias = 'center' :
            align = lambda s : center( s, w, ' ' )
        
        fg = styles.get('color', None)
        bg = styles.get('background-color', None)
        
        r = [ ColorString( align(l[:w]), fg=fg, bg=bg ) for l in in r ]
        
        return r
        
    def _html_print_( self, r, c, styles ):
        
        r = '<br>'.join([ saxutils.escape(l) for l in self.texts ])
        
        return '', '', r
    

class Bar( Node ):
    
    htmlclass = 'ep_Bar'
    
    def __init__( self, number, contain='', **styles ):
        
        self.number = number if number < 1 else 1
        self.contain = AutoNode(contain)
        super( Bar, self ).__init__( **styles )
        
    def _console_length_( self ):
        
        return self.contain._console_length_() + 2
        
    def _console_height_( self ):
        
        return self.contain._console_height_()
        
    def _console_print_( self, w, h, styles ):
        
        styles = styles.copy()
        styles.update(self.styles)
        
        r = [ ( ColorString(' ') + l + ColorString(' ') )
              for l in self.contain._console_print_( w, h, styles ) ]
        
        for l in r :
            
            l.bgcolor( styles.get('barcolor',237),
                       s=0,
                       e=int(l.displaylen*self.number),
                       mode='back',
                     ) 
        
        return r
        
        
    def _html_print_( self, r, c, styles ):
        
        _class, _styles, _to_print = self.contain._html_print_( r, c, styles )
        
        if _styles :
            _styles = 'style="%s"' % (_styles,)
        
        r = '<div style="width: %s%%"><div><div%s>' % \
                (int(self.number*100),_styles,)
        
        r = r + _to_print + </div></div></div>
        
        return htmlclass, '', r
        

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
        
        
if __name__ == '__main__' :
    
    a = ColorString('ABCDEFGHIJKLMNOPQRSTUVWSYZ')
    a.fgcolor( 200, e=10 )
    a.bgcolor( 150, s=5, e=15 )
    print a

    print ColorString('|',bg=237).join(['A','B','C'])
    print ColorString('hello',bg=90)+' world '+ColorString('!',fg=90)

