

import multiprocessing
from multiprocessing.sharedctypes import RawArray

import ctypes

import json
import hashlib

class Namespace():
    
    def __init__( self, maxsize=10240 ):
        
        self.vals = {}
        
        self.sharespace = RawArray( 'c', size )
        
    def _write( self ):
        
        j = json.dumps( self.vals, encoding='utf-8' )
        md5 = hashlib.md5(j).digest()
        l = chr(len(j))
        
        self.sharespace = l+j+md5
        