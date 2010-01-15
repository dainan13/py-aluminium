
import types



class MapableTuple( tuple ):
    
    def setkeys( self, names ):
        
        self._keys = dict( [ (k, i) for i, k in enumerate( names )
                                    if k != None ] )
        
    def __getitem__( self, ind ):
        
        if type(ind) in types.StringTypes :
            ind = self._keys[ind]
        
        return super( MapableTuple, self ).__getitem__( ind )
        
    def keys():
        
        return self._keys.keys()
        
    def __contains__( self, key ):
        
        return key in self._keys
    
    def __iter__( self ):
        
        return self._key.__iter__()
        
    def __len__( self ):
        
        return len( self._key )




class Table( object ):
    
    def __init__( self, columns, table ):
        
        self._c = columns
        self.columns = dict([ ( c, i ) for i, c in enumerate(columns) ])
        
        self.index = {}
        
        self.values = table
        
        return
    
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
    
    def __init__( self, sep='##!#' ):
        
        self.sep = sep
        
    def parse( self, doc ):
        
        stages = self.splitstage(doc)
        
        hs, bs = zip(*stages)
        
        hs = [ self.stageargs(h) for h in hs ]
        
        ns = [ h.get('',None) for h in hs ]
        
        ts = [ getattr( self, 'parse_'+h['__type__'] ) for h in hs ]
        
        ps = [ h['__args__'] for h in hs ]
        
        bs = [ t(b,*p[0],**p[1]) for t, b, p in zip(ts,bs,ps) ]
        
        m = MapableTuple( bs )
        m.setkeys(ns)
        
        return m
    
    def splitstage( self, doc ):
        
        dls = doc.splitlines()
        e = [ l.strip()=='' for l in dls ]
        e = zip([True]+e,e+[True])
        
        gh = [ i for i, em in enumerate(e) if em[0]==True and em[1]==False ]
        gt = [ i for i, em in enumerate(e) if em[0]==False and em[1]==True ]
        
        g = [ dls[h:t] for h, t in zip(gh,gt) ]
        
        stages = [ ( gi[0].strip(), gi[1:], gi[0].find(self.sep) )
                     for gi in g if gi[0].strip().startswith(self.sep) ]
        
        stages = [ ( h, [ li[t:] for li in b ] )
                   for h, b, t in stages ]
        
        return stages
    
    @staticmethod
    def getargs( *args, **kwargs ):
        return ( args, kwargs )
    
    def stageargs( self, stagehead ):
        '''
        eg :
            Infos or Name                  .object as Name
        '''
        
        head = stagehead[len(self.sep):]
        
        dot = head.rfind('.')
        
        if dot < 0 :
            raise SyntexError, 'doc must have a type'
        
        args = head[dot:]
        
        sp = args.rsplit(None, 2)
        
        if len(sp) == 3 and sp[-2] == 'as' and sp[-1].find(')') == -1 :
            name = sp[-1]
            format = sp[0][1:]
            info = head[:dot].strip()
        else :
            name = head[:dot].strip()
            format = args[1:]
            info = name
        
        z = format.find('(')
        
        if z < 0 :
            args = [(),{}]
        else :
            format, args = format[:z], format[z:]
            args = self.getargs( eval('self.getargs%s' % (args,) ) )
        
        return {'':name,'__type__':format.lower(),'__args__':args}
    
    def parse_value( self, lines ):
        
        return '\r\n'.join(lines)
    
    def parse_object( self, lines ):
        
        r = [ li for li in lines if not li.lstrip().startswith('#') ]
        r = [ li.split(':',1) for li in r ]
        r = [ [ k.strip(), v.strip() ] for k, v in r ]
        
        return dict(r)
        
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
    
def parse( doc ):
    
    return DEFAULT_E.parse( doc )
    
    
    
    
    
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
