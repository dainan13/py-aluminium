
import easydecorator
import traceback
import sys

@easydecorator.decorator_builder(0)
def safe( old, *args, **kwargs ):
    
    try :
        return old( *args, **kwargs )
    except :
        traceback.print_exc()
    
    return

class AutoLog():
    
    def __init__( self, logger ):
        
        self.logger = logger
        
        self.assigmentlog = []
        
        self.info = []
        
        self.scene_history = []
        self.scene = []
        
        self.stack = []
        self.path = []
        self.direction = False
        
        return
    
    def __enter__( self ):
        
        self.direction = False
        self.path = []
        sys.settrace( self.trace )
        
        return self
    
    def __exit__( self, exc_type, exc_value, traceback ):
        
        sys.settrace( None )
        
        self.logger( ( tuple( self.path ), tuple( self.scene ) ) )
        
        return
    
    @safe()
    def trace( self, frame, event, args ):
        
        if event in ( 'call', 'c_call' ) :
            
            print '>', frame.f_code.co_name
            
            self.scene = []
            self.direction = True
            
            self.stack.append( frame.f_code.co_name )
            
            print '    @ stack added', self.stack
            
            return self.trace
        
        if event in ( 'return', 'c_return' ) :
            
            print '<', frame.f_code.co_name
            
            exc_type, exc_value, exc_traceback = sys.exc_info()
            
            print '    @ sys.exc_type', sys.exc_type
            
            if len( self.stack ) == 0 :
                print '    @ no stack'
                return self.trace
            
            if self.direction == True :
                self.path.append( ( tuple( self.stack ), exc_value ) )
                self.direction = False
                
                print '    @ stack direction returned', self.path
                
            if exc_value is not self.path[-1][1] :
                self.path.append( ( tuple( self.stack ), exc_value ) )
                self.scene = []
                
            self.stack.pop(-1)
            
            self.scene.append( ( ( frame.f_code.co_name,
                                   frame.f_code.co_filename,
                                   frame.f_lineno,
                                 ),
                                 frame.f_locals.copy(),
                               ) )
            
        return self.trace



@easydecorator.decorator_builder(1)
def autolog( old, logger, *args, **kwargs ):
    
    with AutoLog(logger) :
        return old(*args, **kwargs)




if __name__ == '__main__':
    
    from pprint import pprint
    
    def myraise( e ):
        raise e
        return
    
    @autolog(pprint)
    def foo( erl ):
        
        for e in erl :
            
            try :
                myraise( e('HAHA') )
            except :
                pass
                
        
        return
    
    #foo([Exception,TypeError,ValueError,AttributeError])
    foo([Exception,TypeError])