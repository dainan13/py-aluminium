from simpleparse.parser import Parser
from simpleparse import generator

import types

#MATCH_JUMP          MATCH_FAIL
#MATCH_NOWORD        MATCH_SWORDSTART
#MATCH_LOOPCONTROL_RESET -1

stkeys = [ ln.split(None, 1) for ln in '''\
ALLIN             11
ALLNOTIN          12
IS                13
ISIN              14
ISNOTIN           15
WORD              21
WORDSTART         22
WORDEND           23
ALLINSET          31
ISINSET           32
ALLINCHARSET      41
ISINCHARSET       42
MAX_LOWLEVEL      99
FAIL              100
EOF               101
SKIP              102
MOVE              103
JUMPTARGET        104
MAX_SPECIALS      199
SWORDSTART        211
SWORDEND          212
SFINDWORD         213
CALL              201
CALLARG           202
TABLE             203
SUBTABLE          207
TABLEINLIST       204
SUBTABLEINLIST    208
LOOP              205
LOOPCONTROL       206
JUMP_TO           0
JUMP_MATCHOK      1000000
JUMP_MATCHFAIL    -1000000
MOVE_EOF          -1
MOVE_BOF          0
FAIL_HERE         1
THISTABLE         999
LOOPCONTROL_BREAK 0
CALLTAG           (1 << 8)
APPENDTAG         (1 << 9)
APPENDTAGOBJ      (1 << 10)
APPENDMATCH       (1 << 11)
LOOKAHEAD         (1 << 12)
'''.splitlines() ]

stkeys = dict([ (eval(v),k) for k, v in stkeys ])


