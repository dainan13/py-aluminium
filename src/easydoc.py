#!/usr/bin/env python

"""
@author: dn13(dn13@gmail.com)
@author: Fibrizof(dfang84@gmail.com)
"""

import types

def _splitword( text, quotes ):
    
    if text[0] in quotes :
        s = text.find(text[0],1)
        return text[0], text[1:s], text[s+1:]
        
    else :
        for i in range(len(text)):
            if text[i].isalpha() == False :
                return '', text[:i], text[i:]
        
        return '', text, ''

def buildformattingstring( text, sign=('/*%','*/'), quotes=['"','\'','`'] ):
    '''
    /*%(Arg)s*/'ABC' => "'%(Arg)s'", {'Arg':'ABC'}
    '''
    
    text = text.split(sign[0])
    
    head, body = text[0], text[1:]
    
    body = [ b.split(sign[1],1) for b in body ]
    
    for b in body:
        if len(b) != 2 :
            raise ValueError, ( 'can not find the end of sign', b[0] )
    
    signcnt, body = zip(*body)
    
    ns = [ s[1:].split(')',1)[0] if s[0] == '(' else None for s in signcnt ]
    
    body = [ _splitword(b, quotes) for b in body ]
    
    qs, ds, bs = zip(*body)
    
    body = [ [ '%s%%%s%s' % (q,s,q), b.replace('%','%%') ] 
             for s, q, b in zip( signcnt, qs, bs )]
    
    body = sum( body, [] )
    
    text= [head.replace('%','%%'),]+body
    
    text = ''.join(text)
    
    ns_n = [ n == None for n in ns ]
    
    if all( ns_n ):
        return text, ds
    elif any( ns_n ):
        raise ValueError, 'Mapping key and non-Mapping key all in text'
    
    ds = dict(zip(ns,ds))
    
    return text, ds





class MapableTuple( tuple ):
    
    def setkeys( self, names ):
        
        self._keys = dict( [ (k, i) for i, k in enumerate( names )
                                    if k != None ] )
        
    def __getitem__( self, ind ):
        
        if type(ind) in types.StringTypes :
            ind = self._keys[ind]
        
        return super( MapableTuple, self ).__getitem__( ind )
        
    def get( self, ind, default ):
        
        if type(ind) in types.StringTypes :
            if ind in self._keys :
                ind = self._keys[ind]
            else :
                return default
        
        return super( MapableTuple, self ).__getitem__( ind )
        
    def keys( self ):
        
        return self._keys.keys()
        
    def __contains__( self, key ):
        
        return key in self._keys
    
    #def __iter__( self ):
    #    
    #    return self._keys.__iter__()
        
    def __len__( self ):
        
        return len( self._keys )
        
    def items( self ):
        
        r = self._keys.items()
        r.sort( key = lambda x : x[1] )
        
        return [ (k, self[i]) for k, i in r]
        
    def todict( self ):
        
        return dict( self.items() )



class Table( object ):
    
    def __init__( self, columns, table ):
        
        self._c = columns
        self.columns = dict([ ( c, i ) for i, c in enumerate(columns) ])
        
        self.index = {}
        
        self.values = table
        
        return
    
    def todict( self ):
        
        return [ dict( zip(self._c, r) ) for r in self.values ]
    
    def __getitem__( self, rows ):
        '''
        t[1]
        t['Name':'Cover']
        t[:,'Machine']
        t[5:7,'Machine']
        t['Name':'Cover',('Machine',)]
        t[5:7,6:9]
        '''
        
        cols = slice(None,None)
        
        if type(rows) in ( types.TupleType, types.ListType ) :
            if len(rows) != 2 :
                raise TypeError, 'slice must a tuple/list length 2.'
            
            rows, cols = rows
        
        if type(rows) == types.SliceType :
            if type( rows.start ) in types.StringTypes :
                c = self.columns[rows.start]
                
                rs = [ i for i, r in enumerate(self.values)
                       if r[c] == rows.stop ]
                if len(rs) > 1 :
                    raise IndexError, \
                          ( 'Multi Rows "%s"="%s" ' % (i.start,i.stop) ) \
                          + 'Line:' + ','.join(rs) 
                elif len(rs) == 0 :
                    raise IndexError, '"%s" Not Found' % (i.start,i.stop)
                
                rows = rs[0]
        
        if type(cols) in ( types.TupleType, types.ListType ) :
            cols = [ c if type(c) == types.IntType else self.columns[c]
                     for c in cols ]
        elif type(cols) == types.SliceType :
            if type( cols.start ) in types.StringTypes :
                cols.start = self.columns[cols.start]
            elif type( cols.stop ) in types.StringTypes :
                cols.stop = self.columns[cols.stop]
        elif type(cols) in types.StringTypes :
            cols = self.columns[cols]
        
        if type(cols) in ( types.IntType, types.SliceType ) :
            y = lambda r : r[cols]
        else :
            y = lambda r : [ r[c] for c in cols ]
        
        
        if type(rows) == types.IntType:
            x = y(self.values[rows])
        else :
            x = [ y(r) for r in self.values[rows] ]
        
        return x
    
    def __repr__( self ):
        
        return '(' + ', '.join( [ '('+', '.join([ repr(c) for c in r ])+')'
                                  for r in self.values
                              ] ) + ')'
    
    
    
