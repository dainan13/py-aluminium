
if __name__ == '__main__' :
    try :
        import easyprotocol as ezp
    except :
        from Al import easyprotocol as ezp
else :
    from . import easyprotocol as ezp
    
    
import os
import os.path
import pprint
import cStringIO

__filepath__ = str(os.path.realpath(__file__).rsplit('/',1)[0])


def int8( ch ):
    return chr(ch)
    
def int16( ch ):
    return chr(ch%256) + chr(ch/256)

def int32( ch ):
    return chr(ch%256) + chr((ch/256)%256) + chr((ch/(256**2))%256) + chr(ch/(256**3)%256)


class TagCodeAndLenght( ezp.ProtocolType ):
    
    def __init__( self ):
        
        self.name = 'TagCodeAndLenght'
        self.cname = 'TagCodeAndLenght'
        
        self.identifiable = True
        self.stretch = True
        
        self.variables = []
        
    def length( self, lens, array ):
        return None
    
    def read( self, namespace, fp, lens, args ):
        
        c = ord(fp.read(1)) + ord(fp.read(1))*256
        le = 2
        
        code = c >> 6
        maxlen = ( 1 << 6 ) - 1
        length = c & maxlen
        
        if length == maxlen :
            length = ord(fp.read(1)) + ord(fp.read(1))*256 + ord(fp.read(1))*256*256 + ord(fp.read(1))*256*256*256
            le += 4
        
        return {'code':code, 'length':length}, le
        
    def read_multi( self, namespace, fp, lens, mlens, args ):
        
        raise TTFError, 'flags can\'t read 1+.'


class String( ezp.ProtocolType ):
    
    def __init__( self ):
        
        self.name = 'string'
        self.cname = 'string'
        
        self.identifiable = True
        self.stretch = True
        
        self.variables = []
        
    def length( self, lens, array ):
        return None
    
    def read( self, namespace, fp, lens, args ):
        
        c = fp.read(1)
        r = [c,]
        
        while( c != '\0' ):
            c = fp.read(1)
            r.append(c)
        
        le = len(r)
        
        return ''.join(r), le
        
    def read_multi( self, namespace, fp, lens, mlens, args ):
        
        raise TTFError, 'flags can\'t read 1+.'
        

class Rect( ezp.ProtocolType ):
    
    def __init__( self ):
        
        self.name = 'rect'
        self.cname = 'rect'
        
        self.identifiable = True
        self.stretch = True
        
        self.variables = []
        
    def length( self, lens, array ):
        return None
    
    def read( self, namespace, fp, lens, args ):
        
        c = fp.read(1)
        ci = ord(c)
        nbits = ci >> 3
        
        nexttoread = ( nbits*4 + 5 + 7 ) / 8 - 1 
        
        c = c + fp.read(nexttoread)
        
        return c, nexttoread+1
        
    def read_multi( self, namespace, fp, lens, mlens, args ):
        
        raise TTFError, 'flags can\'t read 1+.'
        

