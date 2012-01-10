import os

class PDFError(Exception):
    pass


class PDF( object ):
    
    def __init__ ( self ):
        
        self.data = {}

    def loads( self, fn ):
        
        with open( fn, 'r' ) as fp :
            
            xrefpos = self.read_startxref( fp )
            
            fp.seek(xrefpos)
            
            xrefs = self.read_xref( fp )
            
            objs = []
            for pos in xrefs :
                if pos is None:
                    objs.append( pos )
                    continue
                fp.seek( pos )
                objs.append( self.read_object(fp) )
            
            print objs
            
    def read_startxref( self, fp ):
        
        fp.seek( -500, os.SEEK_END )
        contains = fp.read().splitlines()[-2:]
        if len(contains) != 2 and contains[-1] != '%%EOF' :
            raise PDFError, 'pdf format error, when read startxref.'
            
        return int(contains[0])
        
    def read_xref( self, fp ):
        
        if fp.readline() != 'xref\n':
            raise PDFError, 'pdf format error, when read xref.'
        
        xrefs = []
        ln = fp.readline()
        while( ln != 'trailer\n' ):
            
            st, cnt = ln.strip().split()
            st, cnt = int(st), int(cnt)
            
            if st != len(xrefs) :
                xrefs = [None]*(st-len(xrefs))
            
            for i in range(cnt):
                pos, upd, tag = fp.readline().split()
                pos = int(pos) if tag == 'n' else None
                xrefs.append(pos)
                
            ln = fp.readline()
        
        fp.seek( -len('trailer\n') , os.SEEK_CUR)
        
        return xrefs
    
    def read_trailer( self, fp ):
        
        pass
        
    def read_object( self, fp ):
        
        n, upd, objtag = fp.readline().split()
        
        print n
        
        v = self.read_type(fp)
        
        ln = fp.readline()
        if ln == 'stream\n' :
            v = v
        elif ln != 'endobj\n':
            raise PDFError, 'pdf format error. when read object' + ln

        return v
        
    def read_type( self, fp, ln='' ):
        
        #ln = ln.strip()
        ln = ln or fp.readline().lstrip()
        
        print ln
        
        if ln.startswith('true') or ln.startswith('false'):
            return self.read_type_booleam( fp, ln )
        
        elif ln[0].isdigit() or ln[0] in '+-' :
            return self.read_type_numeric( fp, ln )
        
        elif ln.startswith('['):
            return self.read_type_array( fp, ln )
        
        elif ln.startswith('<<'):
            return self.read_type_dict( fp, ln )
        
        elif ln.startswith('/'):
            return self.read_type_name( fp, ln )
        
        elif ln.startswith('(') :
            return self.read_type_string1( fp, ln )
            
        elif ln.startswith('<') :
            return self.read_type_string2( fp, ln )
            
        elif ln.startswith('null'):
            return None, ln[4:]
        
        raise PDFError, 'unkown type'
        
    def read_type_booleam( self, fp, ln ):
        v, ln = ln.split(None,1)
        return eval(v.capitalize()), ln.lstrip()
    
    def read_type_numeric( self, fp, ln ):
        v, ln = ln.split(None,1)
        return eval(ln), ln.lstrip()
        
    def read_type_string1( self, fp, ln ):
        
        ln = ln[1:]
        
        v = []
        while(True):
            r = ln.split(')',1)
            if len(r) != 2 :
                v.append(ln)
                ln = fp.readline()
                continue
                
            vi, rln = r
            if ( len(v.rstrip('/')) - len(v) ) % 2 != 0 :
                v.append(ln)
                ln = fp.readline()
                continue
            
            return '\n'.join(vi), rln.lstrip()
        
    def read_type_string2( self, fp, ln ):
        
        v, ln = (ln[1:].split('>',1)+[''])[:2]
        
        return v.decode('hex'), ln.strip()
        
    def read_type_name( self, fp, ln ):
        
        v, ln = (ln[1:].split(None,1)+[''])[:2]
        
        return v.replace('#','\\x').decode('string_escape'), ln.lstrip() 
        
    def read_type_array( self, fp, ln ):
        
        ln = ln[1:].lstrip()
        
        ln = ln or fp.readline().lstrip()
        
        v = []
        while( not ln.startwith(']') ):
            vi, ln = self.read_type( fp, ln )
            v.append(vi)
        
        return v, ln
        
    def read_type_dict( self, fp, ln ):
        
        ln = ln[2:].lstrip()
        
        ln = ln or fp.readline().lstrip()
        
        v = {}
        while( not ln.startswith('>>') ):
            ki, ln = self.read_type_name( fp, ln )
            vi = self.read_type( fp, ln )
        
        return v, ln
        
    def read_stream( self, fp ):
        
        return 

if __name__ == '__main__':
    
    import sys

    pdf = PDF()
    pdf.loads( sys.argv[1] )
    