class EasyDocError( Exception ):
    """
    Error of EasyDocstriong Modules
    """
    pass
    
    
    
class EasyDoc( object ):
    
    def __init__( self, sep=1, title='##!#' ):
        
        self.sep = sep
        self.title = title
        
    def parse( self, doc, parser = None, *args, **kwargs ):
        
        if parser != None :
            body = self.onestage( doc )
            parser = getattr( self, 'parse_' + parser )
            return parser( body, *args, **kwargs )
        
        stages = self.splitstage(doc)
        
        heads, bodys = zip(*stages)
        
        # get the real body
        ends = [ getattr( self, 'ends_'+h['__ends__'] ) for h in heads ]
        bodys = [ e(b) for e, b in zip(ends,bodys) ]
        
        # parse indent
        bodys = [ [ l[h['__indent__']:] for l in b ] 
                  for h, b in zip( heads, bodys ) ]
        
        # get the names
        names = [ h.get('',None) for h in heads ]
        
        # parse the body
        parses = [ getattr( self, 'parse_'+h['__type__'] ) for h in heads ]
        argses = [ h['__args__'] for h in heads ]
        bodys  = [ p( b, *a[0], **a[1] )
                   for p, a, b in zip(parses, argses, bodys) ]
        
        m = MapableTuple( bodys )
        m.setkeys(names)
        
        return m
    
    def onestage( self, doc ):
        
        dls = doc.splitlines()
        
        if dls == [] :
            return dls
        
        while( dls[0].strip() == '' ):
            del dls[0]
        
        while( dls[-1].strip() == '' ):
            del dls[-1]
            
        return dls
    
    def splitstage( self, doc ):
        '''
        split stage
        '''
        
        dls = doc.splitlines()
        len_dls = len(dls)
        striped_dls = [ l.strip() for l in dls ]
        e = [ l=='' for l in striped_dls ]
        e = [ e[ (i-self.sep) if i>self.sep else 0 :i] for i in range(len_dls) ]
        e = [ all(el) for el in e ]
        t = [ l.startswith(self.title) for l in striped_dls ]
        
        s = [ i for e, t, i in zip(e,t,range(len_dls)) if e==True and t==True ]
        s = [ dls[h:n] for h, n in zip( s, s[1:]+[None,] )]
        
        
        s = [ (self.parsetitle(st[0]),st[1:]) for st in s ]
        
        return s
    
    @staticmethod
    def getargs( *args, **kwargs ):
        return ( args, kwargs )
    
    @staticmethod
    def read_stage_args( t ):
        
        x = False
        
        for i in range(len(t)):
            if not t[i].isalpha() :
                break
        else :
            return t, None, None, None
        
        ty = t[0:i]
        t = t[i:].lstrip()
        
        args = None
        
        if t[0] == '(' :
            c = 0
            for i in range(len(t)):
                if t[i] == '(' :
                    c += 1
                if t[i] == ')' :
                    c -= 1
                    if c == 0 :
                        break
            else :
                return ty, t, None, None
            
            args = t[0:i+1]
            t = t[i+1:]
            
        t = t.lstrip()
        
        t = t.split()
        
        t = dict( zip( t[::2],t[1::2] ) )
        
        return ty, args, t.get('ends',None), t.get('as',None)
    
    def parsetitle( self, t ):
        
        leftspace = t.find( self.title )
        t = t[ leftspace + len(self.title) : ]
        
        dot = t.rfind('.')
        
        if dot < 0 :
            raise SyntexError, 'doc must have a type'
        
        ty, args, ends, name = self.read_stage_args( t[dot+1:] )
        
        args = ([],{}) if args == None else \
                            self.getargs( eval('self.getargs%s' % (args,) ) )
        name = name or t[:dot].strip()
        ends = ends or 'E1'
        ty = ty.lower()
        
        return { '': name,
                 '__type__': ty,
                 '__args__': args,
                 '__ends__': ends,
                 '__indent__': leftspace,
               }
        
    def _ends_E( self, lines, n ):
        
        e = [ l.strip()=='' for l in lines ]
        e = [ e[i:i+n] for i in range(len(lines)) ]
        e = [ i for i, el in enumerate(e) if all(el) ]
        
        if e == []:
            return lines
        else :
            return lines[:e[0]]
        
    def ends_E1( self, lines ):
        return self._ends_E( lines, 1 )
        
    def ends_E2( self, lines ):
        return self._ends_E( lines, 2 )
        
    def ends_E3( self, lines ):
        return self._ends_E( lines, 3 )
    
    def parse_value( self, lines ):
        
        return '\r\n'.join(lines)
    
    def parse_object( self, lines ):
        
        r = [ li for li in lines if not li.lstrip().startswith('#') ]
        r = [ li.split(':',1) for li in r ]
        r = [ [ k.strip(), v.strip() ] for k, v in r ]
        
        return dict(r)
        
    def parse_object_ex( self, lines ):
        
        if lines == [] :
            return {}
        
        spacelen = lambda x : len(x) - len(x.lstrip(' '))
        
        sl = spacelen(lines[0])
        p = [ i for i, li in enumerate( lines ) if spacelen(li) == sl ]
        seg = zip( p, p[1:]+[len(lines)] )
        
        r = {}
        
        for f, b in seg :
            
            k, v = lines[f].split(':',1)
            k = k.strip()
            v = v.strip()
            
            if b - f == 1 :
                r[k] = v
            else :
                r[k] = self.parse_object_ex( lines[f+1:b] )
                if v != '' :
                    r[k][''] = v
            
        return r
        
    def parse_table( self, lines ):
        
        if lines[0].startswith('!'):
            
            ns = [ c.strip() for c in lines[0].split('!') ][1:]
            
            cols = [ n for n, i in enumerate(lines[0]) if i == '!' ]
            
            lines = lines[1:]
            
        else :
            
            ns = []
            
            slines = lines[:]
            slines.sort(key=lambda x:len(x),reverse=True)
            
            maxlen = len(slines[0])
            cols = [False,]*maxlen
            
            for i in range(maxlen):
                
                for li in lines :
                    try :
                        if li[i]!=' ' :
                            break
                    except IndexError, e :
                        pass
                else :
                    cols[i] = True
            
            cols = zip( cols, [True]+cols )
            cols = [ i for i, t in enumerate(cols)
                     if t[0]==False and t[1]==True ]
         
        cols = [ slice(a, b) for a, b in zip(cols,cols[1:]+[None]) ]
        
        rows = [ i for i, li in enumerate(lines) if not li.startswith('!') ]
        lines = [ li if not li.startswith('!') else ' '+li[1:] for li in lines ]
        rows = [ slice(a, b) for a, b in zip(rows,rows[1:]+[None]) ]
        
        tbs = [ [ '\r\n'.join([ l[c].rstrip() for l in lines[r] ])
                  for c in cols ]
                for r in rows ]
        
        
        return Table( ns, tbs )
    
    def parse_json( self ):
        
        pass
    
    
    
    
    
    
