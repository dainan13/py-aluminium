
import sys
import re
import new

#InteractiveInterpreter

def parseline( l ):
    
    if l.strip() == '':
        return ''
    
    if not l.startswith(' '):
        return 'if goto[1]=="%s":' % (l.strip(':'),)
    
    xl = l.lstrip()
    sp = len(l) - len(xl)
    
    if xl.startswith('goto'):
        return ' '*sp + 'return "%s", vars().copy(), None' %(xl.split()[1],)
        
    if xl.startswith('return'):
        return ' '*sp + 'return None, None, %s' %(xl[6:])
        
    return l




def goto( f ):
    
    fcode = f.__doc__
    
    lines = fcode.splitlines()
    #lines = [ l for l in lines if l.strip() != '' ]
    segs = [ l.strip(':') for l in lines 
             if l.strip() != '' and not l.startswith(' ') ]
    lines = [ '    '+parseline(l) for l in lines ]
    
    code = '\n'.join(lines)
    
    p = '' if lines[0].startswith(' ') else 'pass\n'
    
    segs = dict(zip([True]+segs,segs+[False]))
    
    #print
    #print 'd0>', vars()
    #sys._current_frames().values()[-1].f_locals.update(goto[0])
    #print 'd1.5>', sys._current_frames().values()
    #print 'd1>', goto[0]
    #print 'd2>', vars()
    #print 'd3>', sys._current_frames().values()[-1].f_locals
    
    code = """\
    for __k in goto[0].keys() :
        exec( __k + ' = goto[0][__k]'  )
    if goto[1] == True :
""" + p + code + ("""
    return %s[goto[1]], vars().copy(), None
""" %(str(segs),) )
    
    define = f.func_code.co_varnames
    
    kwargs = None
    if f.func_code.co_flags & 0x08 :
        kwargs = '**'+define[-1]
        define = define[:-1]
        
    args = None
    if f.func_code.co_flags & 0x04 :
        args = '*'+define[-1]
        define = define[:-1]
    
    define = list(define) + \
             ([args] if args else []) + ([kwargs] if kwargs else [])
    
    define = 'def ' + f.func_name + ' ( ' + ', '.join(define) + ' ):'
    
    code = "def __goto__( goto ):\n" + code
    #code = "def " + f.func_name + " ( goto ):\n" + code
    define = define + '\n' + """
    v = vars()
    n = True
    r = None
    
    n, v, r = __goto__( (v, n) )
    v.pop('goto',None)
    #print 'debug>', n, v, r
    
    while( n ):
        n, v, r = __goto__( (v, n) )
        v.pop('goto',None)
    
    return r
"""

    gl = f.func_globals
    lo = {}

    #print define
    #print code
    
    #new.code( argcount, nlocals, stacksize, flags, codestring, 
    #          constants, names, varnames, filename, name, firstlineno, lnotab) 
    
    linep = 2
    linep += 1 if p else 0
    
    exec( code, gl, lo )
    fg = lo['__goto__'].func_code
    fg = new.code( fg.co_argcount, fg.co_nlocals, fg.co_stacksize, 
                   fg.co_flags, fg.co_code, fg.co_consts, fg.co_names,
                   fg.co_varnames, f.func_code.co_filename,
                   f.func_code.co_name, f.func_code.co_firstlineno-linep,
                   fg.co_lnotab
                 )
    fg = new.function( fg, gl)
    
    #gl['__goto__'] = lo['__goto__']
    gl['__goto__'] = fg
    lo = {}
    
    exec( define, gl, lo )
    
    return lo[f.func_name]






if __name__ == "__main__" :
    
    
    @goto
    def test( prompt ):
        r"""
        print prompt, "hello world"
        i = 0
loop:
        print prompt, i
        i += 1
        if i > 10 :
            goto end
        goto loop
end:
        pass
        """
    
    test( "]" )
    
    @goto
    def test2( prompt ):
        r"""
loop:
        i = 6
        print prompt, i
        i += 1
        if i > 10 :
            goto end
        goto loop
end:
        pass
        """
    
    test( "]" )