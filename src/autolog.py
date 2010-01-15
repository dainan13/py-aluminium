

import easydecorator
import traceback
import sys


class AutoLog():
    
    def __init__( self, logger ):
        
        self.logger = logger
        
        self.laste = None
        self.S = []
        
        self.info = []
        
        return
    
    def __enter__( self ):
        
        sys.settrace( self )
        
        return self
    
    def __exit__( self, exc_type, exc_value, traceback ):
        
        self.info.append( (self.laste,self.S) )
        
        self.info = self.info[1:]
        
        
        self.logger( self.info )
        
        sys.settrace( None )
        
        return
    
    def __call__( self, frame, event, args ):
            
        if event == 'exception':
            
            if args[1] is self.laste :
                self.S.append( ( frame.f_code.co_name,
                                 frame.f_code.co_filename,
                                 frame.f_lineno,
                                 frame.f_locals.copy(),
                             ) )
            
            else :
                self.info.append( (self.laste,self.S) )
                self.laste = args[1]
                self.S = [( frame.f_code.co_name,
                            frame.f_code.co_filename,
                            frame.f_lineno,
                            frame.f_locals.copy(),
                         ),]
                
        return self





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
    
    foo([Exception,TypeError,ValueError,AttributeError])
    foo([Exception,TypeError])