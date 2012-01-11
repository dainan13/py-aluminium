import os
import types

import pprint
import sys

class PDFError(Exception):
    pass
    

class ObjectOnReading(Exception):
    pass

class Name( str ):
    pass
    
class ObjRef( object ):
    def __init__( self, n ):
        self.n = n
        
    def __str__( self ):
        return 'obj('+str(self.n)+')'
        
    def __repr__( self ):
        return 'obj('+str(self.n)+')'

class SuperLongString( str ):
    
    def __str__( self ):
        return 'SuperLongString[['+str(len(self))+']]'
        
    def __repr__( self ):
        return 'SuperLongString[['+str(len(self))+']]'

class PDF( object ):
    
    def __init__ ( self ):
        
        self.objects = {}

    def loads( self, fn ):
        
        with open( fn, 'r' ) as fp :
            
            xrefpos = self.read_startxref( fp )
            
            fp.seek(xrefpos)
            
            xrefs = self.read_xref( fp )
            trailer = self.read_trailer( xrefs, fp )
            
            for nx, pos in xrefs.items() :
                if nx in self.objects :
                    continue
                self.read_object( nx, xrefs, fp )
            
            pprint.pprint( trailer )
            pprint.pprint( self.objects )
            #print self.objects
            
    def read_startxref( self, fp ):
        
        fp.seek( -500, os.SEEK_END )
        contains = fp.read().splitlines()[-2:]
        if len(contains) != 2 and contains[-1] != '%%EOF' :
            raise PDFError, 'pdf format error, when read startxref.'
            
        return int(contains[0])
        
    def read_xref( self, fp ):
        
        if fp.readline() != 'xref\n':
            raise PDFError, 'pdf format error, when read xref.'
        
        xrefs = {}
        ln = fp.readline()
        while( not ln.startswith( 'trailer' ) ):
            
            st, cnt = ln.strip().split()
            st, cnt = int(st), int(cnt)
            
            for i in range(cnt):
                pos, upd, tag = fp.readline().split()
                if tag == 'f' :
                    continue
                xrefs[(st+i, int(upd))] = int(pos)
                
            ln = fp.readline()
        
        fp.seek( -len(ln) , os.SEEK_CUR)
        
        return xrefs
    
    def read_trailer( self, xrefs, fp ):
        
        print >> sys.stderr, 't'
        
        ln = fp.readline()
        if not ln.startswith('trailer'):
            raise PDFError, 'pdf format error. wrong trailer : ' + fp.read()
            
        return self.read_type(fp, xrefs=xrefs)[0]
        
    def read_object( self, nx, xrefs, fp ):
        
        print >> sys.stderr, nx
        
        fp.seek( xrefs[nx] )
        
        n, upd, objtag = fp.readline().split()
        
        self.objects[nx] = ObjectOnReading
        
        if (int(n),int(upd)) != nx :
            raise PDFError, 'pdf format error. object address error.'
        
        v, ln = self.read_type(fp, xrefs=xrefs)
        
        #ln = fp.readline()
        if ln.startswith('stream') :
            
            if type(v) != types.DictType :
                raise PDFError, 'pdf format error. wrong stream'
            le = v['Length']
            v = fp.read(le)
            
            if len(v) > 1024*5 :
                v = SuperLongString(v)
            
        elif ln.startswith('endobj') :
            pass
            
        else :
            raise PDFError, 'pdf format error. when read object : ' + ln
            
        self.objects[nx] = v
        
        return v
        
    def read_type( self, fp, ln='', xrefs={} ):
        
        ss = []
        stack = []
        
        while( True ):
            
            ln = ln.lstrip() or fp.readline().lstrip()
            if ln.startswith('endobj') or \
               ln.startswith('stream') or \
               ln.startswith('startxref'):
                break
                
            print >> sys.stderr, ':', ln.strip()
            
            # boolean
            # eg : true false
            if ln.startswith('true') :
                stack.append(True)
                ln = ln[4:]
                
            elif ln.startswith('false'):
                stack.append(False)
                ln = ln[4:]
                
            # Numeric
            # eg : 123 43445 +17 -98 0
            #      34.5 -3.62 +123.6 4. -.002 0.0
            elif ln[0].isdigit() or ln[0] in '+-':
                e = 0
                while(ln[e] in '+-.0123456789'): e+=1
                stack.append(eval(ln[:e]))
                ln = ln[e:]
                
            # Array
            # eg : [549 3.14 false (Ralph) /SomeName]
            elif ln.startswith('['):
                ss.append(stack)
                stack = []
                ln = ln[1:]
                
            elif ln.startswith(']'):
                ss[-1].append(stack)
                stack = ss.pop()
                ln = ln[1:]
                
            # Dictionaries
            # eg : << /Type /Example
            #      >>
            elif ln.startswith('<<'):
                ss.append(stack)
                stack = []
                ln = ln[2:]
                
            elif ln.startswith('>>'):
                try :
                    r = dict(zip(stack[::2],stack[1::2]))
                except :
                    print >> sys.stderr, stack
                    raise
                ss[-1].append(r)
                stack = ss.pop()
                ln = ln[2:]
                
            # Name
            # eg : /Adobe#20Green
            elif ln.startswith('/'):
                e = 1
                while(ln[e] not in '()[]{}/%\0\t\r\n \x0c'): e+=1
                v = ln[1:e].replace('#','\\x').decode('string_escape')
                v = Name(v)
                stack.append(v)
                ln = ln[e:]
                
            # String Type 1
            elif ln.startswith('('):
                e = 0
                t = False
                while( t or ln[e] != ')' ):
                    t = ( t == False and ln[e] == '\\' )
                    e += 1
                    if e == len(ln) :
                        ln += fp.readline()
                stack.append(ln[1:e].replace('\(','(').replace('\)',')').decode('string_escape'))
                ln = ln[e+1:]
                
            # String Type 2
            elif ln.startswith('<'):
                v, ln = (ln[1:].split('>',1)+[''])[:2]
                if len(v) % 2 == 1 :
                    v = v+'0'
                stack.append(v.decode('hex'))
                # ln = ln
                
            # null
            elif ln.startswith('null'):
                stack.append(None)
                ln = ln[4:]
            
            #
            # # Operator :            
            #
            
            # R
            elif ln.startswith('R'):
                upd, n = stack.pop(), stack.pop()
                v = self.objects.get( (n, upd), KeyError )
                
                if v == KeyError :
                    curpos = fp.tell()
                    v = self.read_object( (n, upd), xrefs, fp )
                    fp.seek( curpos )
                
                if v == ObjectOnReading or type(v) in (types.DictType, types.ListType, SuperLongString):
                    stack.append(ObjRef(n))
                else :
                    stack.append(v)
                
                ln = ln[1:]
                
            
            # Tf selectfont
            #elif ln.startswith('Tf'):
            #    pass
            
            # Tj showtext
            #elif ln.startswith('Tj'):
            #    pass
                
            #elif ln.startswith('TJ'):
            #    pass
        
        if len(stack) != 1 :
            print stack, ss
            raise PDFError, 'pdf format error. when read object '
        
        return stack[0], ln.lstrip()
        
    def read_stream( self, fp ):
        
        return 

if __name__ == '__main__':
    
    import sys

    pdf = PDF()
    pdf.loads( sys.argv[1] )
    