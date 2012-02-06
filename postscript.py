
from simpleparse.parser import Parser

declaration = r'''
EXPRESSION := (TYPE, SAFESPACES?)*, DELIMITER
DELIMITER  := [\r\n]+
SAFESPACES := [ \t]+
COMMENT    := '%', [a-zA-Z0-9 \t]*, ('\r\n' / '\n')
TYPE       := STRING / NUMBERIC / BOOLEAN / NAME / NULL / OPERATOR / ARRAY / DICTIONARY
BOOLEAN    := 'true' / 'false'
OPERATOR   := ([a-zA-Z]+, '*'?) / '"' / '\''
SPACES     := [ \t\r\n]+ / COMMENT+
NUMBERIC   := FLOAT / INTEGER 
INTEGER    := [+-]?, [0-9]+
FLOAT      := [+-]?, ([0-9]+, '.', [0-9]*) / ('.', [0-9]+) 
STRING     := LITERAL_STRING / HEXADECIMAL_STRING
LITERAL_STRING     := '(', ( '\\\\' / '\\)' / -[)] )* ,')'
HEXADECIMAL_STRING := '<', [0-9A-Fa-f]* ,'>'
NAME       := '/', -[\x5B\x5D()<>{}\/\%\0\t\r\n \x0C]+
NULL       := 'null'
ARRAY      := '[' , SPACES?, (TYPE, SPACES?)*, ']'
DICTIONARY := '<<' , SPACES?, (TYPE, SPACES?)*, '>>'
'''

#operators  argc info
type4 = r'''
add         2   %(1)s + %(2)s
sub         2   %(1)s - %(2)s
mul         2   %(1)s * %(2)s
div         2   float(%(1)s) / %(2)s
ldiv        2   %(1)s / %(2)s
mod         2   %(1)s %% %(2)s
neg         1   -%(1)s
abs         1   abs(%(1)s)
ceiling     1   math.ceil(%(1)s)
floor       1   math.floor(%(1)s)
round       1   int(round(%(1))s)
truncate    1   math.trunc(%(1)s)
sqrt        1   math.sqrt(%(1)s)
sin         1   math.sin(%(1)s)
cos         1   math.cos(%(1)s)
atan        1   math.atan(%(1)s)
exp         1   math.atan(%(1)s)
ln          1   math.log(%(1)s)
log         1   math.log10(%(1)s)
cvl         1   int(%(1)s)
cvr         1   float(%(1)s)
eq          2   %(1)s == %(2)s
ne          2   %(1)s != %(2)s
gt          2   %(1)s > %(2)s
ge          2   %(1)s >= %(2)s
lt          2   %(1)s < %(2)s
le          2   %(1)s <= %(2)s
and         2   %(1)s and %(2)s
or          2   %(1)s or %(2)s
xor         2   %(1)s xor %(2)s
not         1   not %(1)s
bitshift    2   %(1)s << %(s)s
'''

#operators  argc 
type4ext = r'''
if          2      if %(1)s : %(2)s
ifelse      3      if %(1)s : %(2)s else : %(3)s
pop         1      %(1)
exch        2      a, b = %(1)s, %(2)s 
dup         2      a = %(1)s
copy        -
index       -
roll        -
'''

#operators      argc
psoperators = r'''
clip            0    
closepath       0    
concat          1    
curveto         6    
eoclip          0    
eofill          0    
fill            0    
grestore        0        
gsave           0    
lineto          2    
moveto          2    
selectfont      2    
setcachedevice  6    
setcharwidth    2    
setcmykcolor    4     
setcolor        (n)
setcolorspace   1    
setdash         2    
setflat         1    
setgray         1     
setlinecap      1    
setlinejoin     1    
setlinewidth    1    
setmiterlimit   1    
setrgbcolor     3    
shfill          1    
show            1    
stroke          0    
'''

