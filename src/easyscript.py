from simpleparse.parser import Parser

class EasyScript(object):
    
    grammer = r'''
        file       := ( [ ]*, (statement, [ ]*)?, ( ';' / '\n' ) )*
        >block<    := ( [ ]*, (statement, [ ]*)?, ( ';' / '\n' ) )*
        
        statement  := ifstate / forstate / whilestate / assignment / expression
        assignment := var, [ ]*, '=', [ ]*, expr
        expression := expr
        
        forstate   := 'for', [ ]+, var, [ ]+, 'in', [ ]+, expr, [ ]*, '{', '}'
        whilestate := 'while', [ ]*, expr, [ ]*, '{', block, '}'
        ifstate    := 'if', [ ]*, expr, [ ]*, '{', block, '}', elifstate*, elsestate?
        elifstate  := [ \n]*, 'elif', [ ]*, expr, [ ]*, '{', block, '}'
        elsestate  := [ \n]*, 'else', [ \n]*, '{', block, '}'
        
        expr       := expr2, ( [ ]*, relop, [ ]*, expr2 )*
        >expr2<    := funcexpr / number / ( '(', expr, ')' ) / var
        funcexpr   := var, '(', [ ]*, args?, [ ]*, ')'
        args       := expr, ( [ ]*, ',', [ ]*, expr )*
        
        relop      := [-+*/] / '==' / '!='
        
        var        := [a-zA-Z_]+, [a-zA-Z0-9_]*
        number     := [0-9]+, ( '.', [0-9]+ )?
    '''
    
    parser = Parser(grammer,'file')
    
    def __init__( self ):
        
        self.namespace = {}
        self.stack = []
        self.code = []
        self.segpos = {}
        
        return
        
    def compile( self, script ):
        
        gtree = vm.parser.parse(script)
        
        print script[gtree[0]:gtree[-1]]
        
        for st in gtree[1] :
            self._compile( script, st )
        
        for i, code in enumerate(self.code) :
            if code.startswith('jump') or code.startswith('jmp') :
                cmd, arg = code.split()
                self.code[i] = '%s %s' % (cmd, self.segpos[arg]-i-1)
        
        self.code.append('halt 0')
        
        return 
        
    def setsegname( self, segname ):
        self.segpos[segname] = len(self.code)
        return
    
    op_pri = {
        '+':1,
        '-':1,
        '*':0,
        '/':0,
        '==':2,
        '!=':2,
        'and':3,
        'or':3,
    }
    
    def _compile( self, script, node, pst=None ):
        
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
        
        elif name == 'whilestate' :
            
            self.setsegname( '%sWHILESTART' % (st,) )
            condexpr = children.pop(0)
            self._compile( script, condexpr )
            self.code.append( 'jmpf %sWHILEEND' % (st,) )
            
            while( children and children[0][0] == 'statement' ):
                child = children.pop(0)
                self._compile( script, child )
            
            self.code.append( 'jump %sWHILESTART' % (st,) )
            self.setsegname( '%sWHILEEND' % (st,) )
            
        elif name == 'ifstate' :
            
            condexpr = children.pop(0)
            self._compile( script, condexpr )
            self.code.append( 'jmpf %sIFFAILD' % (st,) )
            
            
            while( children and children[0][0] == 'statement' ):
                child = children.pop(0)
                self._compile( script, child )
                
            endif = len(self.segpos)
            self.code.append( 'jump %sENDIF' % (st,) )
            self.setsegname( '%sIFFAILD' % (st,) )
            
            while( children and children[0][0] == 'elifstate' ):
                child = children.pop(0)
                self._compile( script, child, st )
                
            if children and children[0][0] == 'elsestate' :
                child = children.pop(0)
                self._compile( script, child )
            
            self.setsegname( '%sENDIF' % (st,) )
            
        elif name == 'elifstate' :
            
            condexpr = children.pop(0)
            self._compile( script, condexpr )
            self.code.append( 'jmpf %sIFFAILD' % (st,) )
            
            while( children and children[0][0] == 'statement' ):
                child = children.pop(0)
                self._compile( script, child )
                self.code.append( 'jump %sENDIF' % (pst,) )
                self.setsegname( '%sIFFAILD' % (st,) )
            
        elif name == 'elsestate' :
            
            while( children and children[0][0] == 'statement' ):
                child = children.pop(0)
                self._compile( script, child )
            
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
            
        elif name == 'statement' :
            
            for child in children :
                self._compile( script, child )
            
        else :
            
            raise Exception, ('unkown node', name)
        
        return
    
    def run( self, ns=None ):
        
        if ns != None :
            self.namespace.update(ns)
        
        cp = 0
        
        while( True ):
            
            cmd, arg = self.code[cp].split()
            
            #print cmd, arg, self.stack
            
            if cmd == 'halt' :
                break
            
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
                elif arg == '==' :
                    self.stack.append( a==b )
                elif arg == '!=' :
                    self.stack.append( a!=b )
                elif arg == 'and' :
                    self.stack.append( a and b )
                elif arg == 'or' :
                    self.stack.append( a or b )
                
            elif cmd == 'jmpf' :
                
                c = self.stack.pop(-1)
                if not c :
                    cp += int(arg)
                    
            elif cmd == 'jump' :
                
                cp += int(arg)
                
            cp += 1
            
            
        return
    
    
    
class GrammerChecker(object):
    
    grammer = r'''
        file       := ( [ ]*, (statement, [ ]*)?, ( ';' / '\n' ) )*
        >block<    := ( [ ]*, (statement, [ ]*)?, ( ';' / '\n' ) )*
        
        statement  := ifstate / forstate / whilestate / assignment / expression
        assignment := var, [ ]*, '=', [ ]*, expr
        expression := expr
        
        forstate   := 'for', [ ]+, var, [ ]+, 'in', [ ]+, expr, [ ]*, '{', block, '}'
        whilestate := 'while', [ ]*, expr, [ ]*, '{', block, '}'
        ifstate    := 'if', [ ]*, expr, [ ]*, '{', block, '}', elifstate*, elsestate?
        elifstate  := [ \n]*, 'elif', [ \n]*, '{', block, '}'
        elsestate  := [ \n]*, 'else', [ \n]*, '{', block, '}'
        
        expr       := expr2, ( [ ]*, relop, [ ]*, expr2 )*
        >expr2<    := funcexpr / number / ( '(', expr, ')' ) / var
        funcexpr   := var, '(', [ ]*, args?, [ ]*, ')'
        args       := expr, ( [ ]*, ',', [ ]*, expr )*
        
        relop      := [-+*/] / '==' / '!=' / 'and' / 'or'
        
        var        := [a-zA-Z_]+, [a-zA-Z0-9_]*
        number     := [0-9]+, ( '.', [0-9]+ )?
    '''
    
    parser = Parser(grammer,'file')
    
    def check( self, script ):
        
        st, nodes, ed = self.parser.parse(script)
        
        if ed == len(script):
            print 'Grammer OK'
        else :
            print 'Grammer ERROR'
            print script[:ed]
        
        for node in nodes :
            self.info( script, node, 0 )
        
        return
        
    def info( self, script, node, lv ):
        
        name, st, ed, children = node
        
        print ' '*(lv*4), name, script[st:ed] if children == [] else ''
        
        for child in children :
            self.info( script, child, lv+1 )
        
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
if a-11 {
    print(123)
} elif a-10 {
    print(456)
} else {
    print(789)
}
while (a) {
    print(a)
    a=a-1
}
'''
    
    import pprint
    print '== code tree =='
    checker = GrammerChecker()
    checker.check(script)
    
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
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    