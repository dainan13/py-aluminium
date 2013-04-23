from simpleparse.parser import Parser

class EasyScript(object):
    
    grammer = r'''
        file       := ( [ ]*, (statement, [ ]*)?, ( ';' / '\n' ) )*
        >block<    := ( [ ]*, (statement, [ ]*)?, ( ';' / '\n' ) )*
        
        statement  := ifstate / forstate / break / continue / whilestate / delstate / trystate / assignment / expression
        assignment := var, [ ]*, '=', [ ]*, expr
        expression := expr
        
        delstate   := 'del', [ ]+, var
        forstate   := 'for', [ ]+, var, [ ]+, 'in', [ ]+, expr, [ ]*, '{', block, [ ]*, '}'
        whilestate := 'while', [ ]*, expr, [ ]*, '{', block, [ ]*, '}'
        ifstate    := 'if', [ ]*, expr, [ ]*, '{', block, [ ]*, '}', elifstate*, elsestate?
        elifstate  := [ \n]*, 'elif', [ ]*, expr, [ ]*, '{', block, '}'
        elsestate  := [ \n]*, 'else', [ \n]*, '{', block, '}'
        trystate   := 'try', [ ]*, '{', block, [ ]*, '}', exceptstate+
        exceptstate:= [ \n]*, 'except', [ ]+, var, [ ]+, 'as', [ ]+, var, [ ]*, '{', block, [ ]*, '}'
        
        break      := 'break'
        continue   := 'continue'
        
        expr       := expr2, ( [ ]*, relop, [ ]*, expr2 )*
        >expr2<    := funcexpr / number / ( '(', expr, ')' ) / var / string
        funcexpr   := var, '(', [ ]*, args?, [ ]*, ')'
        args       := expr, ( [ ]*, ',', [ ]*, expr )*
        
        relop      := [-+*/] / '==' / '!=' / '&&' / '||'
        
        string     := string1 / string2
        >string1<  := "'", -[']+, "'"
        >string2<  := '"', -["]+, '"'
        var        := [a-zA-Z_]+, [a-zA-Z0-9_]*
        number     := [0-9]+, ( '.', [0-9]+ )?
    '''
    
    parser = Parser(grammer,'file')
    
    def __init__( self ):
        
        self.namespace = {}
        self.stack = []
        self.code = []
        self.segpos = {}
        self.loopstack = []
        
        return
        
    def compile( self, script ):
        
        gtree = vm.parser.parse(script)
        
        for st in gtree[1] :
            self._compile( script, st )
        
        for i, code in enumerate(self.code) :
            
            cmd, arg = code.split(None,1)
            
            if cmd in ( 'jump', 'jmpt', 'jmpf', 'try' ):
                
                self.code[i] = '%s %s' % (cmd, self.segpos[arg]-i-1)
        
        self.code.append('halt 0')
        
        return 
        
    def setsegname( self, segname ):
        self.segpos[segname] = len(self.code)
        return
    
    op_pri = {
        '+'  : 1,
        '-'  : 1,
        '*'  : 0,
        '/'  : 0,
        '==' : 2,
        '!=' : 2,
        '&&' : 3,
        '||' : 3,
    }
    
    def _compile( self, script, node, pst=None ):
        
        name, st, ed, children = node
        
        if name == 'assignment' :
            
            assignmentvar = children.pop(0)
            assignmentvar = script[assignmentvar[1]:assignmentvar[2]]
            
            for child in children :
                self._compile( script, child )
            
            self.code.append( 'set %s' % (assignmentvar,) )
        
        elif name == 'forstate':
            
            assignmentvar = children.pop(0)
            assignmentvar = script[assignmentvar[1]:assignmentvar[2]]
            
            expr = children.pop(0)
            self._compile( script, expr )
            
            self.code.append( 'iter 1' )
            self.setsegname( '%sFORSTART' % (st,) )
            self.code.append( 'next 1' )
            self.code.append( 'jmpf %sFOREND' % (st,) )
            self.code.append( 'set %s' % (assignmentvar,) )
            
            while( children and children[0][0] == 'statement' ):
                child = children.pop(0)
                self._compile( script, child )
                
            self.code.append( 'jump %sFORSTART' % (st,))
            self.setsegname( '%sFOREND' % (st,) )
            
        elif name == 'expression' :
            
            for child in children :
                self._compile( script, child )
            
            self.code.append( 'pop 1' )
        
        elif name == 'trystate' :
            
            self.code.append( 'try %sEXCEPTSTART' % (st,) )
            
            while( children and children[0][0] == 'statement' ):
                child = children.pop(0)
                self._compile( script, child )
            
            self.code.append( 'ntry 0' )
            self.code.append( 'jump %sTRYEND' % (st,) )
            
            self.setsegname( '%sEXCEPTSTART' % (st,) )
            self.code.append( 'ntry 1' )
            
            while( children and children[0][0] == 'exceptstate' ):
                child = children.pop(0)
                self._compile( script, child, st )
            
            self.setsegname( '%sTRYEND' % (st,) )
            
        elif name == 'exceptstate' :
            
            eclass = children.pop(0)
            eclass = script[eclass[1]:eclass[2]]
            evar = children.pop(0)
            evar = script[evar[1]:evar[2]]
            
            self.code.append( 'excp %s' % (eclass,) )
            self.code.append( 'jmpf %sEXCEPTEND' % (st,) )
            self.code.append( 'sete %s' % (evar,) )
            
            for child in children :
                self._compile( script, child )
                
            self.code.append( 'jump %sTRYEND' % (pst,) )
            self.setsegname( '%sEXCEPTEND' % (st,) )
            
        elif name == 'delstate' :
            
            delvar = children.pop(0)
            delvar = script[delvar[1]:delvar[2]]
            
            self.code.append( 'del %s' % (delvar,) )
        
        elif name == 'whilestate' :
            
            self.loopstack.append((st,'WHILE'))
            
            self.setsegname( '%sWHILESTART' % (st,) )
            condexpr = children.pop(0)
            self._compile( script, condexpr )
            self.code.append( 'jmpf %sWHILEEND' % (st,) )
            
            while( children and children[0][0] == 'statement' ):
                child = children.pop(0)
                self._compile( script, child )
            
            self.code.append( 'jump %sWHILESTART' % (st,) )
            self.setsegname( '%sWHILEEND' % (st,) )
            
            self.loopstack.pop(-1)
            
        elif name == 'continue' :
            
            lst, lname = self.loopstack[-1]
            self.code.append( 'jump %s%sSTART' % (lst,lname) )
            
        elif name == 'break' :
            
            lst, lname = self.loopstack[-1]
            self.code.append( 'jump %s%sEND' % (lst,lname) )
            
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
            
            self.code.append( 'pvar %s' % ( func, ) )
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
        
        elif name == 'string' :
            
            self.code.append( 'push %s' % ( script[st:ed], )  )
        
        elif name == 'var' :
            
            self.code.append( 'pvar %s' % ( script[st:ed], )  )
        
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
        ep = []
        
        error = None
        
        while( True ):
            
            cmd, arg = self.code[cp].split(None,1)
            
            #print cp, cmd, arg, self.stack
            
            if cmd == 'halt' :
                break
            
            if cmd == 'pop' :
                for i in range(int(arg)):
                    self.stack.pop(-1)
            
            elif cmd == 'set' :
                self.namespace[arg] = self.stack.pop(-1)
            
            elif cmd == 'sete' :
                self.namespace[arg] = error
            
            elif cmd == 'del' :
                self.namespace.pop( arg, None )
            
            elif cmd == 'push' :
                self.stack.append( eval(arg) )
                
            elif cmd == 'pvar' :
                try :
                    self.stack.append( self.namespace[arg] )
                except Exception, e:
                    if ep != [] :
                        error = e
                        cp = ep[-1][0]
                    else :
                        raise
                    
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
                elif arg == '&&' :
                    self.stack.append( a and b )
                elif arg == '||' :
                    self.stack.append( a or b )
                
            elif cmd == 'jmpf' :
                if not self.stack.pop(-1) :
                    cp += int(arg)
            
            elif cmd == 'jmpt' :
                if self.stack.pop(-1) :
                    cp += int(arg)
            
            elif cmd == 'jump' :
                cp += int(arg)
            
            elif cmd == 'try' :
                ep.append( ( cp+int(arg), len(self.stack) ) )
                
            elif cmd == 'ntry' :
                _cp, _sp = ep.pop(-1)
                if arg != '0' :
                    self.stack = self.stack[:_sp]
                
            elif cmd == 'excp' :
                self.stack.append( isinstance(error, self.namespace[arg]) )
            
            else :
                raise Exception, (cmd, 'cmd not found')
            
            
            cp += 1
            
            
        return
    
    
    
