
import sys
import re
import new

#InteractiveInterpreter

def parseline( l ):
    
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
    lines = [ l for l in lines if l.strip() != '' ]
    segs = [ l.strip(':') for l in lines if not l.startswith(' ') ]
    #rlines = [ l for l in lines if l.startswith(' ')]
    lines = [ '    '+parseline(l) for l in lines ]
    #rliens = [ parseline(l) for l in rlines ]
    
    code = '\n'.join(lines)
    #rcode = '\n'.join(rlines)
    
    p = '' if lines[0].startswith(' ') else 'pass\n'
    
    segs = dict(zip([True]+segs,segs+[False]))
    
    #print
    #print 'd0>', vars()
    #sys._current_frames().values()[-1].f_locals.update(goto[0])
    #print 'd1.5>', sys._current_frames().values()
    #print 'd1>', goto[0]
    #print 'd2>', vars()
    #print 'd3>', sys._current_frames().values()[-1].f_locals
    
    code = """
    
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
    #rcode = define + '\n' + rcode
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

    #gl = f.func_globals
    #lo = {'sys':sys}
    
    #exec( rcode, gl, lo )
    #rf = lo[f.func_name]
    
    gl = f.func_globals
    lo = {}

    #print define
    #print code
    
    exec( code, gl, lo )
    gl['__goto__'] = lo['__goto__']
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