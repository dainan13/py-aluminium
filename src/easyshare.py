

import multiprocessing
from multiprocessing.sharedctypes import RawValue

import ctypes

import json
import hashlib
import threading


class Share( property ):
    
    def __init__( self, _v=None, maxsize=10240 ):
        
        class ShareStructure ( ctypes.Structure ):
            _fields_ = [("len",  ctypes.c_long  ),
                        ("md5",  ctypes.c_char* 32),
                        ("json", ctypes.c_char* maxsize)]
        
        self.sharestruct = ShareStructure
        
        s = ShareStructure( 0, '', '' )
        
        self.sharespace = RawValue( ShareStructure, 1 )
        
        self.lock = threading.Lock()
        
        self.value = _v
        
        property.__init__( self, self.value_getter , self.value_setter )
    
    def on_sharereload( self, newvalue ):
        return newvalue
    
    
    def value_getter( self, host ):
        
        if self.md5 != self.sharespace.md5 :
            
            self.lock.acquire()
            
            try :
            
                l = self.sharespace.len
                m = self.sharespace.md5
                j = self.sharespace.json
                
                if len(j) == l and hashlib.md5(j).hexdigest() == m :
                    
                    self._value = self.on_sharereload(
                                        json.loads( j, encoding='utf-8' ) )
                    self.md5 = m
                    
            finally :
                
                self.lock.release()
                
        return self._value
    
    def value_setter( self, host, value ):
        
        self.lock.acquire()
        
        try :
            
            j = json.dumps( value, encoding='utf-8' )
            m = hashlib.md5(j).hexdigest()
            l = len(j)
            
            self.sharespace.len = l
            self.sharespace.md5 = m
            self.sharespace.json = j
            
            self.md5 = hashlib.md5(j).hexdigest()
            self._value = self.on_sharereload( value )
            
        finally :
            self.lock.release()
            
        #self.md5 = hashlib.md5(j).hexdigest()
        #self._value = self.on_sharereload( value )
        
        return
    
    def _value_getter( self ):
        return self.value_getter( self )
        
    def _value_setter( self, value ):
        return self.value_setter( self, value )
    
    value = property( _value_getter, _value_setter )




if __name__ == '__main__' :
    
    import time
    
    def foo(sharevalue):
        for x in xrange(4):
            time.sleep(0.5)
            sharevalue.value = x
    
    s = Share()
    
    p = multiprocessing.Process( target=foo, args=(s,) )
    p.start()
    
    for x in xrange(5):
        time.sleep(0.4)
        print s.value
    
    p.join()
    
    # as the last of value's time interval same ( 0.4*5 = 0.5*4 )
    # the result maybe : None, 0, 1, 2, 3
    # also maybe : None, 0, 1, 2, 2