class ShockwaveFile(object):
    
    ebp = ezp.EasyBinaryProtocol()
    ebp.buildintypes.append(TagCodeAndLenght())
    ebp.buildintypes.append(Rect())
    ebp.buildintypes.append(String())
    ebp.rebuild_namespaces()
    ebp.parsefile( __filepath__+'/protocols/swf.protocol' )
    
    def __init__( self, fname ):
        
        with open(fname) as fp :
            
            self.header = self.ebp.read( 'swf', fp )
            self.tags = []
            
            le = -1
            
            while( le !=0 ):
                
                tag = self.ebp.read( 'tag', fp )
                le = tag['code_and_length']['length']
                self.tags.append(tag)
                
        self.fonts = {}
        
        for tag in self.tags :
            
            if tag['code_and_length']['code'] == 91 :
                
                font = self.ebp.read( 'tag91', cStringIO.StringIO(tag['content']), length=tag['code_and_length']['length'] )
                font['fontname'] = font['fontname'].strip('\0') 
                
                tag['content'] = font
                self.fonts[font['fontname']] = font
                
                
        #pprint.pprint( self.fonts )
    
    def dump_swf( self, fname ):
        
        self.header['filesize'] = \
            3 + 1 + 4 + len(self.header['framesize']) + \
            1 + 1 + 2 + \
            sum( self._len_tag(t) for t in self.tags )
        
        with open( fname, 'wb' ) as fp :
            
            self._dump_header( fp )
            
            for tag in self.tags :
                self._dump_tag( fp, tag )
        
        return
        
    def _dump_header( self, fp ):
        
        fp.write( self.header['signature'] )
        fp.write( int8(self.header['version']) )
        fp.write( int32(self.header['filesize']) )
        fp.write( self.header['framesize'] )
        fp.write( int8(self.header['framerate']['sub']) )
        fp.write( int8(self.header['framerate']['major']) )
        fp.write( int16(self.header['framecount']) )
        
        return
        
    def _len_tag( self, tag ):
        
        if tag['code_and_length']['code'] == 91 :
            return 3 + len(tag['content']['fontname']) + 1 + len(tag['content']['fontdata']) + 6
        
        return len(tag['content']) + 6
        
    def _dump_tag( self, fp, tag ):
        
        fp.write( int16( (tag['code_and_length']['code'] << 6) + 63 ) )
        
        if tag['code_and_length']['code'] == 91 :
            return self._dump_tag_91( fp, tag )
            
        tag['code_and_length']['length'] = len(tag['content'])
        fp.write( int32( tag['code_and_length']['length'] ) )
        fp.write( tag['content'] )
        
        return
        
    def _dump_tag_91( self, fp, tag ):
        
        le = 2 + 1 + len(tag['content']['fontname']) + 1 + len(tag['content']['fontdata'])
        tag['code_and_length']['length'] = le
        fp.write( int32( tag['code_and_length']['length'] ) )
        
        fp.write( int16(tag['content']['fontID']) )
        fp.write( int8(tag['content']['fontflag']) )
        fp.write( tag['content']['fontname'] )
        fp.write( '\0' )
        fp.write( tag['content']['fontdata'] )
        
        return
    
    def print_tag( self, tag ):
        
        print '= TAG ='
        print 'CODE', tag['code_and_length']['code']
        print 'LENGTH', tag['code_and_length']['length']
        
        if tag['code_and_length']['code'] == 91 :
            print '  fontID', tag['content']['fontID']
            print '  fontname',tag['content']['fontname']
            return 
        
        print tag['content'].encode('string_escape')
        
        return
    
if __name__ == '__main__' :
    
    import sys
    import getopt
    
    opts, args = getopt.gnu_getopt(
        sys.argv[1:],
        'o:ih',
        ['output=', 'info', 'font=', 'dump-font=', 'help']
    )
    
    helpinfo = '''\
SWF tool. present by py-Al project. it written by python.


examples :

   swf.py [--font xxx:yyy] [-o outputfile] <xxx.swf>
 or 
   swf.py <xxx.swf> --info

command arguments :

 common :
    --output      -o file      : output file
    
 for display info :
    --info        -i           : show file infomations
 
 for font resource :
    --font           name:font : embed font
    --dump-font      name      : dump font
 
 for help :
    --help        -h           : to show this help info.
'''
    
    if len(sys.argv) < 2 :
        print helpinfo
        sys.exit(-1)
        
    
    swf = ShockwaveFile( args[0] )

    output = None
    info = False
    dump_type = None
    dump_res = None
    
    for k, v in opts :
        
        k = k.strip('-')
        
        if k in ('font',) :
            name, fontfile = v.split(':',1)
            with open(fontfile, 'rb') as fp :
                swf.fonts[name]['fontdata'] = fp.read()
                
        elif k in ('dump-font',):
            dump_type = 'font'
            dump_res = v
            
        elif k in ('output','o') :
            output = v
            
        elif k in ('info', 'i'):
            info = True
            
            
    if dump_type != None :
        
        if dump_type == 'font' :
            with open( output, 'wb' ) as fp:
                fp.write( swf.fonts[dump_res]['fontdata'] )
        else :
            raise Exception, 'unkown dump type.'
        
    elif output != None :
        swf.dump_swf( output )
        
    if info :
        
        print 'SWF INFO:'
        print 
        print swf.header
        
        for tag in swf.tags :
            swf.print_tag(tag)
            print
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    