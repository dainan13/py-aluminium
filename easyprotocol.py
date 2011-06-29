
import re


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
    

autolength = AutoLength()


def parse_expr( e ):
    
    if e == None :
        return (0, None)
    
    e = e.strip()
    
    if e == 'auto' :
        return (1, None)
    
    if e.isnumeric() :
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
        
        args = [ ( (4,a[1:]) if a.startswith('$') else \
                      ( (2, int(a)) if a.isnumeric() else (5,a.split('.')) )
                 ) for a in args ]
        
        return (3, (function, args))
    
    
    if e.startswith('$') :
        return (4, e[1:])
        
    return (5, e.split('.'))


def find_var( e ):
    
    if e[0] == 4 :
        return [e[1]]
        
    if e[0] == 3 :
        return [ a[1] for a in e[2] if a[0] == 4 ]
            
    return []

class TypeStruct( object ):
    
    def __init__( self, name, members ):
        
        self.name = name
        self.cname = name
        self.members = members
        
        idt = sum( 1 for m in members if m['array'] == 'auto' or m['object'].identifiable == False )
        
        if idt > 1 :
            raise UnkownLengthError, 'more than one auto lengt in struct %s' % (self,name)
        
        self.identifiable = (idt == 0)
        self.stretch = False
        
        self.variables = sum( find_var(m['array']) for m in members , [] )
        self.variables += sum( find_var(m['arg']) for m in members , [] )
        self.variables += sum( m['object'].variables for m in members , [] )
        
        return
        
    def read( self, namespace, fp, lens, args ):
        
        r = {}
        
        l = 0
        
        for i, m in enumerate(members) :
            
            t = namespace[m['name']]
            
            if m['array'] == None :
                r0, l0 = t.read( namespace, fp, lens )
            elif m['array'] == 'auto' :
                lx = ( _m['name'].length( _m['len'], _m['array'] ) for _m in members[i:] )
                r0, l0 = t.read_multi( namespace, fp, lens-l-lx, m['array'] )
            else :
                r0, l0 = t.read_multi( namespace, fp, m['length'], m['array'] )
            
            l += l0
            r[m['var']] = r0
            
        return r, l

class TypeUnion( object ):
    
    def __init__( self, name, members, namespace ):
        
        self.name = name
        self.cname = name
        self.members = members
        
        idt = sum( 1 for m in members if m['array'] == 'auto' or namespace[m['name']].identifiable == False )
        
        self.identifiable = (idt == 0)
        
        self.variables = sum( find_var(m['array']) for m in members if m['array'] , [] )
        self.variables += sum( find_var(m['arg']) for m in members if m['arg'] , [] )
        self.variables += sum( for m in members if m['name'] , [] )
        
        return
        
    def read( self, namespace, fp, lens, args ):
        
        r = {}
        
        l = 0
        
        m = members[args]
        
        t = namespace[m['name']]
        
        if m['array'] == None :
            r0, l0 = t.read( namespace, fp, lens )
        elif m['array'] == 'auto' :
            r0, l0 = t.read_multi( namespace, fp, lens-l, m['array'] )
        else :
            r0, l0 = t.read_multi( namespace, fp, m['length'], m['array'] )
        
        l += l0
        r[m['var']] = r0
            
        return r, l

class BuildinTypeUINT( object ):
    
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
        
        i = 0
        
        for i, c in enumerate(chrs) :
            i = ord(c) * ( 256**i )
        
        return i, lens

class BuildinTypePACKINT( object ):
    
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
        
        i = 0
        
        if c == 252 :
            chrs = fp.read(2)
        elif c == 253 :
            chrs = fp.read(3)
        else :
            chrs = fp.read(8)
            
        for i, c in enumerate(chrs) :
            i = ord(c) * ( 256**i )
        
        return i, len(chrs)+1

class BuildinTypeCHAR( object )
    
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

class EasyBinaryProtocol( object ):
    
    buildintypes = [ BuildinTypeCHAR(),
                     BuildinTypePACKINT(),
                     BuildinTypeUINT(),
                   ]
    
    def __init__( self ):
        
        var = r'(?P<var>[a-zA-Z_]\w*)'
        name = r'(?P<name>[a-zA-Z_]\w*)'
        length = r'\((?P<length>\s*\S+?\s*)\)'
        array = r'\[(?P<array>\s*\S+\s*)\]'
        arg = r'\{(?P<arg>\s*\S+\s*)\}'

        self.pat = '%s\s+%s(%s)?(%s)?(%s)?' % (var, name, length, array, arg)

    def parse( self, fname ):
        
        structs = []
        
        defines = self.parsecode()[2]
        
        for define in defines : 
            self.parsedefine( structs, define )
        
        return
    
    def parsedefine( self, structs, define ):
        
        indent, declaration, children = define
        
        for child in children :
            if child[2] :
                self.parsedefine( structs, define )
                
        members = [ childdec for n, childdec, m in children ]
        
        structs.append()
        
        return
    
    def parsecode( self, fname ):
        
        rootnode = ( None, None, [] )
        stack = [rootnode,]
        
        with open(fname,'r') as fp :
            
            for i, li in enumerate(fp.readlines()):
                
                if '\t' in li :
                    raise InvalidCharactorFound, 'ABCDEF'
            
                indent = len(li) - len(li.lstrip())
            
                li = li.strip()
                
                if not li :
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
        
ebp = EasyBinaryProtocol()

if __name__ == '__main__' :
    
    import pprint
    
    pprint.pprint( ebp.parse( 'replication.protocol' ) )
    