#         11    1   2         3        4      4   5
#123456789012345678901234567890123456789012345678901234567890123456789012345678
#operators argc ps                            description
pdfop329 = r'''
BX         +0   (ComSection)                  (PDF 1.1) Begin compatibility section
EX         -0                                 (PDF 1.1) End compatibility section
'''
pdfop407 = r'''
q          0    gsave                         Save graphics state
Q          0    grestore                      Restore graphics state
cm         6    concat                        Concatenate matrix to current transformation matrix
w          1    setlinewidth                  Set line width
J          1    setlinecap                    Set line cap style
j          1    setlinejoin                   Set line join style
M          1    setmiterlimit                 Set miter limit
d          2    setdash                       Set line dash pattern
ri         1    (set_color_rendering)         Set color rendering intent
i          1    setflat                       Set flatness tolerance
gs         1    (usegraphic)                  (PDF 1.2) Set parameters from graphics state parameter dictionary
'''
pdfop409 = r'''
m          2    moveto                        Begin new subpath
l          2    lineto                        Append straight line segment to path
c          6    curveto                       Append curved segment to path (three control points)
v          4    (curveto_fromcur)             Append curved segment to path (initial point replicated)
y          4    (curveto_tocur)               Append curved segment to path (final point replicated)
h          0    closepath                     Close subpath
re         4    (append_rectangle)            Append rectangle to path
'''
pdfop410 = r'''
S          0    stroke                        Stroke path
s          0    closepath, stroke             Close and stroke path
f          0    fill                          Fill path using nonzero winding number rule
F          0    fill                          Fill path using nonzero winding number rule (obsolete)
f*         0    eofill                        Fill path using even-odd rule
B          0    fill, stroke                  Fill and stroke path using nonzero winding number rule
B*         0    eofill, stroke                Fill and stroke path using even-odd rule
b          0    closepath, fill, stroke       Close, fill, and stroke path using nonzero winding number rule
b*         0    closepath, eofill, stroke     Close, fill, and stroke path using even-odd rule
n          0    (endpath)                     End path without filling or stroking
'''
pdfop411 = r'''
W          0    clip                          Set clipping path using nonzero winding number rule
W*         0    eoclip                        Set clipping path using even-odd rule
'''
pdfop424 = r'''
CS         1    setcolorspace                 (PDF 1.1) Set color space for stroking operations
cs         1    setcolorspace                 (PDF 1.1) Set color space for nonstroking operations
SC         n    setcolor                      (PDF 1.1) Set color for stroking operations
SCN        n    setcolor                      (PDF 1.2) Set color for stroking operations (ICCBased and special color spaces)
sc         n    setcolor                      (PDF 1.1) Set color for nonstroking operations
scn        n    setcolor                      (PDF 1.2) Set color for nonstroking operations (ICCBased and special color spaces)
G          1    setgray                       Set gray level for stroking operations
g          1    setgray                       Set gray level for nonstroking operations
RG         3    setrgbcolor                   Set RGB color for stroking operations
rg         3    setrgbcolor                   Set RGB color for nonstroking operations
K          4    setcmykcolor                  Set CMYK color for stroking operations
k          4    setcmykcolor                  Set CMYK color for nonstroking operations
'''
pdfop437 = r'''
Do         1    (call)                        Invoke named XObject
'''
pdfop442 = r'''
BI         +0   (Image)                       Begin an inline image object
ID         +0   (Image)                       Begin the image data for an inline image object
EI         -0                                 End an inline image object
'''
pdfop502 = r'''
Tc         1    (settextspacing)              Set character spacing
Tw         1    (setwordspacing)              Set word spacing
Tz         1    (settext_h)                   Set horizontal text scaling
TL         1    (settext_leading)             Set text leading
Tf         2    selectfont                    Set text font and size
Tr         1    (settext_rendering)           Set text rendering mode
Ts         1    (settext_rise)                Set text rise
'''
pdfop504 = r'''
BT         +0   (Text)                        Begin text object
ET         -0                                 End text object
'''
pdfop505 = r'''
Td         2    (textposition)                Move text position
TD         2    (textposition_d)              Move text position and set leading
Tm         6    (textmatrix)                  Set text matrix and text line matrix
T*         0    (textpos_nextline)            Move to start of next text line
'''
pdfop506 = r'''
Tj         1    show                          Begin text object
TJ         1    (show)                        End text object
'          1    (show_nextline)
"          3    (show_ex)
'''
pdfop510 = r'''
d0         2    setcharwidth                  Set glyph width in Type 3 font
d1         6    setcachedevice                Set glyph width and bounding box in Type 3 font
'''
pdfop1007 = r'''
MP         1    (Marked_Content)              (PDF 1.2) Define marked-content point
DP         2    (Marked_Content)              (PDF 1.2) Define marked-content point with property list
BMC        +1   (Marked_Content)              (PDF 1.2) Begin marked-content sequence
BDC        +2   (Marked_Content)              (PDF 1.2) Begin marked-content sequence with property list
EMC        -0                                 (PDF 1.2) End marked-content sequence
'''
#         1.    .   2         3        4      .   5
#123456789012345678901234567890123456789012345678901234567890123456789012345678
#operators argc ps                            description

pdfopers = [ pdfop329, pdfop407, pdfop409, pdfop410, pdfop411, pdfop424,
             pdfop437, pdfop442,
             pdfop502, pdfop504, pdfop505, pdfop506, pdfop510,
             pdfop1007,
           ]

