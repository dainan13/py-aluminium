

class AjaxBuilder( type ):
    
    def __new__( cls, name, bases, dct ):
        
        print '__new__', name
        print bases
        print dct
        print
        
        if 'ajax_foo' in dct :
            print dct['ajax_foo'].__doc__
            print dct['ajax_foo'].func_doc
            print dir(dct['ajax_foo'])
        
        return type.__new__( cls, name, bases, dct )
        
    def __init__( cls, name, bases, dct ):
        
        print '__init__', name
        print bases
        print dct
        print
        
        return super( AjaxBuilder, cls ).__init__( name, bases, dct )
        

class EasyAjax( object ):
    
    __metaclass__ = AjaxBuilder
    
    def __init__( self ):
        
        return
        
    def foo( self ):
        
        return

if __name__ == '__main__' :
    
    class TestAjax( EasyAjax ):
        
        def ajax_foo( self, arg ):
            '''
            b = arg[0];
            '''
            
            b = b.split()
            
            '''
            return b;
            '''
            
    t = TestAjax()
    