DEFAULT_E = EasyDoc()
    
def parse( doc, *args, **kwargs ):
    
    return DEFAULT_E.parse( doc, *args, **kwargs )
    
    
    
    
    
if __name__=='__main__':
    
    from pprint import pprint
    
    d = '''
        some infos ( not parse )
        
        ##!# Metas_A                                                     .object
        name : foo
        author : d13
        version : 1.0
        
        ##!# Metas_B                                                      .value
        array(
            #.Subject     : string,
            #.Result      : ascii(1),
        )
        
        ##!# Table_A                                                      .table
        !Number   !Alpha    !GreekAlphabet   !phonetic
        1         a         alpha            [a]
        2         b         beta             [v]
        3         c         gamma
        
        ##!# Table_B                                                      .table
        1         a         alpha            [a]
        2         b         beta             [v]
        3         c         gamma
        
        ##!# Table_C                                                      .table
        !Student       !Subject      !Result
        Joth           Math          A
        !              History       B
        !              Geography     A
        Marry          Society       B
        !              History       A
        
        ##!# FOO                                       .value ends E2 as Metas_C
        array(
            #.Subject1     : string,
            #.Subject2     : string,
            
            #.Result1      : ascii(1),
            #.Result2      : ascii(1),
        )
        
        
        ##!# BAR                                               .value as Metas_D
        A
        
        
        ##!# Metas_EX                                                 .object_ex
        argument: showstyle
            showtype: dropdownlist
                items: ['table','list']
                default: 'table'
            action: js.changeshowstyle
        showtype: text
        
        '''
        
    e = EasyDoc()
    
    r = e.parse(d)
    
    pprint( r )
    
    #({'author': 'd13',
    #  'name': 'foo',
    #  'version': '1.0'},
    # 'array(\r\n    #.Subject     : string,\r\n    #.Result      : ascii(1),\r\n)',
    # (('1', 'a', 'alpha', '[a]'), ('2', 'b', 'beta', '[v]'), ('3', 'c', 'gamma', '')),
    # (('1', 'a', 'alpha', '[a]'), ('2', 'b', 'beta', '[v]'), ('3', 'c', 'gamma', '')),
    # (('Joth\r\n\r\n', 'Math\r\nHistory\r\nGeography', 'A\r\nB\r\nA'), ('Marry\r\n', 'Society\r\nHistory', 'B\r\nA')))
    
    print r['Table_A'][:,'GreekAlphabet']
    #['alpha', 'beta', 'gamma']
    
    print r['Table_A'][1]
    #['2', 'b', 'beta', '[v]']
    
    print r['Table_A'][1,1]
    #b
    
    print r['Metas_C']
    
    print r['Metas_EX']