data = 'q\nBT\n/F1 24 Tf\n24 TL\n1 0 0.2126 1 50 700 Tm\n(\x00+\x00H\x00O\x00O\x00R\x00\x03\x00Z\x00R\x00U\x00O\x00G\x00\x04\x00\x03\x04L+\x82\x05\x96\x0f\xb3\x00\x03\x00\x04)Tj\n1 0 0.2126 1 50 676 Tm\n(\x00\x0b\x00V\x00D\x00\\\\\x00V\x00\x03\x003\x00\\\\\x00W\x00K\x00R\x00Q\x00\x0c)Tj\nET\nQ\n0.5335 0.8458 -0.8458 0.5335 88.5386 11.0368 cm\n3.7611 w\nBT\n/F2 125.3695 Tf\n1 Tr\n0 TL\n0 0 Td\n(zzzPsgiolePfrp)Tj\n1 w\nET\n'

def initialpostscript( cls ):
    
    parser = Parser( declaration, 'EXPRESSION' )
    
    cls.parser = parser
    
    opers = [ l.strip() for ops in pdfopers for l in ops.splitlines() ]
    opers = [ (l[:11].strip(), l[11:16].strip(), l[16:46].strip(), l[46:].strip()) for l in opers if l ]

    op_pdf2ps = [ (n,f.strip('()').split(',') ) for n, arg, f, d in opers ]
    op_pdf2ps = [ (n, [ fi.strip() for fi in f] ) for n, f in op_pdf2ps ]
    
    op_cnt = [ (n, int(arg) if arg!='n' else None) for n, arg, f, d in opers ]
    op_sec = [ (n, True if arg.startswith('+') else False if arg.startswith('-') else None ) 
               for n, arg, f, d in opers ]    
    
    cls.pdfopers = dict(op_pdf2ps)
    cls.pdfopers_argc = dict(op_cnt)
    cls.pdfopers_sec = dict(op_sec)
    
    return cls

@initialpostscript
class PostScript(object):
    
    def __init__( self ):
        self.section = []
        
    def decompile( self, inp ):
        
        pos = 0
        success = 1
        
        while( success ):
            success, tree, nchar = self.parser.parse( inp[pos:] )
            #print '----'
            raw = data[pos:pos+nchar]
            pos += nchar
            #print raw
            #print tree
            prefix = ' '*(4*len(self.section))
            print prefix + (prefix+'\n').join( self._d(tree, raw, []) )
            #print
        
        return
        
    def _d( self, inps, raw, stacks ):
        
        for t, s, e, subs in inps :
            if t == 'TYPE' :
                self._d_TYPE((t,s,e,subs), raw, stacks)
                
        return stacks
        
    def _xd_one( self, inps, raw, stacks ):
        t, s, e, subs = inps
        return getattr( self, '_d_'+subs[0][0] )( subs[0], raw, stacks )
        
    _d_TYPE = _xd_one
    _d_NUMBERIC = _xd_one
    _d_STRING = _xd_one
        
    def _d_INTEGER( self, inps, raw, stacks ):
        t, s, e, subs = inps
        v = int(raw[s:e])
        stacks.append(v)
        return v
        
    def _d_FLOAT( self, inps, raw, stacks ):
        t, s, e, subs = inps
        v = float(raw[s:e])
        stacks.append(v)
        return v
        
    def _d_OPERATOR( self, inps, raw, stacks ):
        
        t, s, e, subs = inps
        f = raw[s:e]
        
        if self.pdfopers_sec[f] == False :
            self.section.pop(-1)
            return
        
        ps_opers = self.pdfopers[f]
        argc = self.pdfopers_argc[f]
        argclist = [0]*(len(ps_opers)-1) + [argc]
        
        for oper, argc in zip(ps_opers, argclist):
            if argc == 'n' :
                raise Exception, 'n not supported yet'
            args = [ str(stacks.pop(-1)) for i in range(argc) ]
            args.reverse()
            v = oper + '(' + ', '.join(args) + ')'
            stacks.append(v)
            
        if self.pdfopers_sec[f] == True :
            self.section.append(v)
            stacks.append( 'with '+stacks.pop(-1)+' :' )
            
        return v
        
    def _d_LITERAL_STRING( self, inps, raw, stacks ):
        t, s, e, subs = inps
        v = raw[s+1:e-1]
        v = repr(v)
        stacks.append(v)
        return v
        
    def _d_HEXADECIMAL_STRING( self, inps, raw, stacks ):
        t, s, e, subs = inps
        v = raw[s+1:e-1]
        v = repr(v)
        stacks.append(v)
        return v
        
    def _d_NAME( self, inps, raw, stacks ):
        t, s, e, subs = inps
        v = raw[s+1:e]
        stacks.append(v)
        return v
        
    def compile( self ):
        pass

ps = PostScript()

if __name__ == '__main__' :
    
    ps.decompile(data)
    