import sys
import os
import types

import pprint
import sys
import zlib

import cPickle as pickle

class PDFError(Exception):
    pass
    

class ObjectOnReading(Exception):
    pass

class Name( str ):
    pass

class Stream( str ):
    pass

class ObjRef( object ):
    
    def __init__( self, n, u ):
        self.n = n
        self.u = u
        
    def __str__( self ):
        return 'obj('+str(self.n)+','+str(self.u)+')'
        
    def __repr__( self ):
        return 'obj('+str(self.n)+','+str(self.u)+')'


# fixed pickle load in ipython
if len(sys.argv)==0 and  sys.argv[0].endswith('/ipython'):
    
    m = sys.modules['__main__']
    m.Name = Name
    m.Stream = Stream
    m.ObjRef = ObjRef


class PDF( object ):
    
    def __init__ ( self, fn = None ):
        
        self.pdfver = '%PDF-1.3' # as default
        self.trailer = {}
        self.objects = {}
        
        if fn :
            self.load( fn )
        
    def load( self, fn ):
        
        with open( fn, 'r' ) as fp :
            
            h = fp.readline()
            
        if h.startswith('%PDF-') :
            return self.load_pdf( fn )
        elif h.startswith('%PDFPACK') :
            return self.load_pack( fn )
        
        raise PDFError, 'load error. unsupported format.'
        
    def load_pdf( self, fn ):
        
        with open( fn, 'r' ) as fp :
            
            self.pdfver = fp.readline().rstrip()
            
            xrefpos = self.read_startxref( fp )
            
            fp.seek(xrefpos)
            
            xrefs = self.read_xref( fp )
            self.trailer = self.read_trailer( xrefs, fp )
            
            for nx, pos in xrefs.items() :
                if nx in self.objects :
                    continue
                self.read_object( nx, xrefs, fp )
            
    def read_startxref( self, fp ):
        
        fp.seek( -500, os.SEEK_END )
        contains = fp.read().splitlines()[-2:]
        if len(contains) != 2 and contains[-1] != '%%EOF' :
            raise PDFError, 'pdf format error, when read startxref.'
            
        return int(contains[0])
        
    def read_xref( self, fp ):
        
        h = fp.readline()
        if h.rstrip() != 'xref':
            raise PDFError, 'pdf format error, when read xref.' + h + fp.read()
        
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
        
        ln = fp.readline()
        if not ln.startswith('trailer'):
            raise PDFError, 'pdf format error. wrong trailer : ' + fp.read()
            
        return self.read_type(fp, xrefs=xrefs)[0]
        
    def read_object( self, nx, xrefs, fp ):
        
        fp.seek( xrefs[nx] )
        
        n, upd, objtag = fp.readline().split()
        
        n, upd = int(n),int(upd)
        
        if (n, upd) != nx :
            raise PDFError, 'pdf format error. object address error.'
        
        self.objects[nx] = ObjectOnReading
        
        v, ln = self.read_type(fp, xrefs=xrefs)
        
        if ln.startswith('stream') :
            
            if type(v) != types.DictType :
                raise PDFError, 'pdf format error. wrong stream'
            
            self.objects[(n, upd, None)] = v
            v = self.read_stream( v, fp )
            
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
            
            ln = ln.lstrip()
            while( not ln ):
                ln = fp.readline().lstrip()
               
            if ln.startswith('endobj') or \
               ln.startswith('stream') or \
               ln.startswith('startxref'):
                break
                
            #print >> sys.stderr, ':', ln.strip()
            
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
                r = dict(zip(stack[::2],stack[1::2]))
                ss[-1].append(r)
                stack = ss.pop()
                ln = ln[2:]
                
            # Name
            # eg : /Adobe#20Green
            elif ln.startswith('/'):
                e = 1
                while(ln[e] not in '<>()[]{}/%\0\t\r\n \x0c'): e+=1
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
                
                if v == ObjectOnReading or type(v) in (types.DictType, types.ListType, Stream):
                    stack.append( ObjRef(n, upd) )
                else :
                    stack.append( v )
                
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
        
    def read_stream( self, v, fp ):
        
        le = v['Length']
        s = fp.read(le)
        
        flts = v['Filter'] if type(v['Filter']) == types.ListType else [v['Filter']]
        
        for flt in flts :
            decoder = getattr( self, 'decode_'+flt )
            s = decoder( s, v.get('DecodeParams',{}) )
        
        return Stream(s)
    
    def decode_FlateDecode( self, s, v ):
        #print 'flatedecode'
        if v.get('Predictor',1) != 1 :
            raise PDFError, 'predictor not supported.'
        return zlib.decompress(s)
    
    def dump_pdf( self, fn ):
        
        with open( fn, 'w' ) as fp :
            
            fp.write( self.pdfver )
            fp.write( '\n' )
            
            keys = self.objects.keys()
            keys.sort()
            
            for ki in keys :
                self.write_auto( self.objects[ki], fp )
    
    def write_auto( self, i, fp ):
        w = getattr( self, 'write_'+type(i).__name__ )
        w( i, fp )
    
    def write_int( self, i, fp ):
        fp.write(str(i))
    
    def write_float( self, i, fp ):
        fp.write(str(i))
        
    def write_list( self, i, fp ):
        
        fp.write( '[ ' )
        
        for ii in i :
            self.write_auto( ii, fp )
            fp.write( ' ' )
            
        fp.write( ']' )
    
    def write_dict( self, i, fp ):
        
        fp.write( '<<\n' )
        
        for ki, vi in i.items():
            self.write_auto( ki, fp )
            fp.write( ' ' )
            self.write_auto( vi, fp )
            fp.write( '\n' )
            
        fp.write( '>>\n' )
        
    def write_Stream( self, i, fp ):
        self.write_auto({Name('Length'):len(i)})
        fp.write( 'stream' )
        fp.write( i )
        fp.write( 'endstream' )
        
    def write_Name( self, i, fp ):
        fp.write( '/' )
        fp.write( i )
        
    def write_ObjRef( self, i, fp ):
        self.write_auto(i.n)
        fp.write( ' ' )
        self.write_auto(i.u)
        fp.write( ' R' )
        
    def load_pack( self, fn ):
        
        with open( fn, 'r' ) as fp :
            fp.seek( len('%PDFPACK\n') )
            self.trailer, self.objects = pickle.load( fp )
    
    def dump_pack( self, fn ):
        
        with open( fn, 'w' ) as fp :
            fp.write('%PDFPACK\n')
            pickle.dump( ( self.trailer, self.objects ), fp )
            
    def getref( self, ref ):
        return self.objects[(ref.n, ref.u)]

