
import easydecorator
import traceback
import sys


class AutoLog():
    
    def __init__( self, logger ):
        
        self.logger = logger
        
        self.assigmentlog = []
        
        self.info = []
        
        self.scene_history = []
        self.scene = []
        
        self.stack = []
        self.path = []
        self.direction = True
        
        return
    
    def __enter__( self ):
        
        sys.setprofile( self.profile )
        
        return self
    
    def __exit__( self, exc_type, exc_value, traceback ):
        
        sys.setprofile( None )
        
        self.logger( ( tuple( self.path ), tuple( self.scene ) ) )
        
        return
    
    def profile( self, frame, event, args ):
        
        if event in ( 'call', 'c_call' ) :
            self.scene = []
            self.direction = True
            
            self.stack.append( frame.f_code.co_name )
            
            return self.profile
        
        if event in ( 'return', 'c_return' ) :
            
            if len( self.stack ) == 0 :
                return self.profile
            
            if self.direction == True :
                self.path.append( ( tuple( self.stack ), sys.exc_value ) )
                self.direction = False
                
            if sys.exc_value is not self.path[-1][1] :
                self.path.append( ( tuple( self.stack ), sys.exc_value ) )
                self.scene = []
                
            self.stack.pop(-1)
            
            self.scene.append( ( ( frame.f_code.co_name,
                                   frame.f_code.co_filename,
                                   frame.f_lineno,
                                 ),
                                 frame.f_locals.copy(),
                               ) )
            
        return self.profile





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