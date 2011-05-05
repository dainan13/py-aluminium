#!/usr/bin/env python2.6
# coding: utf-8

import types
import unicodedata
import re

from pprint import pprint

def safestr( a ):
    
    if type(a) == types.UnicodeType :
        return a
    
    return unicode( str(a), 'utf-8', 'replace' ).replace('\ufffd','\u00b7')
    
def safelen( a ):
    
    if type(a) == types.StringType :
        return len(a)
    
    if type(a) == types.UnicodeType :
        return sum( [ 2 if unicodedata.east_asian_width(c).startswith('W') else 1 
                      for c in a ])
    
    raise Exception, a
    


def _namescore( name ):
    
    score = 0
    
    name = name.lower()
    
    if name in ( '!','#' ) :
        score += 150
    
    if name.endswith('id') :
        score += 100
        score -= len(name)-2
    
    if name.endswith('name') :
        score += 80
        score -= len(name)-4
    
    if name.startswith('last-') :
        score -= 50
        score -= len(name)-5
        
    if name.find('data') != -1 or name.find('time') != -1 :
        score -= 50
        score -= len(name)-5
    
    if name.find('url') != -1 or name.find('address') != -1 :
        score -= 30
        score -= len(name)-5
    
    return -score

def smartsort( kvpair ):
    
    l = kvpair[:]
    
    l.sort( key = lambda x : [_namescore(x[0]),x[0]] )
    
    return l



def _coltree( Name, d ):
    return ( Name, {}, tuple( _coltree(k, v)
                              for k, v in smartsort( d.items() )
                            )
           )

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
    m2 = [ list(r) + ['',]*(maxlen-len(r)) for r in matrix ]
    
    return zip(*m2)


def _format( v, cols ):
    
    if cols == None or cols[2] == () :
        return safestr(v).splitlines()
        
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
        r = safelen(v)
    
    cols[1]['__width__'] = max( cols[1].get('__width__',safelen(cols[0])), r )
    
    return cols[1]['__width__']
    
def _colwidth( cols ):
    
    
    cols[1]['__width__'] = max( cols[1].get('__width__'),
                                sum( [ _colwidth(c)+1  for c in cols[2] ] ) -1,
                                *[ safelen(l) for l in cols[0].splitlines()]
                           )
    
    return cols[1]['__width__']

def width( v, cols ):
    
    _colwidth(cols)
    
    for vi in v :
        _width( vi, cols )
    
    
    return

def _print( v, cols ):
    
    if type(v) == types.TupleType :
        return ' '.join([ _print(vi, cols[2][i]) for i, vi in enumerate(v) ])
    else :
        j = cols[1].get( '__just__', 'left' )
        if callable(j):
            j = j(v)
        
        #if j == 'right' :
        #    return v.rjust(cols[1]['__width__'])
        #elif j == 'center' :
        #    return v.center(cols[1]['__width__'])
        #    
        #return v.ljust(cols[1]['__width__'])
        if j == 'right' :
            return ' '*(cols[1]['__width__'] - safelen(v))+v
        elif j == 'center' :
            n = (cols[1]['__width__'] - safelen(v))/2
            m = cols[1]['__width__'] - n
            return ' '*m+v+' '*n
        return v + ( ' '*(cols[1]['__width__'] - safelen(v)) )

def eprint( v, cols ):
    
    for vi in v :
        print _print( vi, cols )
        
def eformat( v, cols ):
    
    return '\r\n'.join( [ _print( vi, cols ) for vi in v ] )
    

def ifdict( di ):
    
    return [ { 'Key':k, 'Value':v } for k, v in di.items() ]

def easyprint( data, cols = None ):
    
    if type(data) == types.DictType :
        data = ifdict(data)
    
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


def easyformat( data, cols = None ):
    
    if type(data) == types.DictType :
        data = ifdict(data)
    
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
    
    r = [ eformat( cdata, cols ),
          '-'*cols[1]['__width__'],
          eformat( fdata, cols ) ]
    
    return '\r\n'.join(r)