import difflib
import hashlib

differ = difflib.Differ()

def pdf_item_diff( x, y, a, b, pth, queue ):
    
    xt = type(x)
    yt = type(y)
    
    if xt == ObjRef and yt == ObjRef :
        queue.append( ( x, y, pth ) )
        return None
    
    if xt == ObjRef :
        x = a.getref(x)
        x = type(x)
    
    if yt == ObjRef :
        y = b.getref(y)
        y = type(y)
    
    if xt == types.ListType and yt != types.ListType :
        y = {0:y}
        x = dict(zip(range(len(x)),x))
        xt = yt = types.DictType
    
    elif xt != types.ListType and yt == types.ListType :
        x = {0:x}
        y = dict(zip(range(len(y)),y))
        xt = yt = types.DictType
        
    elif xt == types.ListType and yt == types.ListType :
        x = dict(zip(range(len(x)),x))
        y = dict(zip(range(len(y)),y))
        xt = yt = types.DictType

    if xt == Stream and yt == Stream :
        
        if x == y :
            return None
        
        if pth.endswith('/Contents') :
            return list(differ.compare(x,y))
        else :
            return [ 'L) '+hashlib.md5(x).hexdigest() +' Length:'+str(len(x)),
                     'R) '+hashlib.md5(y).hexdigest() +' Length:'+str(len(y)),
                   ]
        
    elif xt == types.DictType and yt == types.DictType :
        
        keys = list(set( x.keys() + y.keys() ))
        keys.sort()
        
        dr = []
        
        for k in keys :
            
            xv = x.get(k, None)
            yv = y.get(k, None)
            
            vr = pdf_item_diff( xv, yv, a, b, pth+'/'+str(k), queue )
            
            if vr != None :
                dr.append( ': ' + k )
                dr.extend( vr )
                
        return None if dr == [] else dr
    
    if x == y :
        return None
        
    return [ 'L) ' + repr(x),
             'R) ' + repr(y),
           ]
    

def pdf_diff( a, b ):
    
    r = {}
    queue = []
    
    queue.append( ( a.trailer['Root'], b.trailer['Root'], 'Root' ) )
    
    while( queue != [] ):
    
        xr, yr, pth = queue.pop(0)
        
        x = a.getref(xr)
        y = b.getref(yr)
        
        rk = ((xr.n,xr.u),(yr.n,yr.u))
        if rk not in r :
            r[rk] = ( pdf_item_diff(x,y,a,b,pth,queue), [pth] ) 
        else :
            r[rk][1].append(pth)
        
    str2 = lambda i : str(i[0])+'.'+str(i[1])
    pr = [ [ '>'*30+' '+str2(ia)+' '+str2(ib)]+pths+v+['',''] 
           for (ia,ib), (v,pths) in r.items() if v != None
         ]
    for ipr in pr :
        for lr in ipr :
            print lr

    
if __name__ == '__main__':
    
    import sys

    helpinfo = """\
pdf.py usage :

    pdf.py dump xxx.pdf xxx.dump
    pdf.py make xxx.dump xxx.pdf
    pdf.py diff xxx yyy

"""
    
    if len(sys.argv) != 4 or sys.argv[1].strip('-') in ('help', 'h') :
        print helpinfo
    
    if sys.argv[1] == 'dump' :
        pdf = PDF( sys.argv[2] )
        pdf.dump_pack( sys.argv[3] )
    elif sys.argv[1] == 'make' :
        pdf = PDF( sys.argv[2] )
        pdf.dump_pdf( sys.argv[3] )
    elif sys.argv[1] == 'diff' :
        pdf1 = PDF( sys.argv[2] )
        pdf2 = PDF( sys.argv[3] )
        pdf_diff( pdf1, pdf2 )
    else :
        print helpinfo
        
        
        
        