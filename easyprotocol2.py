

import ast
import tokenize
import StringIO

class EasyBinaryProtocolError( Exception ):
    pass
    
class InvalidCharactorFound( EasyBinaryProtocolError ):
    pass

class ParseSyntaxError( EasyBinaryProtocolError ):
    pass
    
    

class PyLang( ast.NodeTransformer ):
    
    def visit_Name( self, node ):
        
        self.constants = False
        
        if node.id.startswith('__') :
            
            self.refvars.append( node.id[2:] )
            
            r = ast.copy_location(
                    ast.Subscript(
                        value=ast.Name(id='refvars', ctx=ast.Load()),
                        slice=ast.Index(value=ast.Str(s=node.id[2:])),
                        ctx=node.ctx,
                    ), 
                    node
                )
        
        elif node.id.startswith('_f_'):
            
            self.f_vars.append( node.id[3:] )
            
            r = ast.copy_location(
                    ast.Subscript(
                        value=ast.Name(id='refvars', ctx=ast.Load()),
                        slice=ast.Index(value=ast.Str(s=node.id[3:])),
                        ctx=node.ctx,
                    ), 
                    node
                )
        
        elif node.id == 'auto' :
            
            self.isauto = True
            
            e = ast.parse('auto(rlength,members,m)','<string>',mode='eval')
            
            r = ast.copy_location(e.body, node)
        
        elif node.id == '_i' :
            
            self.fluid = True
            
            node.id = 'i'
            r = node
        
        elif node.id == '_':
            
            self.introspection = True
            
            r = ast.copy_location(
                    ast.Subscript(
                        value=ast.Name(id='vars', ctx=ast.Load()),
                        slice=ast.Index(value=ast.Name(id='cur', ctx=ast.Load())),
                        ctx=node.ctx,
                    ),
                    node
                )
        
        else :
            
            r = ast.copy_location(
                    ast.Subscript(
                        value=ast.Name(id='vars', ctx=ast.Load()),
                        slice=ast.Index(value=ast.Str(s=node.id)),
                        ctx=node.ctx,
                    ),
                    node
                )
        
        return r
        
    def visit_Attribute( self, node ):
        
        self.generic_visit( node )
        
        return  ast.copy_location(
                    ast.Subscript(
                        value=node.value,
                        slice=ast.Index(value=ast.Str(s=node.attr)),
                        ctx=node.ctx,
                    ), 
                    node
                )
    
    def visit_Call( self, node ):
        
        if type(node.func) != ast.Name :
            raise ParseSyntaxError, ('function call syntax error')
        
        node.func.id == '_f_'+node.func.id
        
        self.generic_visit( node )
        
        return
    
    def exprparse( self, source ):
        
        e = ast.parse(source,'<string>',mode='eval')
        
        self.refvars = []
        self.f_vars = []
        self.isauto = False
        self.introspection = False
        self.constants = True
        self.fluid = False
        self.function = False
        
        r = ast.fix_missing_locations( self.visit(e) )
        
        return {
            'ast' : r,
            'refvars' : self.refvars,
            'function' : self.function,
            'f_vars' : self.f_vars,
            'isauto' : self.isauto,
            'introspection' : self.introspection,
            'constants' : self.constants,
            'fluid' : self.fluid,
        }