#
#⠀ ⠁ ⠂ ⠃ ⠄ ⠅ ⠆ ⠇ ⠈ ⠉ ⠊ ⠋ ⠌ ⠍ ⠎ ⠏ ⠐ ⠑ ⠒ ⠓ ⠔ ⠕ ⠖ ⠗ ⠘ ⠙ ⠚ ⠛ ⠜ ⠝ ⠞ ⠟ 
#⠠ ⠡ ⠢ ⠣ ⠤ ⠥ ⠦ ⠧ ⠨ ⠩ ⠪ ⠫ ⠬ ⠭ ⠮ ⠯ ⠰ ⠱ ⠲ ⠳ ⠴ ⠵ ⠶ ⠷ ⠸ ⠹ ⠺ ⠻ ⠼ ⠽ ⠾ ⠿ 
#⡀ ⡁ ⡂ ⡃ ⡄ ⡅ ⡆ ⡇ ⡈ ⡉ ⡊ ⡋ ⡌ ⡍ ⡎ ⡏ ⡐ ⡑ ⡒ ⡓ ⡔ ⡕ ⡖ ⡗ ⡘ ⡙ ⡚ ⡛ ⡜ ⡝ ⡞ ⡟ 
#⡠ ⡡ ⡢ ⡣ ⡤ ⡥ ⡦ ⡧ ⡨ ⡩ ⡪ ⡫ ⡬ ⡭ ⡮ ⡯ ⡰ ⡱ ⡲ ⡳ ⡴ ⡵ ⡶ ⡷ ⡸ ⡹ ⡺ ⡻ ⡼ ⡽ ⡾ ⡿ 
#⢀ ⢁ ⢂ ⢃ ⢄ ⢅ ⢆ ⢇ ⢈ ⢉ ⢊ ⢋ ⢌ ⢍ ⢎ ⢏ ⢐ ⢑ ⢒ ⢓ ⢔ ⢕ ⢖ ⢗ ⢘ ⢙ ⢚ ⢛ ⢜ ⢝ ⢞ ⢟ 
#⢠ ⢡ ⢢ ⢣ ⢤ ⢥ ⢦ ⢧ ⢨ ⢩ ⢪ ⢫ ⢬ ⢭ ⢮ ⢯ ⢰ ⢱ ⢲ ⢳ ⢴ ⢵ ⢶ ⢷ ⢸ ⢹ ⢺ ⢻ ⢼ ⢽ ⢾ ⢿ 
#⣀ ⣁ ⣂ ⣃ ⣄ ⣅ ⣆ ⣇ ⣈ ⣉ ⣊ ⣋ ⣌ ⣍ ⣎ ⣏ ⣐ ⣑ ⣒ ⣓ ⣔ ⣕ ⣖ ⣗ ⣘ ⣙ ⣚ ⣛ ⣜ ⣝ ⣞ ⣟ 
#⣠ ⣡ ⣢ ⣣ ⣤ ⣥ ⣦ ⣧ ⣨ ⣩ ⣪ ⣫ ⣬ ⣭ ⣮ ⣯ ⣰ ⣱ ⣲ ⣳ ⣴ ⣵ ⣶ ⣷ ⣸ ⣹ ⣺ ⣻ ⣼ ⣽ ⣾ ⣿ 
#

chartchar = [ u'\u2800\u2880\u28a0\u28b0\u28b8',
              u'\u2840\u28C0\u28E0\u28F0\u28F8',
              u'\u2844\u28C4\u28E4\u28F4\u28FC',
              u'\u2846\u28C6\u28E6\u28F6\u28FE',
              u'\u2847\u28C7\u28E7\u28F7\u28FF',
            ]

chartline = '⣀⠤⠒⠉'.decode('utf-8')
chartlinex = '⡀⠄⠂⠁'.decode('utf-8')

SIprefixes = " kMGTPEZY"
IECprefixes = ["  ", "Ki","Mi","Gi","Ti","Pi","Ei","Zi","Yi"]

def humanreadable( a, f=2, iec=False ):
    
    p = 1024 if iec else 1000
    
    s = '%%.%df%%s' % (f,)
    
    for i in range(8,0,-1):
        z = float(a) / (p**i)
        if z >= 1 :
            return s % ( z, IECprefixes[i] if iec else SIprefixes[i]  )
    
    if type(a) in ( types.IntType , types.LongType ):
        return str(a)
    
    return s % ( float(a), '' )

