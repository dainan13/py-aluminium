
import easydecorator


class TypeError(TypeError):
    pass

@easydecorator.decorator_builder(1)
def autocheck ( old, checkers, *args, **kwargs ):
    
    r_old = easydecorator.real(old)
    
    argc = r_old.func_code.co_argcount
    argv = r_old.func_code.co_varnames[:argc]
    
    v_args = args[:argc]
    r_args = args[argc:]
    
    r_kwargs = dict([ (k, v) for k, v in kwargs.items() if k in argv ])
    
    for k, v in zip( argv, v_args ):
        if k in checkers and checkers[k](v) == False :
            raise TypeError( 'argument %s error'% (k,), v )
    
    for k, v in kwargs :
        if k not in argv :
            continue
        
        if k in checkers and checkers[k](v) == False :
            raise TypeError( 'argument %s error'% (k,), v )
    
    if len(r_old.func_code.co_varnames) > argc :
        
        k = r_old.func_code.co_varnames[argc]
        v = r_args
        
        if k in checkers and checkers[k](v) == False :
            raise TypeError( 'argument %s error' % (k,), v )
    
    if len(r_old.func_code.co_varnames) > argc + 1 :
        
        k = r_old.func_code.co_varnames[argc+1]
        v = r_kwargs
        
        if k in checkers and checkers[k](v) == False :
            raise TypeError( 'argument %s error'% (k,), v )
    
    return old( *args, **kwargs )
    
    

@easydecorator.decorator_builder(1)
def replacer ( old, fake, *args, **kwargs  ):
    
    try :
        return old( *args, **kwargs )
    except TypeError :
        return fake( *args, **kwargs ) if callable(fake) else fake







if __name__ == '__main__':
    
    import traceback
    import types
    
    checkers = { 'a': lambda x : type(x) == types.IntType ,
                 'b': lambda x : type(x) in types.StringTypes,
                 'args': lambda xs : \
                                 all([ type(x) == types.IntType for x in xs ]),
                 'kwargs': lambda xd : \
                             all([ type(x) == type(v) for k, v in xd.items() ]),
               }
    
    @autocheck(checkers)
    def foo( a, b ):
        print 'a>', a
        print 'b>', b
        
    @autocheck(checkers)
    def bar( a, b, *args, **kwargs ):
        print 'a>', a
        print 'b>', b
        print 'args>', args
        print 'kwargs>', kwargs
        
        
    
    
    
    print "foo( 1, 'a' )"
    print foo( 1, 'a' )
    print
    
    
    
    print "foo( 1, 2 )"
    try :
        print foo( 1, 2 )
    except :
        traceback.print_exc()
    print
        
    
    
    print "bar( 1, 'a', 1, 2, 3 )"
    print bar( 1, 'a', 1, 2, 3 )
    print
    
    
    
    
    print "bar( 1, 'a', 1, 2, 'b' )"
    try :
        print bar( 1, 'a', 1, 2, 'b' )
    except :
        traceback.print_exc()
    print
    
    
    
    
    @replacer( 'hello world' )
    @autocheck(checkers)
    def foo2( a, b ):
        print 'a>', a
        print 'b>', b
    
    
    print "foo2( 1, 2 )"
    print foo2( 1, 2 )
    print