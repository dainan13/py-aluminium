



class this ( object ):
    
    def __init__ ( self, *args, **kwargs ):
        
        kwargs['this'] = lambda x : x
        
        self.__la = args
        self.__ka = kwargs
        
        return
    
    def __call__ ( self, func ):
        
        for builder in args :
            func.func_globals[gva].update()
        
        for gva, builder in self.__atr.items() :
            func.func_globals[gva] = builder(func)
        
        return func

import new

def Al_Decorator( wrapper ):
    
    def _wrapper ( func ):
        
        new.function()
        
        newfunc = wrapper( func )
        
        newfunc._decorator = func
        newfunc.__name__ = cmd.__name__
        newfunc.__doc__  = cmd.__doc__
        
        return newfunc
    
    return _wrapper


if __name__ == '__main__' :
    
    @this()
    def foo():
        '''
        a function of foo
        '''
        
        print 'this function\'s docstring is :', this.__doc__
        
    foo()