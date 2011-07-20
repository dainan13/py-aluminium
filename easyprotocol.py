
import re
import types

class EasyBinaryProtocolError( Exception ):
    pass
    
class InvalidCharactorFound( EasyBinaryProtocolError ):
    pass

class ParseSyntaxError( EasyBinaryProtocolError ):
    pass
    
class IndentSyntaxError( EasyBinaryProtocolError ):
    pass
    
class UnkownLengthError( EasyBinaryProtocolError ):
    pass
    
class AutoArrayError( EasyBinaryProtocolError ):
    pass

class UndefinedValueInUnion( EasyBinaryProtocolError ):
    pass


def parse_expr( e ):
    
    if e == None :
        return (0, None)
    
    e = e.strip()
    
    if e == 'auto' :
        return (1, None)
    
    #if e.isnumeric() :
    if e.isdigit() :
        return (2, int(e))
    
    if '(' and ')' in e :
        
        function = r'(?P<function>[a-zA-Z_]\w*)'
        #argument = r'(?P<arg>[a-zA-Z_]\w*)'
        arguments = r'(?P<args>.*)'
        
        m = re.match(r'%s\(%s\)' % (function, arguments), e)
        
        if m == None :
            raise ParseSyntaxError, ( 'Line: %d %s' % (i,li) )
        
        m = m.groupdict()
        
        f = m['function']
        args = [ a.strip() for a in m['args'].split(',') ]
        
        args = [ parse_expr(a) for a in args ]
        
        return (3, (f, args))
    
    
    if e.startswith('$') :
        return (4, e[1:])
    
    if not e.startswith('.'):
        return (5, e.split('.'))
    
    return (6, e.split('.')[1:])


def complength( e, vs, namespace ):
    
    t = e[0]
    
    if t == 0 :
        return 1
    
    if t == 1 :
        return None
    
    if t == 2 :
        return e[1]
    
    if t == 3 :
        args = [ complength(a, vs, namespace) for a in e[1][1] ]
        print '@',e
        return namespace[e[1][0]](*args)
        
    if t == 4 :
        return namespace[e[1]]
        
    if t == 5 :
        return reduce( (lambda x,y : x[y]), e[1], vs )
    
    if t == 6 :
        return reduce( (lambda x,y : x[y]), e[1], vs )

def find_var( e ):
    
    if e == None :
        return []
    
    if e[0] == 4 :
        return [e[1]]
        
    if e[0] == 3 :
        #print '>>>',e
        return [ a[1] for a in e[1][1] if a[0] == 4 ]
            
    return []


class ProtocolType( object ):
    
    def read_multi( self, namespace, fp, lens, mlens, args ):
        
        r = [ self.read( namespace, fp, lens, args ) for i in range(mlens) ]
        
        r, le = zip( *r )
        
        return r, sum(le)

class TypeStruct( ProtocolType ):
    
    def __init__( self, name, members ):
        
        self.name = name
        self.cname = name
        self.members = members
        
        idt = sum( 1 for m in members if m['array'] == 'auto' or m['object'].identifiable == False )
        
        if idt > 1 :
            print
            print self.name
            print members
            raise UnkownLengthError, 'more than one auto lengt in struct %s' % (self,name)
        
        self.identifiable = (idt == 0)
        self.stretch = False
        
        self.variables = sum( (find_var(m['array']) for m in members) , [] )
        self.variables += sum( (find_var(m['arg']) for m in members) , [] )
        self.variables += sum( (m['object'].variables for m in members) , [] )
        
        return
        
    def read( self, namespace, fp, lens, args ):
        
        r = {}
        
        l = 0
        
        for i, m in enumerate(self.members) :
            
            if m['array'][0] == 0 : #None
                
                if m['length'][0] == 1 : #auto
                    lx = sum( _m['object'].length( complength(_m['length'], r, namespace), complength(_m['array'], r, namespace) ) for _m in self.members[i+1:] )
                    #lx = sum( )
                    if type(lens) not in ( types.IntType, types.LongType ) :
                        lens = complength( lens, r, namespace )
                    le = lens - l - lx
                else :
                    le = complength( m['length'], r, namespace )
                
                a = complength( m['arg'], r, namespace )
                
                r0, l0 = m['object'].read( namespace, fp, le, a )
                
            elif m['array'][0] == 1 : #auto
                
                le = complength( m['length'], r, namespace )
                
                lx = sum( _m['object'].length( complength(_m['length'], r, namespace), complength(_m['array'], r, namespace) ) for _m in self.members[i+1:] )
                if type(lens) not in ( types.IntType, types.LongType ) :
                    lens = complength( lens, r, namespace )
                
                xle = lens - l - lx
                
                if xle % le != 0 :
                    raise AutoArrayError, 'auto array error'
                
                array = xle/le
                
                a = complength( m['arg'], r, namespace )
                
                r0, l0 = m['object'].read_multi( namespace, fp, le, array, a )
                
            else :
                
                array = complength( m['array'], r, namespace )
                le = complength( m['length'], r, namespace )
                
                a = complength( m['arg'], r, namespace )
                
                r0, l0 = m['object'].read_multi( namespace, fp, le, array, a )
            
            l += l0
            r[m['var']] = r0
            
        return r, l