def show_chart( n, maxn = None, ratio = None):

    maxn = maxn or max(n)

    ratio = ratio or maxn/40
    ratio = ratio or 1

    maxh = maxn/ratio

    hs = [ min(x/ratio, maxh) for x in n ]
    hs = [ [x%4]+[4]*(x/4) for x in hs ]
    hs = [ [0]*(maxh/4-len(x)) + x for x in hs ]

    rs = zip(*hs)
    rs = [ list(r)+[0] for r in rs ]
    rs = [ zip(r[::2],r[1::2]) for r in rs ]

    chrs = [ [ chartchar[a][b] for a, b in r ] for r in rs ]
    chrs = [ ''.join(cs) for cs in chrs ]

    for r in chrs :
        print r

    return


def smart_show_chart( n, height=10, points=None, iec=False, unit='', rjust=0, color=True ):

    maxn = max(n)

    segmax = maxn
    fix = 1
    
    if not iec :
        while( segmax >= 100 ):
            segmax = segmax/10
            fix = fix*10
        segmax = int(segmax)
        segmax = ((segmax/10)+1)*10 if segmax >= 20 else ((segmax/5)+1)*5 
        step = 5 if segmax <= 20 else 10 if segmax <= 50 else 20
        xpoints = [ (x*fix, x*4*height/segmax) for x in range(0,segmax,step) ]
    else :
        while( segmax >= 16 ):
            segmax = segmax/4
            fix = fix*4
        segmax = int(segmax)
        segmax = segmax+1
        step = 1 if segmax <= 4 else 2 if segmax <= 8 else 4
        xpoints = [ (x*fix, x*4*height/segmax) for x in range(0,segmax,step) ]
        
    maxn = segmax*fix
    maxp = humanreadable(maxn, iec=iec)+unit
    
    xpoints = [ ( humanreadable(p, iec=iec)+unit, x ) for p, x in xpoints ]
    xpointslen = max( len(p) for p, x in xpoints )
    xpointslen = max(xpointslen, len(maxp))+rjust
    xpoints = dict( (int(x)/4,(p,int(x)%4)) for p, x in xpoints )

    hs = [ min(x*4*height/maxn, 4*height) for x in n ]
    hs = [ [int(x)%4]+[4]*(int(x)/4) for x in hs ]
    hs = [ [0]*(height-len(x)) + x for x in hs ]

    rs = zip(*hs)
    rs = [ list(r)+[0] for r in rs ]
    rs = [ zip(r[::2],r[1::2]) for r in rs ]

    chrs = [ [ chartchar[a][b] for a, b in r ] for r in rs ]
    chrs = [ ''.join(cs) for cs in chrs ]
    
    maxp = maxp.rjust(xpointslen)
    
    if color :
        print maxp+chartlinex[0]+\
                    u'\033[38;5;237m'+chartline[0]*((len(n)+1)/2)+ u'\033[0m'
    else :
        print maxp+chartlinex[0]

    for i, r in enumerate( chrs ) :
        p, c = xpoints.get(height-i-1,('',None))
        p = p.rjust(xpointslen)
        if c is not None:
            #r = re.sub("([ ]+)",r'<\1>',"abc   def    ghi")
            r = re.sub(u"([\u2800]+)",u'\033[38;5;237m\\1\033[0m',r)
            r = r.replace(u'\u2800', chartline[c])
            c = chartlinex[c]
        else :
            c = ' '
        print p+c+r
    
    if points != None :
        points = points+[None,]
        points = [ (str(p) if p else None) for p in points ]
        points = zip(points[::2],points[1::2])
        points = [ ( a or b ) for a, b in points ]
        points = [ (i, x) for i, x in enumerate(points) if x ]
        pp, sp = zip(*points)
        if pp[0] != 0 :
            pplen = zip( [0]+list(pp), list(pp)+[0] )
            sp = ['',]+list(sp)
        else :
            pplen = zip( list(pp), list(pp[1:])+[0] )
        pplen = [ max( e-s, 0 ) for s, e in pplen ]
        lp = [ '|' if spi else ' ' for spi in sp ]
        lp = [ lpi.ljust(e) for lpi, e in zip(lp,pplen) ]
        sp = [ spi[:(e or None)].ljust(e) for spi, e in zip(sp,pplen) ]
        print ' '*(xpointslen+1)+''.join(lp)
        print ' '*(xpointslen+1)+''.join(sp)
    
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
    
    print
    print easyformat(d)
    
    import cmath
    print
    smart_show_chart([ x*123 for x in range(100) ])
    
    print
    smart_show_chart(
        [ x*123 for x in range(100) ],
        points = [ ( x if x%10==0 else None ) for x in range(100)],
        iec=True, unit='Byte',
    )
    