class GrammerChecker(object):
    
    grammer = r'''
        file       := ( [ ]*, (statement, [ ]*)?, ( ';' / '\n' ) )*
        >block<    := ( [ ]*, (statement, [ ]*)?, ( ';' / '\n' ) )*
        
        statement  := ifstate / forstate / break / continue / whilestate / delstate / trystate / assignment / expression
        assignment := var, [ ]*, '=', [ ]*, expr
        expression := expr
        
        delstate   := 'del', [ ]+, var
        forstate   := 'for', [ ]+, var, [ ]+, 'in', [ ]+, expr, [ ]*, '{', block, [ ]*, '}'
        whilestate := 'while', [ ]*, expr, [ ]*, '{', block, [ ]*, '}'
        ifstate    := 'if', [ ]*, expr, [ ]*, '{', block, [ ]*, '}', elifstate*, elsestate?
        elifstate  := [ \n]*, 'elif', [ ]*, expr, [ ]*, '{', block, '}'
        elsestate  := [ \n]*, 'else', [ \n]*, '{', block, '}'
        trystate   := 'try', [ ]*, '{', block, [ ]*, '}', exceptstate+
        exceptstate:= [ \n]*, 'except', [ ]+, var, [ ]+, 'as', [ ]+, var, [ ]*, '{', block, [ ]*, '}'
        
        break      := 'break'
        continue   := 'continue'
        
        expr       := expr2, ( [ ]*, relop, [ ]*, expr2 )*
        >expr2<    := funcexpr / number / ( '(', expr, ')' ) / var / string
        funcexpr   := var, '(', [ ]*, args?, [ ]*, ')'
        args       := expr, ( [ ]*, ',', [ ]*, expr )*
        
        relop      := [-+*/] / '==' / '!=' / '&&' / '||'
        
        string     := string1 / string2
        >string1<  := "'", -[']+, "'"
        >string2<  := '"', -["]+, '"'
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
        
        for child in children or [] :
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

if a == 11 {
    if b == 9 {
        print("HAHAHA")
    }
}

if a == 10 {
    print(123)
} elif a == 11 {
    print(456)
} else {
    print(789)
}


while (a) {
    
    if a == 9 {
        a = a-1
        continue
    }
    
    print(a)
    a=a-1
    if a == 4 {
        break
    }
}

del a

try {
    print(a)
} except Exception as e {
    print('var a not found')
    print(e)
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
    vm.run( {'foo':foo, 'abc':2, 'print':pprint.pprint, 'Exception':Exception} )
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    