class TypeUnion( ProtocolType ):
    
    def __init__( self, name, members ):
        
        self.name = name
        self.cname = name
        self.members = {}
        self.defaultmember = None
        
        i = 0
        for m in members :
            if 'seg' in m and m['seg']:
                
                if m['seg'] == '*:' :
                    self.defaultmember = m
                    continue
                    
                keys = [ int(i) for i in m['seg'].strip(':').split(',') if i ]
                for k in keys :
                    self.members[k] = m
                i = max(keys)
            else :
                self.members[i] = m
            i += 1
        
        #print 'u', self.members.keys()
        
        idt = sum( 1 for m in members if m['array'] == 'auto' or m['object'].identifiable == False )
        
        self.identifiable = (idt == 0)
        
        self.variables = sum( (find_var(m['array']) for m in members if m['array']) , [] )
        self.variables += sum( (find_var(m['arg']) for m in members if m['arg']) , [] )
        self.variables += sum( (m['object'].variables for m in members) , [] )
        
        return
        
    def read( self, namespace, fp, lens, args ):
        
        r = {}
        
        l = 0
        
        m = self.members.get(args, self.defaultmember )
        
        if not m :
            raise UndefinedValueInUnion, args
        
        if m['array'][0] == 0 : #None
            
            if m['length'][0] == 1 : #auto

                if type(lens) not in ( types.IntType, types.LongType ) :
                    lens = complength( lens, r, namespace )
                le = lens - l
                
            else :
                le = complength( m['length'], r, namespace )
            
            a = complength( m['arg'], r, namespace )
            
            r0, l0 = m['object'].read( namespace, fp, le, a )
            
        elif m['array'][0] == 1 : #auto
            
            le = complength( m['length'], r, namespace )

            if type(lens) not in ( types.IntType, types.LongType ) :
                lens = complength( lens, r, namespace )
            
            xle = lens - l
            
            if xle % le != 0 :
                raise AutoArrayError, 'auto array error'
            
            array = xle/le
            
            a = complength( m['arg'], r, namespace )
            
            r0, l0 = m['object'].read_multi( namespace, fp, le, array, a )
            
        else :
            
            array = complength( m['array'], r, namespace )
            le = complength( m['length'], r, namespace )
            
            a = complength( m['arg'], r, namespace )
            
            r0, l0 = m['object'].read_multi( namespace, fp, le, array, a )
        
        l += l0
        r[m['var']] = r0
            
        return r, l

class BuildinTypeUINT( ProtocolType ):
    
    def __init__( self ):
        
        self.name = 'uint'
        self.cname = 'long'
        
        self.identifiable = True
        self.stretch = False
        
        self.variables = []
        
    def length( self, lens, array ):
        return lens*array
        
    def read( self, namespace, fp, lens, args ):
        
        chrs = fp.read(lens)
        
        r = 0
        
        for i, c in enumerate(chrs) :
            r += ord(c) * ( 256**i )
        
        return r, lens

class BuildinTypePACKINT( ProtocolType ):
    
    def __init__( self ):
        
        self.name = 'packint'
        self.cname = 'long'
        
        self.identifiable = True
        self.stretch = True
        
        self.variables = []
        
    def length( self, lens, array ):
        return None
        
    def read( self, namespace, fp, lens, args ):
        
        c = ord(fp.read(1))
        
        if c < 251 :
            return c, 1
        
        if c == 251 :
            return None, 1
        
        r = 0
        
        if c == 252 :
            chrs = fp.read(2)
        elif c == 253 :
            chrs = fp.read(3)
        else :
            chrs = fp.read(8)
            
        for i, c in enumerate(chrs) :
            r += ord(c) * ( 256**i )
        
        return r, len(chrs)+1

class BuildinTypeCHAR( ProtocolType ):
    
    def __init__( self ):
        
        self.name = 'char'
        self.cname = 'char'
        
        self.identifiable = True
        self.stretch = False
        
        self.variables = []
        
    def length( self, lens, array ):
        return array
    
    def read( self, namespace, fp, lens, args ):
        
        return fp.read(1), 1
        
    def read_multi( self, namespace, fp, lens, mlens, args ):
        
        s = fp.read(mlens)
        
        return s, mlens

class BuildinTypeBYTE( ProtocolType ):
    
    def __init__( self ):
        
        self.name = 'byte'
        self.cname = 'char'
        
        self.identifiable = True
        self.stretch = False
        
        self.variables = []
        
    def length( self, lens, array ):
        return array
    
    def read( self, namespace, fp, lens, args ):
        
        return fp.read(1), 1
        
    def read_multi( self, namespace, fp, lens, mlens, args ):
        
        s = fp.read(mlens)
        
        return s, mlens