class TypeUnion( ProtocolType ):
    
    def __init__( self, name, members ):
        
        self.name = name
        
        self.c_type = 'union ebp_' + name
        self.c_malloc = True
        
        self.identifiable = True
        self.stretch = any( m['isauto'] for m in members )
        
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
        
    def read( self, p_locals, fp, lens, args ):
        
        r = {}
        
        l = 0
        
        m = self.members.get(args, self.defaultmember )
        
        if not m :
            raise UndefinedValueInUnion, args
        
        if m['isauto'] == 'auto' :
            return
        
        if m['array'][0] == 0 : #None
            
            if m['length'][0] == 1 : #auto

                if type(lens) not in ( types.IntType, types.LongType ) :
                    lens = complength( lens, r, p_locals )
                le = lens - l
                
            else :
                le = complength( m['length'], r, p_locals )
            
            a = complength( m['arg'], r, p_locals )
            
            r0, l0 = m['object'].read( p_locals, fp, le, a )
            
        elif m['array'][0] == 1 : #auto
            
            le = complength( m['length'], r, p_locals )

            if type(lens) not in ( types.IntType, types.LongType ) :
                lens = complength( lens, r, p_locals )
            
            xle = lens - l
            
            if xle % le != 0 :
                raise AutoArrayError, 'auto array error'
            
            array = xle/le
            
            a = complength( m['arg'], r, p_locals )
            
            r0, l0 = m['object'].read_multi( namespace, fp, le, array, a )
            
        else :
            
            array = complength( m['array'], r, p_locals )
            le = complength( m['length'], r, p_locals )
            
            a = complength( m['arg'], r, p_locals )
            
            r0, l0 = m['object'].read_multi( p_locals, fp, le, array, a )
        
        l += l0
        r[m['var']] = r0
            
        return r, l



class BuildinTypeUINT( ProtocolType ):
    
    def __init__( self ):
        
        self.name = 'uint'
        
        self.c_type = 'unsigned long'
        self.c_malloc = False
        
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
        

class BuildinTypeCHAR( ProtocolType ):
    
    def __init__( self ):
        
        self.name = 'char'
        
        self.c_type = 'char'
        self.c_malloc = False
        
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
        
        self.c_type = 'char'
        self.c_malloc = False
        
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
        
        self.c_type = 'char'
        self.c_malloc = False
        
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


