


import re

name = r'(?P<name>[a-zA-Z_]\w*)'
length = r'\((?P<length>\s*\S+?\s*)\)'
array = r'\[(?P<array>\s*\S+\s*)\]'
arg = r'\{(?P<arg>\s*\S+\s*)\}'

pat = '%s(%s)?(%s)?(%s)?' % (name, length, array, arg)


class EasyBinaryProtocolError( Exception ):
    pass
    
class InvalidCharactorFound( EasyBinaryProtocolError ):
    pass

class ParseSyntaxError( EasyBinaryProtocolError ):
    pass
    
class IndentSyntaxError( EasyBinaryProtocolError ):
    pass
    


class ProtocolDataType( object ):
    
    def __init__( self, name, members ):
        
        self.name = name
        self.members = members
        
        return
        
    def build_c_types( self ):
        
        
        
        return


class EasyBinaryProtocol( object ):
    
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
    