class BuildinTypeBIT( ProtocolType ):
    
    def __init__( self ):
        
        self.name = 'bit'
        self.cname = 'char'
        
        self.identifiable = True
        self.stretch = False
        
        self.variables = []
    
    @staticmethod
    def roundlen( l ):
        return (l+7) / 8
    
    def length( self, lens, array ):
        return self.roundlen(array)
    
    def read( self, namespace, fp, lens, args ):
        
        r = fp.read(1)
        
        return [ ( (r>>i) & 1 ) for i in range(8) ], 1
        
    def read_multi( self, namespace, fp, lens, mlens, args ):
        
        le = self.roundlen(mlens)
        
        s = fp.read( le )
        
        s = [ ( (ord(r)>>i) & 1 ) for r in s for i in range(8) ]
        
        return s[:mlens], le

def roundbin( a, b ):
    return a + b - ( a - 1 ) % b - 1

class EasyBinaryProtocol( object ):
    
    buildintypes = [ BuildinTypeCHAR(),
                     BuildinTypePACKINT(),
                     BuildinTypeUINT(),
                     BuildinTypeBYTE(),
                     BuildinTypeBIT(),
                   ]
    
    def __init__( self ):
        
        seg = r'(?P<seg>[0-9,*]*:)'
        var = r'(?P<var>[a-zA-Z_]\w*)'
        name = r'(?P<name>[a-zA-Z_]\w*)'
        length = r'\((?P<length>\s*\S+?\s*)\)'
        array = r'\[(?P<array>\s*\S+\s*)\]'
        arg = r'\{(?P<arg>\s*\S+\s*)\}'

        self.pat = '%s?%s\s+%s(%s)?(%s)?(%s)?' % (seg,var, name, length, array, arg)
        
        self.namespaces = dict( (bt.name, bt) for bt in self.buildintypes )
        self.p_globals = {}
    
    def parsefile( self, fname ):
        
        with open(fname,'r') as fp :
            defines = self._parsecode( fp.readlines() )[2]
        
        self._parse( defines )
        
        return
    
    def parse( self, fname ):
        
        defines = self._parsecode( fname )[2]
        
        self._parse( defines )
        
        return
    
    def _parse( self, defines ):
    
        for define in defines : 
            self._parsedefine( define )
            declaration = define[1].copy()
            v = declaration.pop('var')
            declaration['length'] = parse_expr( declaration['length'] )
            declaration['array'] = parse_expr( declaration['array'] )
            declaration['arg'] = parse_expr( declaration['arg'] )
            self.p_globals[v] = declaration
            
        return
    
    def _parsedefine( self, define ):
        
        indent, declaration, children = define
        
        if not children :
            return
        
        for child in children :
            if child[2] :
                self._parsedefine( child )
        
        members = [ childdec for n, childdec, m in children ]
        
        for m in members :
            m['array'] = parse_expr( m['array'] )
            m['length'] = parse_expr( m['length'] )
            m['arg'] = parse_expr( m['arg'] )
            m['object'] = self.namespaces[m['name']]
    
        if declaration['arg'] == None :
            self.namespaces[declaration['name']] = TypeStruct( declaration['name'], members )
        else :
            self.namespaces[declaration['name']] = TypeUnion( declaration['name'], members )
        
        return
    
    def _parsecode( self, lines ):
        
        rootnode = ( None, None, [] )
        stack = [rootnode,]
        
        for i, li in enumerate(lines):
            
            if '\t' in li :
                raise InvalidCharactorFound, 'tab founded'
        
            indent = len(li) - len(li.lstrip())
        
            li = li.strip()
            
            if ( not li ) or li.startswith('#'):
                continue
            
            m = re.match(self.pat,li)
            
            if m == None :
                raise ParseSyntaxError, ( 'Line: %d %s' % (i,li) )
            
            node = ( indent, m.groupdict(), [] )
            
            if indent > stack[-1][0] :
                
                stack[-1][2].append( node )
                stack.append( node )
                
                continue
            
            while( stack[-1][0] > indent ):
                stack.pop()
            
            if indent != stack[-1][0] :
                raise IndentSyntaxError, ( 'Line: %d %s %d %d' % (i,li) )
            
            stack.pop()
            
            stack[-1][2].append(node)
            stack.append(node)
        
        return rootnode
    
    def read( self, name, io, **spaces ):
        
        v = self.p_globals[name]
        stt = self.namespaces[v['name']]
        
        return stt.read( spaces, io, v['length'], v['array'] )[0]
        
        
ebp = EasyBinaryProtocol()

if __name__ == '__main__' :
    
    import pprint
    import cStringIO
    
    ebp.parsefile( 'test.protocol' )
    
    pprint.pprint( ebp.read('test1', cStringIO.StringIO('abcdefghij') ) )
    pprint.pprint( ebp.read('test2', cStringIO.StringIO(chr(3)+'abcdefghij') ) )
    pprint.pprint( ebp.read('test3', cStringIO.StringIO(chr(3)+'abcdefghij') ) )
    pprint.pprint( ebp.read('test4', cStringIO.StringIO(chr(10)+'abcdefghij') ) )
    pprint.pprint( ebp.read('test5', cStringIO.StringIO('abcdefghij') ) )
    pprint.pprint( ebp.read('test6', cStringIO.StringIO(chr(10)+chr(1)+'abcdefghij') ) )
    pprint.pprint( ebp.read('test7', cStringIO.StringIO(chr(1)+chr(2)+chr(3)) ) )