def gen( d ):
    
    for i in d :
        yield i
        
    return


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
        >expr2<    := funcexpr / number / ( '(', [ ]*, expr, [ ]*, ')' ) / var / string / array
        funcexpr   := var, '(', [ ]*, args?, [ ]*, ')'
        args       := expr, ( [ ]*, ',', [ ]*, expr )*
        array      := '[', [ ]*, expr, ( [ ]*, ',', [ ]*, expr )*, [ ]*, ']'
        
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
        
        gtree = self.parser.parse(script)
        
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
            self.code.append( 'pop 1' )
            
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
        
        elif name == 'array' :
            
            self.code.append( 'arry 0' )
            
            for child in children :
                self._compile( script, child )
                self.code.append( 'apnd 2' )
            
        elif name == 'statement' :
            
            for child in children :
                self._compile( script, child )
            
        else :
            
            raise Exception, ('unkown node', name)
        
        return
    
    def binarycode( self ):
        
        r = []
        
        for code in self.code :
            cmd, arg = code.split(None,1)
            
            if cmd == 'halt' :
                r.append( (cmd, int(arg)) )
            elif cmd == 'pop' :
                r.append( (cmd, int(arg)) )
            elif cmd == 'set' :
                r.append( (cmd, arg) )
            elif cmd == 'sete' :
                r.append( (cmd, arg) )
            elif cmd == 'del' :
                r.append( (cmd, arg) )
            elif cmd == 'push' :
                r.append( (cmd, eval(arg)) )
            elif cmd == 'pvar' :
                r.append( (cmd, arg) )
            elif cmd == 'call' :
                r.append( (cmd, int(arg)) )
            elif cmd == 'oper' :
                r.append( (cmd, arg) )
            elif cmd == 'jmpf' :
                r.append( (cmd, int(arg)) )
            elif cmd == 'jmpt' :
                r.append( (cmd, int(arg)) )
            elif cmd == 'jump' :
                r.append( (cmd, int(arg)) )
            elif cmd == 'try' :
                r.append( (cmd, int(arg)) )
            elif cmd == 'ntry' :
                r.append( (cmd, int(arg)) )
            elif cmd == 'excp' :
                r.append( (cmd, arg) )
            elif cmd == 'arry' :
                r.append( (cmd, int(arg)) )
            elif cmd == 'apnd' :
                r.append( (cmd, int(arg)) )
            elif cmd == 'iter' :
                r.append( (cmd, int(arg)) )
            elif cmd == 'next' :
                r.append( (cmd, int(arg)) )
            
        return r
    
    def run( self, ns=None ):
        
        if ns != None :
            self.namespace.update(ns)
        
        cp = 0
        ep = []
        
        error = None
        
        while( True ):
            
            cmd, arg = self.code[cp].split(None,1)
            
            #print ' '*10, cp, cmd, arg, self.stack
            
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
            
            elif cmd == 'arry' :
                self.stack.append( [] )
            
            elif cmd == 'apnd' :
                ax = self.stack.pop( -1 ) 
                self.stack[-1].append( ax )
            
            elif cmd == 'iter' :
                if type( self.stack[-1] ) != types.GeneratorType :
                    self.stack.append( gen(self.stack.pop(-1)) )
            
            elif cmd == 'next' :
                try :
                    self.stack.append( self.stack[-1].next() )
                    self.stack.append(True)
                except StopIteration as e:
                    self.stack.append(False)
                    
            
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
        >expr2<    := funcexpr / number / ( '(', [ ]*, expr, [ ]*, ')' ) / var / string / array
        funcexpr   := var, '(', [ ]*, args?, [ ]*, ')'
        args       := expr, ( [ ]*, ',', [ ]*, expr )*
        array      := '[', [ ]*, expr, ( [ ]*, ',', [ ]*, expr )*, [ ]*, ']'
        
        relop      := [-+*/] / '==' / '!=' / '&&' / '||'
        
        string     := string1 / string2
        >string1<  := "'", -[']+, "'"
        >string2<  := '"', -["]+, '"'
        var        := [a-zA-Z_]+, [a-zA-Z0-9_]*
        number     := [0-9]+, ( '.', [0-9]+ )?
    '''
    
    parser = Parser(grammer,'file')
    
    def check( self, script ):
        
        #st, nodes, ed = self.parser.parse(script)
        st, nodes, ed = self.tagbuilder(script)
        
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
        
    def state( self ):
        
        self.tagcmds = {}
        
        parser = generator.buildParser(self.grammer).parserbyname('file')
        r = [ id(node) for node in parser ]
        parser = [ self.compilestate(node) for node in parser ]
        
        return r
        
    def compilestate( self, tag ):
        
        idtag = id(tag)
        
        if idtag in self.tagcmds :
            return
        
        self.tagcmds[idtag] = None
        
        name = tag[0]
        cmd = stkeys[tag[1]]
        arg = tag[2]
        jmpf = None if len(tag)<4 else tag[3]
        jmpt = 1 if len(tag)<5 else tag[4]
        
        if len(tag) > 5 :
            raise Exception, '...'
        
        if cmd == 'TABLEINLIST' :
            cmd = 'TABLE'
            arg = arg[0][arg[1]]
        
        if cmd == 'SUBTABLEINLIST' :
            cmd = 'SUBTABLE'
            arg = arg[0][arg[1]]
        
        if cmd == 'TABLE' or cmd == 'SUBTABLE' :
            
            for child in arg :
                self.compilestate(child)
            
            arg = [ id(child) for child in arg ]
        
        self.tagcmds[idtag] = (name,cmd,arg,jmpf,jmpt)
        
        return
        
    def tagbuilder( self, code ):
        
        cur, nodes = self.taglist( code, self.state(), 0 )
        
        return (0, nodes, cur)
        
    def taglist( self, code, tagparsers, st ):
        
        cur = st
        r = []
        
        tagpos = 0
        
        mxtag = len(tagparsers)

        while( tagpos < mxtag ):
        
            print st, tagpos, '/', mxtag, tagparsers[tagpos]
        
            tag = self.tagcmds[tagparsers[tagpos]]
            
            jmpf = tag[3]
            jmpt = tag[4]
            
            _cur, node = self.tag( code, tag, cur )
            
            jump = jmpf if _cur == cur else jmpt 
            jump = jmpt if tag[1] == 'EOF' else jump
            
            if jump is None :
                break
            
            tagpos += jump
            if _cur != cur :
                r.extend(node)
            cur = _cur
            
        else :
            
            return cur, r
        
        return st, []
    
    def tag( self, code, tag, st ):
        
        cur = st
        r = []
        
        name = tag[0]
        cmd = tag[1].split()[0]
        arg = tag[2]
        
        childrens = []
        
        print name, cmd, arg, cur, code[:cur+1]
        
        if cmd == 'SUBTABLE' or cmd == 'TABLE' :
            cur, childrens = self.taglist( code, arg, cur )
        
        elif cmd == 'ALLIN':
            while( code[cur] in arg ):
                cur += 1
        
        elif cmd == 'ALLNOTIN':
            while( code[cur] not in arg ):
                cur += 1
        
        elif cmd == 'ISIN' :
            if code[cur] in arg :
                cur += 1
        
        elif cmd == 'WORD' :
            if code[cur:cur+len(arg)] == arg :
                cur += len(arg)
        
        elif cmd == 'EOF' :
            pass
        
        else :
            raise Exception, ('UnkownTag', tag[1])

        if name :
            return cur, [(name,st,cur,childrens)]
        else :
            return cur, []
    
class GrammerCheckerTest( GrammerChecker ):
    
    #http://www.egenix.com/products/python/mxBase/mxTextTools/doc/#_Toc293606134
    
    grammer = r'''
        file       := [A-Z]*, 'ab'+, statement+
        statement  := var+, 'gh'
        var        := 'cd' / 'ef' / 'ij'
    '''
    
    # 11 14 21 101 203 204 207 208
    pass
    
def test2():
    
    import pprint
    
    checker = GrammerCheckerTest()
    
    #pprint.pprint( generator.buildParser(checker.grammer).parserbyname('file') )
    
    print checker.state()
    print
    for k, v in checker.tagcmds.items():
        print k, v
    
    print set( [ v[1] for v in checker.tagcmds.values() ] )
    
    
    print
    print 
    print checker.tagbuilder('AAAabcdefghcdgh')
    
    return
    
def foo( a, b ):
    
    print a, b
    return a**b


def test():
    
    vm = EasyScript()
    
    script = '''
a = foo( 1 +(4 / 2) , abc )
b = a
a = a+1
a = 1+a
print(a);print(b)

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

for i in [1,2,4,8,16,32] {
    print(i)
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

'''

#try {
#    print(a)
#} except Exception as e {
#    print('var a not found')
#    print(e)
#}

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
    bc = zip(*vm.binarycode())
    print list(bc[0])
    print list(bc[1])
    
    print '== run result ==' 
    vm.run( {'foo':foo, 'abc':2, 'print':pprint.pprint, 'Exception':Exception} )
    
    return
    

if __name__ == '__main__' :
    

    test2()
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    