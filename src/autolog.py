

import __builtin__

import easydecorator
import traceback


__builtin__.Exception = None


class BaseHookException():
    
    _switch = False
    
    def __init__( self, *args, **kwargs ):
        
        self._callback( )
        
        return
    
    @staticmethod
    def start():
        BaseHookException._switch = True
        
    @staticmethod
    def stop():
        BaseHookException._switch = True
    
    def _callback( self ):
        #if BaseHookException._switch == True :
            print 'ERROR:', self.__class__.__name__


OrignalTypeError

def hook( e ):
    
    print 'Hook>', e.__name__
    
    try :
        
        e.__base__ = BaseHookException
        e.__bases__ = tuple( [BaseHookException,] + list(e.__bases__) )
        return
        
    except TypeError, te :
        
        print 'sub>', e.__subclasses__()
        
        for se in e.__subclasses__():
            hook( se )
        
        class _NEWCLASS( BaseHookException, e ):
            pass
        
        _NEWCLASS.__name__ = e.__name__
        
        setattr( __builtin__, e.__name__, _NEWCLASS )
        
        return
    
    raise BaseException, 'Autolog Error'

hook(BaseException)


@easydecorator.decorator_builder(0)
def autolog( old, *args, **kwargs ):
    
    BaseHookException._switch = True
    
    try :
        return old(*args, **kwargs)
    finally :
        print 'TB>', traceback.print_exc()
        
    BaseHookException._switch = False



if __name__ == '__main__':
    
    @autolog()
    def foo( erl ):
        
        for e in erl :
            
            try :
                raise e('HAHA')
            except :
                pass
        
        return
    
    foo([Exception,TypeError,ValueError,AttributeError])
    