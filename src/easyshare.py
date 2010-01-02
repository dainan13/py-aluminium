

import multiprocessing
from multiprocessing.sharedctypes import RawValue

import ctypes

import json
import hashlib


class Share( object ):
    
    def __init__( self, maxsize=10240 ):
        
        class ShareStructure ( ctypes.Structure ):
            _fields_ = [("len",  ctypes.c_long  ),
                        ("md5",  ctypes.c_char* 32),
                        ("json", ctypes.c_char* maxsize)]
        
        self.sharestruct = ShareStructure
        
        s = ShareStructure( 0, '', '' )
        
        self.sharespace = RawValue( ShareStructure, 1 )
        
        self.value = None
        
    def __setattr__( self, key, value ):
        
        if key == 'value' :
            
            j = json.dumps( value, encoding='utf-8' )
            self.md5 = hashlib.md5(j).hexdigest()
            l = len(j)
            self.sharespace.len = l
            self.sharespace.md5 = self.md5
            self.sharespace.json = j
            self._value = value
            
            return
        
        return super( Share, self ).__setattr__( key, value )
        
    def __getattr__( self, key ):
        
        if key == 'value' :
            
            if self.md5 != self.sharespace.md5 :
                
                l = self.sharespace.len
                m = self.sharespace.md5
                j = self.sharespace.json
                
                if len(j) == l and hashlib.md5(j).hexdigest() == m :
                    
                    self._value = json.loads( j, encoding='utf-8' )
                    self.md5 = m
                    
            return self._value
        
        return super( Share, self ).__getattr__( key )
        
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