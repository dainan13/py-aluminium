
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
    
    def __init__( self, nclses=[], styles = {}, nid=None,
                        *contains, **_styles ):
        
        self.contains = [ AutoNode(c) for c in contains ]
        
        self.styles = styles.copy()
        self.styles.update(_styles)
        self.nclses = nclses
        self.nid = nid
        
        return
        
    def _console_length_( self ):
        
        return 1
        
    def _console_height_( self ):
        
        return 1
        
    def _find_styles( self, stylesheet ):
        
        styles = {}
        
        for c in self.nclses :
            styles.update( stylesheet.get(c,{}) )
        
        styles.update(self.styles)
        
        return styles
        
    def _console_print_( self, w, h, stylesheet ):
        
        styles = self._find_styles(stylesheet)
        #fg = styles.get('color', None)
        bg = styles.get('background-color', None)
        
        return [ ColorString(' '*w, bg=bg ) for i in range(h) ]
        
    def _html_print_( self, pname='div' ):
        
        st = '' if st == {} else \
                 ( 'style="' + ';'.join( ('%s: %v' % x) for x in self.styles.items() ) + '"' )
        nid = 'id="%s"' % ( str(nid), ) if self.nid != None else '' 
        return '<%s %s %s />' % (pname,st,nid)
        #e = "</%s>" % (pname,)
        
    def add_node_cls( self, cls ):
        
        self.nclses += [cls]
        
        return


class Text( Node ):
    
    def __init__( self, text, **styles ):
        
        super( Text, self ).__init__( **styles )
        
        self.texts = text.splitlines()
        
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
        
        return max( [ self._onelinelen(l) for l in self.texts ] )
            
    def _console_height_( self ):
        
        return len( self.texts )
        
    def _console_print_( self, w, h, stylesheet ):
        
        #styles = styles.copy()
        #styles.update(self.styles)
        styles = self._find_styles(stylesheet)
        
        v_align = styles.get('vertical-align','top')
        if v_align == 'top' :
            r = self.texts[:h] + ['']*max( h - len(self.texts), 0 )
        elif v_align == 'bottom' :
            r = ['']*max( h - len(self.texts), 0 ) + self.texts[:h]
        elif v_align == 'middle' :
            bt = ['']*max( (h - len(self.texts))/2, 0 )
            bb = ['']*max( h - bt - len(self.texts), 0 )
            r = bt + self.texts[:h]
            
        align = styles.get('align','left')
        if align == 'left' :
            align = lambda s : s.ljust( w, ' ' )
        elif align == 'right' :
            align = lambda s : s.rjust( w, ' ' )
        elif align == 'center' :
            align = lambda s : s.center( w, ' ' )
        
        fg = styles.get('color', None)
        bg = styles.get('background-color', None)
        
        r = [ ColorString( align(l[:w]), fg=fg, bg=bg ) for l in r ]
        
        return r
        
    def _html_print_( self, pname='div' ):
        
        r = '<br>'.join([ saxutils.escape(l) for l in self.texts ])
        
        st = '' if st == {} else \
                 ( 'style="' + ';'.join( ('%s: %v' % x) for x in self.styles.items() ) + '"' )
        nid = 'id="%s"' % ( str(nid), ) if self.nid != None else '' 
        
        return '<%s %s %s>%s</%s>' % (pname,st,nid,r,pname)
    

class Bar( Node ):
    
    def __init__( self, number, contain='', **styles ):
        
        super( Bar, self ).__init__( **styles )
        
        self.number = number if number < 1 else 1
        self.contain = AutoNode(contain)
        self.add_node_cls('epBar')
        
    def _console_length_( self ):
        
        return self.contain._console_length_() + 2
        
    def _console_height_( self ):
        
        return self.contain._console_height_()
        
    def _console_print_( self, w, h, stylesheet ):
        
        #styles = styles.copy()
        #styles.update(self.styles)
        styles = self._find_styles(stylesheet)
        
        r = [ ( ColorString(' ') + l + ColorString(' ') )
              for l in self.contain._console_print_( w, h, styles ) ]
        
        for l in r :
            
            l.bgcolor( styles.get('barcolor',237),
                       s=0,
                       e=int(l.displaylen*self.number),
                       mode='back',
                     ) 
        
        return r
        
    def _html_print_( self, pname='div' ):
        
        r = self.contain._html_print_( 'div' )
        
        st = '' if st == {} else \
                 ( 'style="' + ';'.join( ('%s: %v' % x) for x in self.styles.items() ) + '"' )
        nid = 'id="%s"' % ( str(nid), ) if self.nid != None else '' 
        
        return """\
<%s %s %s>
<div style="width: %s%%">
<div>
%s
</div>
</div>
</%s>""" % (pname,st,nid,int(self.number*100),r,pname)
        

