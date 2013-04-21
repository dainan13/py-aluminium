from simpleparse.parser import Parser

class EasyScript(object):
    
    grammer = r'''
        statement  := assignment / expression / forstate / ifstate / whilestate
        assignment := var, [ ]*, '=', [ ]*, expr
        expression := expr
        
        forstate   := 'for', [ ]+, var, [ ]+, 'in', [ ]+, expr, ':'
        ifstate    := 'if', [ ]*, expr, [ ]*, ':'
        whilestate := 'while', [ ]*, expr, [ ]*, ':'
        
        expr       := expr2, ( [ ]*, relop, [ ]*, expr2 )*
        >expr2<    := funcexpr / number / ( '(', expr, ')' ) / var
        funcexpr   := var, '(', [ ]*, args?, [ ]*, ')'
        args       := expr, ( [ ]*, ',', [ ]*, expr )*
        
        relop      := [+-*/]
        
        var        := [a-zA-Z_]+, [a-zA-Z0-9_]*
        number     := [0-9]+, ( '.', [0-9]+ )?
    '''
    
    parser = Parser(grammer,'statement')
    
    def __init__( self ):
        
        self.namespace = {}
        self.stack = []
        self.code = []
        
        return
        
    def compile( self, script ):
        
        for ln in script.splitlines():
            
            ln = ln.strip()
            if ln == '' :
                continue
        
            gtree = vm.parser.parse(ln)
            self._compile( ln, gtree[1][0] )
            
        return 
        
    
    op_pri = {
        '+':1,
        '-':1,
        '*':0,
        '/':0,
    }
    
    def _compile( self, script, node ):
        
        name, st, ed, children = node
        
        if name == 'assignment' :
            
            assignmentvar = children.pop(0)
            assignmentvar = script[assignmentvar[1]:assignmentvar[2]]
            
            for child in children :
                self._compile( script, child )
            
            self.code.append( 'set %s' % (assignmentvar,) )
        
        elif name == 'expression' :
            
            for child in children :
                self._compile( script, child )
            
            self.code.append( 'pop 1' )
        
        elif name == 'funcexpr' :
            
            func = children.pop(0)
            func = script[func[1]:func[2]]
            
            for child in children :
                self._compile( script, child )
            
            self.code.append( 'pushv %s' % ( func, ) )
            self.code.append( 'call %s' % ( len(children[0][-1]), ) )
            
        elif name == 'number' :
            
            self.code.append( 'push %s' % script[st:ed] )
        
        elif name == 'expr' :
            
            ops = [ (i, script[op[1]:op[2]]) for i, op in enumerate( children[1::2] ) ]
            ops.sort( key = (lambda x : (self.op_pri[x[1]], x[0])) )
            
            for i, child in enumerate( children[::2] ) :
                
                self._compile( script, child )
                
                while( ops and ops[0][0] <= i-1 ) :
                    
                    op = ops.pop(0)
                    self.code.append( 'oper %s' % ( op[1], ) )
        
        elif name == 'var' :
            
            self.code.append( 'pushv %s' % ( script[st:ed], )  )
        
        elif name == 'args' :
            
            for child in children :
                self._compile( script, child )
            
        else :
            
            raise Exception, ('unkown node', name)
        
        return
    
    def run( self, ns=None ):
        
        if ns != None :
            self.namespace.update(ns)
        
        for code in self.code :
            
            cmd, arg = code.split()
            
            if cmd == 'pop' :
                for i in range(int(arg)):
                    self.stack.pop(-1)
            
            elif cmd == 'set' :
                self.namespace[arg] = self.stack.pop(-1)
                
            elif cmd == 'push' :
                self.stack.append( eval(arg) )
                
            elif cmd == 'pushv' :
                self.stack.append( self.namespace[arg] )
                
            elif cmd == 'call' :
                func = self.stack.pop(-1)
                fargs = [ self.stack.pop(-1) for i in range(int(arg)) ]
                fargs.reverse()
                self.stack.append( func(*fargs) )
            
            elif cmd == 'oper' :
                b = self.stack.pop(-1)
                a = self.stack.pop(-1)
                if arg == '+' :
                    self.stack.append( a+b )
                elif arg == '-' :
                    self.stack.append( a-b )
                elif arg == '*' :
                    self.stack.append( a*b )
                elif arg == '/' :
                    self.stack.append( a/b )
                
        return
    
    
def foo( a, b ):
    
    print a, b
    return a**b


if __name__ == '__main__' :
    
    vm = EasyScript()
    
    script = '''
a = foo( 1 +(4 / 2) , abc )
b = a
a = a+1
a = 1+a
print(a)
print(b)
'''
    
    import pprint
    print '== code tree =='
    for ln in script.splitlines():
        
        ln.strip()
        if ln == '' :
            continue
            
        pprint.pprint( vm.parser.parse(ln) )
    
    
    print
    print
    
    print '== binary code =='
    vm.compile( script )
    for code in vm.code :
        print code
    
    print
    print
    
    print '== run result ==' 
    vm.run( {'foo':foo, 'abc':2, 'print':pprint.pprint} )
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    