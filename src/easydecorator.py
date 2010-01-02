
import types

class Deal( object ):
    
    def __init__( self, value ):
        self.value = value
        
    def __call__( self, *args, **kwargs ):
        return self.value( *args, **kwargs )

de = Deal

class Decorator( object ):
    
    def __init__( self, _new, _args ):
        
        self._new = _new
        self._args = _args
        
    def __call__( self, _old ):
        
        def _decorator( *args, **kwargs ):
            return self._new( _old, *(self._args+args), **kwargs )
        
        _decorator._decorator = _old
        _decorator.__name__ = _old.__name__
        _decorator.__doc__  = _old.__doc__
        
        return _decorator


class This ( Decorator ):
    
    def __call__( self, _old ):
        
        self._new( _old, *self._args )
        
        return _old


class DecoratorBuilder( object ):
    
    def __init__ ( self, _new, _argscount, deco = Decorator ):
        
        self._new = _new
        self._argscount = _argscount
        self._d = deco
        
    def __call__ ( self, *_args ):
        
        if len(_args) != self._argscount :
            raise TypeError, '%s decorator takes '\
                             'exactly %d arguments (%d given)' \
                                % ( self._new.__name__,
                                    self._argscount,
                                    len(_args)
                                  )
        
        return self._d( self._new, _args )
        
    def __lshift__ ( self, _args ):
        
        if type(_args) not in ( types.ListType, types.TupleType ) :
            _args = (_args,)
        
        return lambda x : \
                    self( *[ arg if not callable(arg) else arg(x) \
                             for arg in _args
                           ]
                        )(x)

def decorator_builder( number ):
    return lambda x : DecoratorBuilder( x, number )
    
def this_builder( number ):
    return lambda x : DecoratorBuilder( x, number, This )




@this_builder(0)
def this( _old ):
    
    _old.func_globals['this'] = _old
    
    return






if __name__ == '__main__' :
    

    @decorator_builder(1)
    def bar( _old, _promote, *args, **kwargs ):
        
        ar = [ str(a) for a in args ]
        ar += [ str(k)+'='+str(v) for k, v in kwargs.items() ]
        ar = _old.__name__ + '(' + ', '.join(ar) + ')'
        
        print _promote, ar, '>', 'start to run'
        r = _old( *args, **kwargs )
        print _promote, ar, '=', str(r), '>', 'fin'
        
        return r
    
    
    @bar('bar>')
    @de( bar << (lambda x : x.__doc__.strip(' \r\n')+' >') )
    @this()
    def foo( a, b ):
        ''' 
        hello world
        '''
        
        print 'this function\'s docstring is :', this.__doc__
        
        return a+b
        
    foo(34,56)
    