=========================
 Easydecorator
=========================




 Designs
=========================

the aim is a decorator builder libuary, which helping the user to write
decorator easy.

in common, we offten write the decorator like this ::

    def decorator_builder( argA, argB ):
    
        def _deco( old ):
            
            def _new( * args, ** args ):
            
                ... # with use old, argA, argB
                
            ... # change `_new`'s name, docstring and so on...
                
            return _new
            
        return _deco
        
and use it like ::

    @decorator_builder( A, B )
    def foo( a, b ):
        return a+b

there is nested function factories in the builder, I want to simplify the code.
it may be like this ::

    # print function name and arguments when it has been called.
    @decorator_builder( promote )
    def deco( * args, ** kwargs ):
        
        ar = [ str(a) for a in args ]
        ar += [ str(k)+'='+str(v) for k, v in kwargs.items() ]
        ar = old.__name__ + '(' + ', '.join(ar) + ')'
        
        print promote, '>', ar
        
        return old( * args, ** kwargs )

    @deco('hello world')
    def foo( a, b ):
        ...

and you will get ::

    >>> foo( 1, 2 )
    hello world > foo( 1, 2 )
    3
  
In decorator, we offten use the function's attribute as argument,
but in decorator builder, the arguments not all come from the function's
attribute, it often as function input. so we need a way to extract the
function'a attribute to argument ::

    @de( deco << lambda x : x.__doc__.strip(' \r\n') )
    def foo():
        '''
        hello world
        '''
        ...
        
it same as ::

    def foo():
        '''
        hello world
        '''
        ...
        
    foo = deco( (lambda x : x.__doc__.strip(' \r\n'))(foo) )( foo )
    
also you can write like this :

    newdeco = deco << lambda x : x.__doc__.strip(' \r\n')
    
    @newdeco
    def foo():
        '''
        hello world
        '''
        ...


.. Note ::

    In current, the decorator_builder in easydocrator not same as design,
    it cut off the namespace design, instead, you must declare the var
    by yourself, and input a arguments' number ::
    
        @decorator_builder(1)
        def deco( old, promote, * args, ** kwargs ):
            
            ar = [ str(a) for a in args ]
            ar += [ str(k)+'='+str(v) for k, v in kwargs.items() ]
            ar = old.__name__ + '(' + ', '.join(ar) + ')'
            
            print promote, '>', ar
            
            return old( * args, ** kwargs )
    
        @deco('hello world')
        def foo( a, b ):
            ...
            
            
 Operation
-------------------------

======================= ===============================================================================
 function/operation      tail
======================= ===============================================================================
 decorator_builder       generate a decorator builder
 this_builder            generate a decorator builder, and the decorator will not instead the old one.
 this                    add a var named `this` in function, the value is the function self.
 de                      do nothing, only return the value when it be called
 <<                      an argument stream
======================= ===============================================================================