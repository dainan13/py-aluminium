============
 autolog
============


 design
=============

decorator ::
    
    def bar( a ):
        raise Exception('an exception raised')
    
    @autolog( logger )
    def foo( b ):
        bar( b*b )
    
    foo( 5 )
    
get a log ::

    ExceptionName: Exception
    ExceptionInfo: an exception raised
    Path:
        - FunctionName: bar
          Arguments:
            - a: 25
          Position: 2
          ExceptionName: Exception
          ExceptionInfo: a exception raised
    
another example ::

    def bar( a ):
        raise ValueError('a value error raised %d' % (a,))
        
    @autolog( logger )
    def foo( b ):
        try :
            bar( b )
        except :
            pass
        
        bar( b*b )
    
    foo( 5 )
    
get a log ::

    ExceptionName: ValueError
    ExceptionInfo: a value error raised 25
    Path:
        - FunctionName: bar
          Arguments:
            - a: 5
          Position: 2
          ExceptionName: ValueError
          ExceptionInfo: a value error raised 5
        - FunctionName: bar
          Arguments:
            - a: 25
          Position: 2
          ExceptionName: ValueError
          ExceptionInfo: a value error raised 25