class Table( Node ):
    
    def __init__( self, contains=[], headers=[], **styles ):
        
        #self.number = number if number < 1 else 1
        super( Table, self ).__init__( **styles )
        
        self.contains = contains
        self.headers = headers
        self.x_max = max( (x+l) for x, y, l, h, n in contains )
        self.y_max = max( (y+h) for x, y, l, h, n in contains )
        self.add_node_cls('epTable')
        
    def _console_length_( self ):
        
        return
        
    def _console_height_( self ):
        
        return
        
    def _console_print_( self, w=None, h=None, stylesheet={} ):
        
        styles = self._find_styles(stylesheet)
        
        lenmatrix = [ ( x, y, l, h, n._console_length_(), n._console_height_() )
                      for x, y, l, h, n in self.contains ]
        
        directx = [ max( cl for x, y, l, h, cl, ch in lenmatrix if l == 1 and x == _x ) 
                    for _x in range(self.x_max) ]
        
        directy = [ max( ch for x, y, l, h, cl, ch in lenmatrix if h == 1 and y == _y ) 
                    for _y in range(self.y_max) ]
        
        indirectx = [ zip( range(x,x+l), self._adjust( cl-l+1, l, directx[x:x+l] ) )
                      for x, y, l, h, cl, ch in lenmatrix if l != 1 ]
        
        indirecty = [ zip( range(y,y+h), self._adjust( ch, h, directx[y:y+h] ) )
                      for x, y, l, h, cl, ch in lenmatrix if h != 1 ]
        
        indirectx = sum(indirectx,[])
        indirecty = sum(indirecty,[])
        
        maxx = [ max([ v for x, v in indirectx if x == _x ] + [directx[x]]) 
                 for _x in range(self.x_max) ]
        
        maxy = [ max([ v for y, v in indirecty if y == _y ] + [directy[y]]) 
                 for _y in range(self.y_max) ]
        
        
        tp = [ ( x, y, l, h, n._console_print_( sum(maxx[x:x+l]) , 
                                                sum(maxy[y:y+h]) , 
                                                stylesheet ) ) 
               for x, y, l, h, n in self.contains
             ]
            
        tp = [ [ ( x, y+i, l, h, c[sum(maxy[y:y+i]):][:maxy[i]] ) for i in range(l) ] 
               for x, y, l, h, c in tp ]
        
        tp = sum(tp,[])
        
        rows = [ [ ( x, c ) for x, y, l, h, c in tp if y == _y ] for _y in range(self.y_max) ]
        
        #print 
        
        for row in rows :
            row.sort( key = lambda r : r[0] )
            #for l in row :
            #    print l
        
        rows = [ [ c for x, c in row ] for row in rows ]
        
        lines = [ ColorString(': ') \
                    + ColorString(' | ',bg=237).join(l) \
                    + ColorString(' :') 
                  for row in rows for l in zip(*row) ]
        
        return lines
        
    @staticmethod
    def _adjust( d, ds, n ):
        
        avg = (d+ds-1) / ds ;
        
        m = [ x if x > avg else 0 for x in n ]
        
        a = d - sum(m)
        
        z = sum( 1 if x == 0 else 0 for x in m )
        
        if z == 0 or a < 0 :
            return n
        
        p = [a/z]*(z-1) + [a%z]
        
        return [ x if x > avg else (x+p.pop()) for x in n ]
        
    def _html_print_( self, ):
        
        #
        # +-------+---------------+-------------+
        # |       |       X       |             |
        # |   X   +-------+-------+      X      |
        # |       |   X   |   X   |             |
        # +-------+-------+-------+-------------+
        #
        #
        

        
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
        
        if type(data) not in ( types.ListType, types.TupleType ):
            return [( rk, pth, AutoNode(data) ),]
        
        a = [ self._parse_inner( v, tuple(list(rk)+[k]), tuple(list(pth)+[i]) )
              for i, _a in enumerate(data) for k, v in _a.items() ]
        
        return sum( a, [] )
        
    def _parse( self, data, covert={}, format={} ):
        '''
        convert :
        
        format :
        ( A, (A2,A1) ) : None
        ( C, ) : under(A, )
        ( D, ) : inner(B, )
        
        +---------+---------+
        |    A    |    B    |
        +----+----+---------+
        | A2 | A1 |    D    |
        +---------+---------+
        |    C    |         |
        +---------+---------+
        
        '''
        
        tbv = self._parse_inner( data, covert=covert )
        
        ks = list(set( k for k, pth, v in tbv ) )
        ks.sort()
        
        kcs = [ ( k, sum( 1 for _k in ks 
                            if len(_k) > len(k) and _k[:len(k)] == k ) ) 
                for k in ks ]
        
        #        key end  cols
        kcs = [ ( k, c==0, max(c,1) ) for k, c in kcs ]
        
        colnum = [ ( 1 if e else 0 ) for k, e, c in kcs ]
        colnum = reduce( lambda x, y : x+[x[-1]+y], colnum, [0] )
        
        colnum, colsum = colnum[:-1], colnum[-1]
        #colsum = sum( 1 for k, e, c in kcs if e )
        
        rowmax = max( len(k) for k in ks )
        
        #tbs_k = [ [ ( rowmax-len(k)+1 if e else 1 , c, k[-1] ) 
        #            for k, e, c in kcs if len(k) == r+1 ] 
        #          for r in range(rowmax) ]
        
        # x, y, cols, rows, node
        t = [ ( x, len(k)-1, c, rowmax-len(k)+1, Text(k[-1]) ) 
              for ( k, e, c ), x in zip( kcs, colnum )  ]
        
        tbl = Table( contains = t )
        r = tbl._console_print_()
        
        for l in r :
            print l
        
        return
        
        
if __name__ == '__main__' :
    
    a = ColorString('ABCDEFGHIJKLMNOPQRSTUVWSYZ')
    a.fgcolor( 200, e=10 )
    a.bgcolor( 150, s=5, e=15 )
    print a

    print ColorString('|',bg=237).join(['A','B','C'])
    print ColorString('hello',bg=90)+' world '+ColorString('!',fg=90)
    
    print u'\u2714'
    print u'\u28ff'
    
    print
    print
    print
    
    d = [ { 'colA' : 'A.1.alpha\r\nA.1.beta' ,
            'colB' : 'B.1.alpha\r\nB.1.beta\r\nB.1.gamma\r\nB.1.delta' },
          { 'colA' : 'A.2.alpha\r\nA.2.beta' ,
            'colB' : [{'B.2.alpha':'z','B.1':'qew' }] },
        ]
    
    ep = EasyPrinter()
    ep._parse(d)