class EasyBinaryProtocol( object ):
    
    buildintypes = [ BuildinTypeCHAR(),
                     BuildinTypeUINT(),
                     BuildinTypeBYTE(),
                     BuildinTypeBIT(),
                   ]
    
    def __init__( self ):
        
        self.cc = PyLang()
        
        self.namespaces
        
        return
    
    def parse( self, source ):
        
        ebp_st = self.parsecode( source, 'string' )
        
        for define in ebp_st : 
            self._parsedefine( define )
            declaration = define[1].copy()
            v = declaration.pop('var')
            #declaration['length'] = parse_expr( declaration['length'] )
            #declaration['array'] = parse_expr( declaration['array'] )
            #declaration['arg'] = parse_expr( declaration['arg'] )
            self.p_globals[v] = declaration
        
        return
    
    def builddefine( self, defines ):
        
        indent, declaration, children = define
        
        if not children :
            return
        
        for child in children :
            if child[2] :
                self._parsedefine( child )
        
        members = [ childdec for n, childdec, m in children ]
        
        for m in members :
            #m['array'] = parse_expr( m['array'] )
            #m['length'] = parse_expr( m['length'] )
            #m['arg'] = parse_expr( m['arg'] )
            m['object'] = self.namespaces[m['name']]
    
        if declaration['arg'] == None :
            self.namespaces[declaration['name']] = TypeStruct( declaration['name'], members )
        else :
            self.namespaces[declaration['name']] = TypeUnion( declaration['name'], members )
        
        return
    
    def parsecode( self, source, filename ):
        
        rootnode = ( None, None, [] )
        stack = [rootnode,]
        
        lns = [ ln for ln in source.splitlines() ]
        
        for i, ln in enumerate(lns):
            
            if '\t' in ln :
                raise InvalidCharactorFound, 'tab founded'
            
            indent = len(ln) - len(ln.lstrip())
            
            li = ln.strip()
            
            if ( not li ) or li.startswith('#'):
                continue
            
            decl = self.parseline( li, i, filename )
            
            node = (indent, decl, [])
            
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
    
    defargsign = {')':'length',']':'array','}':'arg'}
    brks = {'(':')','[':']','{':'}'}
    
    def parseline( self, li, lineno, filename ):
        
        name, define = li.split(None, 1)
        
        stack51 = []
        
        g = list( tokenize.generate_tokens(StringIO.StringIO(define).readline) )
        
        ng = []
        
        defarg = {}
        
        gvar = False
        
        i = 0
        for toknum, tokval, _, _, _ in g:
            
            if toknum == 51 :
                if tokval in ('(','[','{') :
                    stack51.append( (tokval, i) )
                elif tokval in (')',']','}') :
                    s, si = stack51.pop()
                    if self.brks[s] != tokval or tokval in defarg :
                        raise ParseSyntaxError, (filename, lineno)
                    if len(stack51) == 0 :
                        if tokval in defarg :
                            raise ParseSyntaxError, (filename, lineno)
                        defarg[tokval] = (si,i)
                    
            if toknum == 52 : # $ sign
                gvar = True
                continue
            
            if toknum == 1 and tokval.startswith('_') and tokval!='_' and tokval!='_i':
                raise ParseSyntaxError, (filename, lineno)
            
            if gvar == True :
                gvar = False
                if toknum != 1 or tokval == '_' or tokval == '_i' :
                    raise ParseSyntaxError, (filename, lineno)
                ng.append( (toknum, '__'+tokval) )
                i += 1
                continue
                
            ng.append( (toknum, tokval) )
            i += 1
        
        v = min( [s for s, e in defarg.values()] or [len(ng)-1] )
        
        if v != 1 :
            raise ParseSyntaxError, (filename, lineno)
            
        defarg = [ ( k, tokenize.untokenize(ng[s+1:e]).strip() ) 
                   for k, (s, e) in defarg.items() ]
        defarg = [ ( self.defargsign[k], self.cc.exprparse(a) ) 
                   for k, a in defarg ]
        
        defarg = dict(defarg)
        
        #                 ( length )[ array ]{ arguments }
        # refvar                                             sum
        # fucntion          -auto     -auto                  any
        # isauto     auto     1         1          N         any
        # introspection _               N          N         any
        # constants
        # fluid               N         N                    any
        
        if defarg.get('length',{}).get('isauto',False) and defarg.get('array',{}).get('isauto',False) :
            raise ParseSyntaxError, 'auto only used in length or array, not both.'
        
        if defarg.get('arguments',{}).get('isauto',False) :
            raise ParseSyntaxError, 'auto only can be used in length or array, not in arguments.'
        
        if defarg.get('array',{}).get('introspection',False) or defarg.get('arguments',{}).get('introspection',False) :
            raise ParseSyntaxError, '_ only can be used in length .'
        
        if defarg.get('length',{}).get('fluid',False) or defarg.get('array',{}).get('fluid',False) :
            raise ParseSyntaxError, '_i only can be used in arguments .'
        
        refvar = sum( [ v['refvars'] for v in defarg.values() ] , [] )
        f_vars = sum( [ v['f_vars'] for v in defarg.values() ] , [] )
        isauto = 'length' if defarg.get('length',{}).get('isauto',False) else \
            ( 'array' if defarg.get('array',{}).get('isauto',False) else None )
        introspection = defarg.get('length',{}).get('introspection',False)
        fluid = defarg.get('arguments',{}).get('fluid',False)
        
        
        declaration = [ ( k, defarg.get(k,{}).get('ast',None) ) 
                        for k in self.defargsign.values() ]
        declaration = dict(declaration)
        
        declaration['var'] = ng[0][1]
        declaration['name'] = name
        declaration['refvars'] = set(refvar)
        declaration['f_vars'] = set(f_vars)
        declaration['isauto'] = isauto
        declaration['introspection'] = introspection
        declaration['fluid'] = fluid
        
        return declaration
        
if __name__ == '__main__' :
    
    ebp = EasyBinaryProtocol()
    
    from pprint import pprint
    
    pprint( ebp.parse( open('replication.protocol').read() ) )
    