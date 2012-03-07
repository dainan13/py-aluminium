
#import easyprotocol as ezp
from . import easyprotocol as ezp

import os
import os.path


class FileInfoError( Exception ):
    pass
    
class NotMatch( FileInfoError ):
    pass


class BuildinTypeSegmentMark( ezp.ProtocolType ):
    
    def __init__( self ):
        
        self.name = 'segmark'
        self.cname = 'void *'
        
        self.identifiable = False
        self.stretch = False
        
        self.variables = []
        
    def length( self, lens, array ):
        return array
    
    def read( self, namespace, fp, lens, args ):
        
        h = fp.read(1)
        a = fp.read(1)
        
        if h != '\xff' :
            raise ezp.ConnectionError, ( 'jpeg deconstruct error.', h, fp.io.tell() )
        
        while( a == '\xff' ) :
            a = fp.read(1)
        
        return ord(a), 1


class JPEG( dict ):
    
    ebp = ezp.EasyBinaryProtocol()
    ebp.buildintypes.append(BuildinTypeSegmentMark())
    ebp.rebuild_namespaces()
    ebp.parsefile( ( os.path.dirname(__file__) or '.' )+'/protocols/jpeg.protocol' )
    
    segnames = {
        0xD8 : 'SOI',
        0xE0 : 'APP0', 0xE1 : 'APP1', 0xE2 : 'APP2', 0xE3 : 'APP3',
        0xE4 : 'APP4', 0xE5 : 'APP5', 0xE6 : 'APP6', 0xE7 : 'APP7',
        0xE8 : 'APP8', 0xE9 : 'APP9', 0xEA : 'APP10', 0xEB : 'APP11',
        0xEC : 'APP12', 0xED : 'APP13', 0xEE : 'APP14', 0xEF : 'APP15',
        0xDB : 'DQT',
        0xC4 : 'DHT',
        0xC0 : 'SOF0',
        0xDA : 'SOS',
        0xD9 : 'EOI',
    }
    
    def __init__( self, fname ):
        
        with open(fname) as fp :
            
            while( True ):
                d = self.ebp.read( 'jpeg', fp )
                name = self.segnames.get( d['appmark'], d['appmark'] )
                self[name] = d['content']
                if name == 'EOI' :
                    break
                if name == 'SOS' :
                    fp.seek(-2, os.SEEK_END)
        

class PNG( dict ):
    
    ebp = ezp.EasyBinaryProtocol()
    ebp.parsefile( ( os.path.dirname(__file__) or '.' )+'/protocols/png.protocol' )
    
    def __init__( self, fname ):
        
        with open(fname) as fp :
            
            x = fp.read( 8 )
            if x != '\x89\x50\x4E\x47\x0D\x0A\x1A\x0A' :
                raise ezp.ConnectionError, ('png PREFIX error')
            
            while( True ):
                d = self.ebp.read( 'png', fp )
                name = d['type']
                self[name] = d
                if name == 'IEND' :
                    if d['crc'] != '\xAE\x42\x60\x82' :
                        raise ezp.ConnectionError, ('png IEND chunk error')
                    
                    break
            

class BMP( dict ):
    
    def __init__( self, fname ):
        
        with open(fname) as fp :
            
            x = fp.read(2)
            if x != 'BM' :
                raise ezp.ConnectionError, ('bmp PREFIX error')
        
            length = int( fp.read(4), 16 )
            fp.seek(0, os.SEEK_END)
            if fp.tell() < length :
                raise ezp.ConnectionError, ('bmp error')
        
        
class GIF( dict ):
    
    def __init__( self, fname ):

        with open(fname) as fp :

            x = fp.read(4)
            if x != 'GIF8' :
                raise ezp.ConnectionError, ('bmp PREFIX error')
            
            fp.seek(-2, os.SEEK_END)
            if fp.read(2) != '\x00\x3B' :
                raise ezp.ConnectionError, ('bmp error')
        


def auto_match( f ):
    
    ext = os.path.splitext( f )[-1]
    
    if ext in ('.jpeg','.jpg','.jpe') :
        return JPEG
    elif ext in ('.png',):
        return PNG
    elif ext in ('.bmp',):
        return BMP
    elif ext in ('.gif',):
        return GIF
    
    raise NotMatch, ('not supported format',ext)

if __name__ == '__main__' :
    
    import sys
    
    f = sys.argv[1]
    ext = os.path.splitext( f )[-1]
    if ext in ('.jpeg','.jpg','.jpe') :
        print JPEG(f)
    elif ext in ('.png',):
        print PNG(f)
    elif ext in ('.bmp',):
        print BMP(f)
    elif ext in ('.gif',):
        print GIF(f)
    else :
        print 'unsupported'